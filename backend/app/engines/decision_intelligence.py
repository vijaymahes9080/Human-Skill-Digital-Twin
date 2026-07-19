from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.engines.core_twin import get_or_create_twin, update_twin_state

def evaluate_decision_metrics(
    db: Session,
    user_id: int,
    title: str,
    choice_made: str,
    risk_level: str, # 'low', 'medium', 'high'
    evidence_collected: List[str],
    decision_speed_seconds: float,
    confidence: float  # 0.0 to 1.0
) -> Dict[str, Any]:
    """Evaluates cognitive indicators from a decision log, checks for potential bias,
    and updates the twin's decision profile.
    """
    twin = get_or_create_twin(db, user_id)
    profile = dict(twin.state.get("decision_profile", {
        "risk_tolerance": 0.5,
        "analytical_thinking": 0.5,
        "intuition": 0.5,
        "evidence_collection_speed": 0.5,
        "decision_speed": 0.5,
        "bias_index": 0.1,
        "consistency": 0.8,
        "tradeoff_handling": 0.5,
        "decision_confidence": 0.5
    }))
    
    # 1. Update Risk Tolerance
    risk_weight = 0.1
    current_risk = profile.get("risk_tolerance", 0.5)
    if risk_level.lower() == "high":
        new_risk = current_risk + risk_weight * (1.0 - current_risk)
    elif risk_level.lower() == "low":
        new_risk = current_risk - risk_weight * current_risk
    else:
        new_risk = current_risk
        
    # 2. Update Analytical Thinking vs Intuition
    # More evidence collected = higher analytical score
    num_evidence = len(evidence_collected)
    evidence_score = min(1.0, num_evidence / 5.0)
    
    # Fast decision + low evidence = intuition-heavy
    # Slow decision + high evidence = analysis-heavy
    speed_factor = max(1.0, decision_speed_seconds / 60.0) # speed relative to a minute
    
    # smoothing factor
    smooth = 0.1
    current_analytical = profile.get("analytical_thinking", 0.5)
    current_intuition = profile.get("intuition", 0.5)
    
    if evidence_score > 0.4:
        new_analytical = current_analytical + smooth * (evidence_score - current_analytical)
        new_intuition = current_intuition + smooth * ((1.0 - speed_factor) - current_intuition)
    else:
        new_analytical = current_analytical - smooth * current_analytical
        new_intuition = current_intuition + smooth * (1.0 - current_intuition)
        
    new_analytical = max(0.1, min(0.9, new_analytical))
    new_intuition = max(0.1, min(0.9, new_intuition))
    
    # 3. Detect Biases
    biases = {}
    bias_sum = 0.0
    
    # Overconfidence bias: high confidence but very little evidence
    if confidence > 0.8 and num_evidence <= 1:
        biases["overconfidence"] = {
            "severity": 0.7,
            "description": "Decision made with high self-reported confidence, but backed by minimal evidence."
        }
        bias_sum += 0.7
        
    # Availability/Speed bias: extremely fast decision (< 5 seconds)
    if decision_speed_seconds > 0 and decision_speed_seconds < 5.0:
        biases["impulsiveness"] = {
            "severity": 0.8,
            "description": "Decision was processed instantly, pointing to potential heuristical availability bias."
        }
        bias_sum += 0.8
        
    # 4. Consistency & Confidence updates
    current_bias = profile.get("bias_index", 0.1)
    new_bias = current_bias + 0.1 * ((bias_sum / 2.0) - current_bias)
    new_bias = max(0.01, min(0.95, new_bias))
    
    profile.update({
        "risk_tolerance": round(new_risk, 3),
        "analytical_thinking": round(new_analytical, 3),
        "intuition": round(new_intuition, 3),
        "bias_index": round(new_bias, 3),
        "decision_confidence": round(confidence, 3)
    })
    
    update_twin_state(db, user_id, "decision_profile", profile)
    return {"profile": profile, "biases_detected": biases}
