import requests
import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.engines.core_twin import get_or_create_twin
from backend.app.engines.weakness_intelligence import diagnose_weaknesses
from backend.app.engines.career_intelligence import analyze_career_readiness
from backend.app.core.config import settings

def query_local_ollama(prompt: str, system_context: str) -> str:
    """Attempts to fetch responses from local Ollama endpoint.
    
    Returns response content or raises Exception if offline.
    """
    try:
        url = f"{settings.OLLAMA_HOST}/api/chat"
        payload = {
            "model": settings.LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_context},
                {"role": "user", "content": prompt}
            ],
            "stream": False
        }
        res = requests.post(url, json=payload, timeout=8.0)
        if res.status_code == 200:
            data = res.json()
            return data["message"]["content"]
    except Exception:
        pass
    raise ConnectionError("Ollama host is unreachable or model not found locally.")

def generate_mentor_response(
    db: Session, 
    user_id: int, 
    messages: List[Dict[str, str]], 
    current_topic: str = None
) -> Dict[str, Any]:
    """Orchestrates the AI Mentor conversation, injecting complete Digital Twin parameters into context."""
    # 1. Fetch Twin context
    twin = get_or_create_twin(db, user_id)
    dna = twin.state.get("learning_dna", {})
    skills = twin.state.get("skills", {})
    
    dominant_style = sorted(
        [{"style": k, "score": v["score"]} for k, v in dna.items() if k != "mixed"],
        key=lambda x: x["score"],
        reverse=True
    )[0]["style"] if dna else "reading"
    
    weaknesses = diagnose_weaknesses(db, user_id)
    career_status = analyze_career_readiness(db, user_id)
    
    # Construct summary context
    twin_ctx = (
        f"You are the AI Mentor for the Human Skill Digital Twin platform. "
        f"The user you are advising has the following digital twin profile:\n"
        f"- Target Career: {career_status['target_role']} (Readiness: {int(career_status['readiness_score']*100)}%)\n"
        f"- Dominant Learning Style: {dominant_style} learner\n"
        f"- Top Skills: " + ", ".join([f"{k} (level: {v['level']})" for k, v in list(skills.items())[:3]]) + "\n"
        f"- Active Weaknesses: " + ", ".join([f"[{w['category']}] {w['title']}" for w in weaknesses[:2]]) + "\n"
        f"Your task is to provide explanations, career guidance, and answers strictly suited to their profile. "
        f"Keep your tone supportive, structural, and explain details step-by-step."
    )
    
    user_query = messages[-1]["content"] if messages else "Hello"
    
    # 2. Try Local LLM inference
    try:
        reply = query_local_ollama(user_query, twin_ctx)
        source = "local_ollama"
    except (ConnectionError, Exception):
        # 3. Smart local template fallback
        source = "local_rule_engine"
        reply = run_local_rule_mentor(user_query, dominant_style, weaknesses, career_status)
        
    return {
        "message": reply,
        "twin_parameters_injected": {
            "dominant_style": dominant_style,
            "readiness_score": career_status["readiness_score"],
            "target_role": career_status["target_role"],
            "weaknesses_count": len(weaknesses)
        },
        "explanation": {
            "evidence": f"Injected active twin parameters (Style: {dominant_style}, Role: {career_status['target_role']})",
            "reasoning": f"Query routed to {source} to construct personalized feedback.",
            "confidence": 0.85 if source == "local_ollama" else 0.95
        }
    }

def run_local_rule_mentor(query: str, dominant_style: str, weaknesses: List[Dict[str, Any]], career: Dict[str, Any]) -> str:
    """Provides detailed advice matching common keywords, fallback for offline setups."""
    q = query.lower()
    
    if "career" in q or "job" in q or "ready" in q:
        gaps_str = "\n".join([f"  • {g['title']} (Delta: -{int(g['gap']*100)}%)" for g in career["gaps"]]) if career["gaps"] else "None (Ready!)"
        return (
            f"Analyzing your profile alignment for the role of **{career['target_role']}**:\n\n"
            f"Your current readiness ratio is **{int(career['readiness_score']*100)}%**. "
            f"According to your skill velocity, you are approximately **{career['months_to_job_ready']} months** away from job readiness.\n\n"
            f"To accelerate, you should cover the following concepts first:\n{gaps_str}\n\n"
            f"Since your dominant style is **{dominant_style}**, I suggest finding active "
            f"{'coding tutorials' if dominant_style == 'project' else 'video lecture walkthroughs' if dominant_style == 'visual' else 'research papers'} on these topics."
        )
        
    if "weak" in q or "mistake" in q or "bottleneck" in q:
        if weaknesses:
            weak_list = "\n".join([f"• **{w['title']}** ({w['category']}): {w['explanation']}\n  *Action*: {w['action_item']}" for w in weaknesses[:2]])
            return (
                f"I've scanned your recent interactive runs and found the following bottlenecks:\n\n"
                f"{weak_list}\n\n"
                f"Let's focus today's schedule on these items to stabilize your prerequisite tree!"
            )
        return "Your concept mastery is currently balanced! I found no significant knowledge gaps or repeated mistake patterns."
        
    if "plan" in q or "study" in q or "today" in q:
        return (
            f"Based on your **{dominant_style}** learning preference, here is your target study structure for today:\n\n"
            f"1. **Active Revision** (15 mins): Spend time recalling decaying concepts due in your memory queue.\n"
            f"2. **Concept Exploration** (30 mins): Dive into "
            f"{'video tutorials' if dominant_style == 'visual' else 'hands-on project coding' if dominant_style == 'project' else 'foundational text resources'}.\n"
            f"3. **Self Check** (15 mins): Complete an adaptive challenge block to write updates back to your Digital Twin."
        )
        
    # Default chat responder
    return (
        f"Welcome! As your AI Mentor, I am reading your Digital Twin profile. "
        f"I see you are building skills for **{career['target_role']}** using a **{dominant_style}** learning preference. "
        f"Ask me about your 'career readiness', 'weaknesses', or request a 'study plan' to see tailored advice!"
    )
