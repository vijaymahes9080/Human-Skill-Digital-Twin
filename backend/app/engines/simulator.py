import math
import random
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models.database_models import KnowledgeNode, MemoryItem

def simulate_trajectories(
    db: Session, 
    user_id: int, 
    study_minutes_daily: float, 
    practice_frequency: str, 
    skip_revision: bool, 
    strategy: str,
    months: int = 12
) -> Dict[str, Any]:
    """Generates detailed 12-month projections of mastery and retention scores
    under various behavioral constraints.
    """
    # 1. Fetch initial states
    nodes = db.query(KnowledgeNode).filter(KnowledgeNode.user_id == user_id).all()
    memory_items = db.query(MemoryItem).filter(MemoryItem.user_id == user_id).all()
    
    init_mastery = sum(n.mastery for n in nodes) / len(nodes) if nodes else 0.1
    init_retention = 0.8
    if memory_items:
        # Calculate approximate current retention
        now = datetime = datetime_from_timestamp = datetime_now = datetime.utcnow()
        ret_sum = 0.0
        for item in memory_items:
            delta_days = (now - item.last_reviewed).total_seconds() / (24 * 3600.0)
            strength = item.ease_factor * (item.repetitions + 0.5)
            ret_sum += math.exp(-delta_days / max(0.5, strength))
        init_retention = ret_sum / len(memory_items)
        
    time_series = []
    
    # Base coefficients
    # More time = higher velocity, but capping efficiency returns
    time_efficiency = math.log1k = math.log(study_minutes_daily + 1.0) / 4.5
    
    # Practice modifiers
    practice_mods = {"never": -0.05, "weekly": 0.05, "daily": 0.12}
    practice_bonus = practice_mods.get(practice_frequency.lower(), 0.0)
    
    # Current values
    curr_mastery = init_mastery
    curr_retention = init_retention
    
    # We create a deterministic random generator seeded by the user_id to ensure consistency across redraws
    rng = random.Random(user_id + int(study_minutes_daily))
    
    for m in range(months + 1):
        # Apply changes starting month 1
        if m > 0:
            # Mastery update
            m_gain = 0.08 * time_efficiency + 0.03 * practice_bonus
            # If strategy is mixed or project, add positive modifier
            if strategy in ["project", "mixed"]:
                m_gain *= 1.15
            # If skip revision, mastery gains drop after month 3 as memory decays
            if skip_revision and m > 3:
                m_gain *= max(0.2, 1.0 - (m - 3) * 0.15)
                
            curr_mastery += m_gain + rng.uniform(-0.01, 0.02)
            curr_mastery = max(0.01, min(0.98, curr_mastery))
            
            # Retention update
            if skip_revision:
                # Exponential decay of memory
                curr_retention *= math.exp(-0.08)
            else:
                # Retention gains through scheduled review
                r_gain = 0.02 if study_minutes_daily > 20 else -0.01
                r_gain += 0.03 if practice_frequency in ["weekly", "daily"] else -0.02
                curr_retention += r_gain + rng.uniform(-0.015, 0.015)
                
            curr_retention = max(0.1, min(0.96, curr_retention))
            
        time_series.append({
            "month": m,
            "mastery": round(curr_mastery, 3),
            "retention": round(curr_retention, 3),
            "burnout_risk": round(min(0.95, (study_minutes_daily / 180.0) * (1.0 - (practice_bonus if practice_bonus > 0 else 0))), 3)
        })
        
    # Analyze final result to return predicted bottlenecks
    predicted_weaknesses = []
    if curr_retention < 0.6:
        predicted_weaknesses.append("Rapid Knowledge Decay (High probability of forgetting core concepts)")
    if study_minutes_daily > 120 and practice_frequency == "never":
        predicted_weaknesses.append("Cognitive Fatigue / Impaired Practical Mastery (Theory heavy without active application)")
    if skip_revision:
        predicted_weaknesses.append("Severe long-term memory fade across foundational prerequisites")
        
    explanation = {
        "analysis": (
            f"Under this regime ({study_minutes_daily}m/day, "
            f"{'no' if skip_revision else 'active'} revision, {practice_frequency} practice), "
            f"your mastery is projected to reach {int(curr_mastery*100)}% with a memory retention level of {int(curr_retention*100)}%."
        ),
        "advantages": [
            "Good procedural memory" if practice_frequency in ["weekly", "daily"] else "Low cognitive friction",
            "Accelerated path progress" if study_minutes_daily > 60 else "Sustainable workload"
        ],
        "disadvantages": [
            "Prerequisite failure risk due to skipped revisions" if skip_revision else "Requires high calendar commitment",
            "Lack of hands-on verification" if practice_frequency == "never" else "Possibility of temporary fatigue plateaus"
        ]
    }
    
    return {
        "time_series": time_series,
        "final_mastery": round(curr_mastery, 3),
        "final_retention": round(curr_retention, 3),
        "predicted_weaknesses": predicted_weaknesses,
        "explaination": explanation
    }
