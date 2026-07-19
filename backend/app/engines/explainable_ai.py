from typing import Dict, Any, List

def make_explanation(
    evidence: str,
    reasoning: str,
    confidence: float,
    alternatives: List[Dict[str, str]] = None,
    advantages: List[str] = None,
    disadvantages: List[str] = None
) -> Dict[str, Any]:
    """Wraps any engine decision in a clear, explainable format for the end-user.
    
    Ensures that every AI decision explains the evidence, reasoning, confidence, and trade-offs.
    """
    return {
        "evidence": evidence,
        "reasoning": reasoning,
        "confidence_score": round(confidence, 3),
        "alternatives": alternatives or [],
        "advantages": advantages or [],
        "disadvantages": disadvantages or []
    }
