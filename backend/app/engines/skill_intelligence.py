from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.engines.core_twin import get_or_create_twin, update_twin_state

# Mapping session types and topic tags to impacted skills
SKILL_MAP = {
    "coding": ["programming", "technical", "problem_solving"],
    "writing": ["writing", "research", "communication"],
    "quiz": ["critical_thinking", "problem_solving"],
    "presentation": ["presentation", "communication", "soft"],
    "collaboration": ["collaboration", "negotiation", "leadership", "soft"],
    "planning": ["time_management", "soft"]
}

def update_skills_from_activity(
    db: Session, 
    user_id: int, 
    activity_type: str, 
    tags: List[str], 
    performance: float,  # 0.0 to 1.0 (e.g., test score or completion rating)
    time_spent_ratio: float = 1.0  # ratio of planned vs actual time, default 1.0
) -> Dict[str, Any]:
    """Calculates updated skill scores and confidence based on activity outcomes.
    
    Uses a Bayesian-like exponential smoothing update:
    new_mastery = old_mastery + alpha * (performance - old_mastery)
    Confidence increases slightly with each positive iteration.
    """
    twin = get_or_create_twin(db, user_id)
    skills = dict(twin.state.get("skills", {}))
    
    # Gather all skills that are affected
    affected_skills = set(SKILL_MAP.get(activity_type.lower(), []))
    for tag in tags:
        tag_lower = tag.lower()
        if tag_lower in skills:
            affected_skills.add(tag_lower)
            
    # Default alpha (learning rate)
    alpha = 0.15
    
    updated_fields = {}
    for skill_name in affected_skills:
        skill_data = skills.get(skill_name, {"level": 0.1, "confidence": 0.5})
        old_level = skill_data.get("level", 0.1)
        old_conf = skill_data.get("confidence", 0.5)
        
        # Calculate new level
        diff = performance - old_level
        new_level = old_level + alpha * diff
        new_level = max(0.0, min(1.0, new_level))
        
        # Confidence update: gets closer to 1.0 as iterations accumulate,
        # but drops if there is a mismatch (low performance vs high level)
        perf_mismatch = abs(performance - old_level)
        conf_adjustment = 0.05 * (1.0 - perf_mismatch)
        new_conf = old_conf + conf_adjustment
        new_conf = max(0.1, min(0.95, new_conf))
        
        skills[skill_name] = {
            "level": round(new_level, 3),
            "confidence": round(new_conf, 3)
        }
        updated_fields[skill_name] = skills[skill_name]
        
    update_twin_state(db, user_id, "skills", skills)
    return updated_fields
