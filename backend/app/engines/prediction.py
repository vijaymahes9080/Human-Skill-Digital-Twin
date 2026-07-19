from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models.database_models import LearningSession, MemoryItem, KnowledgeNode
from backend.app.engines.core_twin import get_or_create_twin
from backend.app.engines.career_intelligence import analyze_career_readiness
from backend.app.engines.memory_intelligence import calculate_retention

def generate_predictions(db: Session, user_id: int) -> Dict[str, Any]:
    """Forecasts learning progression rates, burnout risks, and upcoming memory decay events."""
    twin = get_or_create_twin(db, user_id)
    
    # 1. Calculate Burnout Risk
    # Fetched from active streaks and intense study focus hours
    habits = twin.state.get("habits", {})
    focus_hours = habits.get("total_focus_hours", 0.0)
    streak = habits.get("study_streak", 0)
    
    # Simple risk model:
    # High focus hours + high streak + low average performance = elevated burnout
    recent_sessions = db.query(LearningSession).filter(
        LearningSession.user_id == user_id,
        LearningSession.start_time >= datetime.utcnow() - timedelta(days=5)
    ).all()
    
    performance_scores = []
    for s in recent_sessions:
        perf = s.data.get("score")
        if perf is not None:
            performance_scores.append(perf)
            
    avg_perf = sum(performance_scores) / len(performance_scores) if performance_scores else 0.7
    
    # Base risk components
    streak_component = min(0.3, streak * 0.02)
    hours_component = min(0.4, (focus_hours / 40.0) * 0.2)  # relative to 40 hours limit
    performance_friction = max(0.0, (0.7 - avg_perf) * 0.5) if avg_perf < 0.7 else 0.0
    
    burnout_risk = streak_component + hours_component + performance_friction
    burnout_risk = round(max(0.05, min(0.95, burnout_risk)), 3)
    
    # 2. Forgetting projections
    memory_items = db.query(MemoryItem).filter(MemoryItem.user_id == user_id).all()
    predicted_forgetting = []
    
    for item in memory_items:
        ret = calculate_retention(item.last_reviewed, item.interval, item.ease_factor, item.repetitions)
        # If current retention is < 0.85 and it's near due date, it's highly likely to be forgotten soon
        if ret < 0.85:
            node = db.query(KnowledgeNode).filter(
                KnowledgeNode.user_id == user_id,
                KnowledgeNode.concept_id == item.concept_id
            ).first()
            if node:
                predicted_forgetting.append(node.title)
                
    # 3. Calculate Learning Velocity
    # Number of concepts mastered (>0.75) per focus hour
    mastered_nodes = db.query(KnowledgeNode).filter(
        KnowledgeNode.user_id == user_id,
        KnowledgeNode.mastery >= 0.75
    ).count()
    
    velocity = mastered_nodes / max(1.0, focus_hours)
    velocity = round(min(5.0, velocity), 3) # scale score
    
    career = analyze_career_readiness(db, user_id)
    
    # 4. Formulate explanation
    explanations = {
        "burnout_risk": (
            f"Burnout risk is {int(burnout_risk*100)}% based on a study streak of {streak} days "
            f"and total focus hours of {round(focus_hours, 1)}h. "
            f"{'We suggest planning a rest day to maintain long-term retention.' if burnout_risk > 0.6 else 'Your learning pacing looks sustainable.'}"
        ),
        "forgetting": f"Predicted {len(predicted_forgetting)} concepts to forget in the upcoming weeks if revisions are skipped.",
        "velocity": f"You are mastering {velocity} concepts per hour of study focus."
    }
    
    return {
        "burnout_risk": burnout_risk,
        "velocity_score": velocity,
        "forgetting_rate_monthly": round(0.1 + (0.2 * (1.0 - habits.get("revision_delay_adherence", 0.8))), 3),
        "predicted_concepts_to_forget": predicted_forgetting[:3],
        "readiness_career": {career["target_role"]: career["readiness_score"]},
        "explanations": explanations
    }
