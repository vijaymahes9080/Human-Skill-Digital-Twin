from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.app.engines.core_twin import get_or_create_twin, update_twin_state

# Mapping session types to DNA styles
DNA_MAP = {
    "video": "visual",
    "reading": "reading",
    "audio": "audio",
    "project": "project",
    "coding": "project",
    "experiment": "experiment",
    "discussion": "discussion",
    "teaching": "teaching",
    "simulation": "simulation",
    "exploration": "exploration"
}

def update_learning_dna_from_session(
    db: Session,
    user_id: int,
    session_type: str,
    duration_minutes: float,
    performance_score: float = 0.5  # performance in session helps weight suitability
) -> Dict[str, Any]:
    """Updates learning style preferences and confidence scores based on logged session duration and score.
    
    Larger durations reinforce corresponding styles. High performance scores reinforce confidence in that style.
    """
    twin = get_or_create_twin(db, user_id)
    dna = dict(twin.state.get("learning_dna", {}))
    
    style = DNA_MAP.get(session_type.lower())
    if not style:
        # If unknown, slightly bump the "mixed" style
        style = "mixed"
        
    style_data = dna.get(style, {"score": 0.5, "confidence": 0.5})
    current_score = style_data.get("score", 0.5)
    current_conf = style_data.get("confidence", 0.5)
    
    # Calculate incremental updates based on session attributes
    # More time spent relative to a standard 30 min session increases style score
    duration_weight = min(2.0, duration_minutes / 30.0)
    score_delta = 0.05 * duration_weight
    
    # Update style score (bound between 0.0 and 1.0)
    new_score = current_score + score_delta
    new_score = min(1.0, max(0.1, new_score))
    
    # Update confidence: more reviews lead to higher confidence
    conf_delta = 0.02 * duration_weight * (performance_score / 0.5)
    new_conf = current_conf + conf_delta
    new_conf = min(0.95, max(0.1, new_conf))
    
    dna[style] = {
        "score": round(new_score, 3),
        "confidence": round(new_conf, 3)
    }
    
    # Normalize scores across all styles except 'mixed'
    total_non_mixed = sum(v["score"] for k, v in dna.items() if k != "mixed")
    if total_non_mixed > 0:
        for k in dna.keys():
            if k != "mixed":
                dna[k]["score"] = round(dna[k]["score"] / total_non_mixed, 3)
                
    update_twin_state(db, user_id, "learning_dna", dna)
    return dna
