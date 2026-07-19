from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models.database_models import LearningSession, ReflectionLog, User
from backend.app.engines.core_twin import get_or_create_twin

def generate_reflection(db: Session, user_id: int, reflection_type: str) -> Dict[str, Any]:
    """Aggregates recent learning logs to construct a cognitive growth reflection summary.
    
    reflection_type: 'daily', 'weekly', 'monthly'
    """
    now = datetime.utcnow()
    
    # Define timeframe
    if reflection_type == "daily":
        start_time = now - timedelta(days=1)
    elif reflection_type == "weekly":
        start_time = now - timedelta(days=7)
    else: # monthly
        start_time = now - timedelta(days=30)
        
    sessions = db.query(LearningSession).filter(
        LearningSession.user_id == user_id,
        LearningSession.start_time >= start_time
    ).all()
    
    # 1. Aggregate indicators
    total_sessions = len(sessions)
    focus_minutes = 0.0
    scores = []
    concepts_touched = set()
    mistakes_count = 0
    
    for s in sessions:
        # Calculate duration
        if s.end_time:
            duration = (s.end_time - s.start_time).total_seconds() / 60.0
            focus_minutes += duration
            
        data = s.data or {}
        score = data.get("score")
        if score is not None:
            scores.append(score)
            
        concept = data.get("concept_id")
        if concept:
            concepts_touched.add(concept)
            
        # Count failures/mistakes
        errors = data.get("incorrect_answers", [])
        mistakes_count += len(errors)
        
    avg_performance = sum(scores) / len(scores) if scores else 0.7
    
    # 2. Get current Twin state snapshot
    twin = get_or_create_twin(db, user_id)
    twin_state_snapshot = dict(twin.state)
    
    # 3. Formulate the reflection narrative
    time_frame_str = "past 24 hours" if reflection_type == "daily" else "past week" if reflection_type == "weekly" else "past month"
    
    growth_point = "stable"
    if avg_performance > 0.8:
        growth_point = "accelerating mastery"
    elif avg_performance < 0.6:
        growth_point = "facing foundation challenges"
        
    narrative = (
        f"During the {time_frame_str}, you completed {total_sessions} sessions "
        f"totaling {int(focus_minutes)} minutes of focused learning, targeting concepts like {', '.join(list(concepts_touched)[:3]) if concepts_touched else 'various topics'}. "
        f"Your performance level averaged {int(avg_performance*100)}%, indicating {growth_point}. "
        f"You logged {mistakes_count} test mistakes, indicating active learning trials. "
    )
    
    if mistakes_count > 5:
        narrative += "Action plan: Leverage the Weakness Diagnostics dashboard. Revisit core prerequisite lessons to resolve repeated patterns."
    else:
        narrative += "Action plan: Excellent consistency. Proceed along your customized career roadmap path."
        
    # Save the log in DB
    reflection = ReflectionLog(
        user_id=user_id,
        reflection_type=reflection_type,
        reflection_date=now,
        content=narrative,
        digital_twin_snapshot=twin_state_snapshot
    )
    db.add(reflection)
    db.commit()
    db.refresh(reflection)
    
    # Adjust focus hours in twin state habits
    habits = dict(twin_state_snapshot.get("habits", {}))
    habits["total_focus_hours"] = habits.get("total_focus_hours", 0.0) + (focus_minutes / 60.0)
    twin.state["habits"] = habits
    db.add(twin)
    db.commit()
    
    return {
        "id": reflection.id,
        "reflection_type": reflection_type,
        "reflection_date": reflection.reflection_date,
        "focus_hours": round(focus_minutes / 60.0, 2),
        "average_performance": round(avg_performance, 2),
        "concepts_explored": list(concepts_touched),
        "mistakes_made": mistakes_count,
        "summary": narrative
    }
