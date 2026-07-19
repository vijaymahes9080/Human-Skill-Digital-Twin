from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.database_models import DigitalTwin

def get_default_twin_state() -> Dict[str, Any]:
    """Generates the initial blueprint for a user's digital twin."""
    return {
        "learning_dna": {
            "visual": {"score": 0.5, "confidence": 0.5},
            "reading": {"score": 0.5, "confidence": 0.5},
            "audio": {"score": 0.5, "confidence": 0.5},
            "project": {"score": 0.5, "confidence": 0.5},
            "experiment": {"score": 0.5, "confidence": 0.5},
            "discussion": {"score": 0.5, "confidence": 0.5},
            "teaching": {"score": 0.5, "confidence": 0.5},
            "simulation": {"score": 0.5, "confidence": 0.5},
            "exploration": {"score": 0.5, "confidence": 0.5},
            "mixed": {"score": 1.0, "confidence": 0.8}
        },
        "skills": {
            "technical": {"level": 0.1, "confidence": 0.5},
            "soft": {"level": 0.1, "confidence": 0.5},
            "communication": {"level": 0.1, "confidence": 0.5},
            "leadership": {"level": 0.1, "confidence": 0.5},
            "research": {"level": 0.1, "confidence": 0.5},
            "writing": {"level": 0.1, "confidence": 0.5},
            "programming": {"level": 0.1, "confidence": 0.5},
            "problem_solving": {"level": 0.1, "confidence": 0.5},
            "critical_thinking": {"level": 0.1, "confidence": 0.5},
            "presentation": {"level": 0.1, "confidence": 0.5},
            "collaboration": {"level": 0.1, "confidence": 0.5},
            "negotiation": {"level": 0.1, "confidence": 0.5},
            "time_management": {"level": 0.1, "confidence": 0.5}
        },
        "memory_profile": {
            "short_term_capacity": 0.6,
            "long_term_capacity": 0.4,
            "overall_retention": 0.8,
            "recall_speed_score": 0.7,
            "average_decay_rate": 0.05,
            "revision_effectiveness": 0.75
        },
        "decision_profile": {
            "risk_tolerance": 0.5,
            "analytical_thinking": 0.5,
            "intuition": 0.5,
            "evidence_collection_speed": 0.5,
            "decision_speed": 0.5,
            "bias_index": 0.1,
            "consistency": 0.8,
            "tradeoff_handling": 0.5,
            "decision_confidence": 0.5
        },
        "habits": {
            "study_streak": 0,
            "active_hours_preference": [9, 10, 11, 14, 15, 16], # hour indices 0-23
            "practice_to_theory_ratio": 1.0,
            "revision_delay_adherence": 0.8,
            "completion_ratio": 0.7,
            "total_focus_hours": 0.0
        },
        "interests": {},
        "career_target": {
            "target_role": "AI Research Engineer",
            "readiness_score": 0.15,
            "target_date": "2027-12-31"
        },
        "goals": []
    }

def get_or_create_twin(db: Session, user_id: int) -> DigitalTwin:
    """Retrieves an existing twin or initializes a default one for the user."""
    twin = db.query(DigitalTwin).filter(DigitalTwin.user_id == user_id).first()
    if not twin:
        twin = DigitalTwin(
            user_id=user_id,
            state=get_default_twin_state()
        )
        db.add(twin)
        db.commit()
        db.refresh(twin)
    return twin

def update_twin_state(db: Session, user_id: int, section: str, updates: Dict[str, Any]) -> DigitalTwin:
    """Updates a sub-key within the JSON state of a user's digital twin."""
    twin = get_or_create_twin(db, user_id)
    state = dict(twin.state)
    
    if section not in state:
        state[section] = {}
        
    # Apply shallow or deep updates depending on configuration
    if isinstance(state[section], dict) and isinstance(updates, dict):
        state[section].update(updates)
    else:
        state[section] = updates
        
    twin.state = state
    db.add(twin)
    db.commit()
    db.refresh(twin)
    return twin
