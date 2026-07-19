from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models.database_models import KnowledgeNode, DigitalTwin
from backend.app.engines.core_twin import get_or_create_twin

# Predefined role requirements mapped to core concepts
ROLE_REQUIREMENTS = {
    "AI Research Engineer": [
        {"concept_id": "python_basics", "required_mastery": 0.85, "title": "Advanced Python Programming"},
        {"concept_id": "linear_algebra", "required_mastery": 0.75, "title": "Linear Algebra for ML"},
        {"concept_id": "neural_networks", "required_mastery": 0.80, "title": "Neural Networks & Deep Learning"},
        {"concept_id": "pytorch_framework", "required_mastery": 0.80, "title": "PyTorch Implementations"},
        {"concept_id": "calculus", "required_mastery": 0.65, "title": "Vector Calculus"}
    ],
    "Backend Engineer": [
        {"concept_id": "python_basics", "required_mastery": 0.90, "title": "Advanced Python Programming"},
        {"concept_id": "relational_db", "required_mastery": 0.85, "title": "Relational Databases & SQL"},
        {"concept_id": "rest_apis", "required_mastery": 0.85, "title": "FastAPI & REST API Architecture"},
        {"concept_id": "systems_design", "required_mastery": 0.75, "title": "Distributed Systems Design"},
        {"concept_id": "security_basics", "required_mastery": 0.70, "title": "Web Security & JWT"}
    ],
    "Data Scientist": [
        {"concept_id": "python_basics", "required_mastery": 0.80, "title": "Python for Data Analysis"},
        {"concept_id": "statistics", "required_mastery": 0.85, "title": "Probability & Mathematical Statistics"},
        {"concept_id": "machine_learning", "required_mastery": 0.80, "title": "Supervised & Unsupervised ML"},
        {"concept_id": "relational_db", "required_mastery": 0.75, "title": "SQL Databases"},
        {"concept_id": "data_viz", "required_mastery": 0.80, "title": "Data Visualization & Communication"}
    ]
}

def analyze_career_readiness(db: Session, user_id: int) -> Dict[str, Any]:
    """Evaluates readiness scores, career gap lists, and target timelines
    relative to target career profiles.
    """
    twin = get_or_create_twin(db, user_id)
    career_target = twin.state.get("career_target", {
        "target_role": "AI Research Engineer",
        "target_date": "2027-12-31"
    })
    
    role = career_target.get("target_role", "AI Research Engineer")
    if role not in ROLE_REQUIREMENTS:
        role = "AI Research Engineer"
        
    requirements = ROLE_REQUIREMENTS[role]
    nodes = db.query(KnowledgeNode).filter(KnowledgeNode.user_id == user_id).all()
    
    # Map user concept masteries
    mastery_map = {n.concept_id: n.mastery for n in nodes}
    
    gaps = []
    total_required_score = 0.0
    user_matching_score = 0.0
    
    for req in requirements:
        concept_id = req["concept_id"]
        required = req["required_mastery"]
        user_has = mastery_map.get(concept_id, 0.0)
        
        total_required_score += required
        user_matching_score += min(required, user_has)
        
        if user_has < required:
            gaps.append({
                "concept_id": concept_id,
                "title": req["title"],
                "required_mastery": required,
                "current_mastery": user_has,
                "gap": round(required - user_has, 2),
                "importance": "critical" if required > 0.8 else "medium"
            })
            
    readiness_ratio = user_matching_score / total_required_score if total_required_score > 0 else 0.0
    readiness_ratio = round(readiness_ratio, 3)
    
    # Simulate velocity (based on recent learning sessions, average 3% gain/month)
    # Estimate months needed to hit 90% readiness
    remaining_readiness = 0.9 - readiness_ratio
    months_needed = 0
    if remaining_readiness > 0:
        monthly_velocity = 0.06  # default average progress multiplier
        months_needed = int(round(remaining_readiness / monthly_velocity))
        months_needed = max(1, months_needed)
        
    # Generate simulations of other career path readiness for comparison
    simulations = {}
    for other_role, other_reqs in ROLE_REQUIREMENTS.items():
        other_total = sum(r["required_mastery"] for r in other_reqs)
        other_user = sum(min(r["required_mastery"], mastery_map.get(r["concept_id"], 0.0)) for r in other_reqs)
        simulations[other_role] = round(other_user / other_total, 3) if other_total > 0 else 0.0
        
    # Update career readiness score in twin state
    twin_career = dict(twin.state.get("career_target", {}))
    twin_career["readiness_score"] = readiness_ratio
    twin.state["career_target"] = twin_career
    db.add(twin)
    db.commit()
    
    return {
        "target_role": role,
        "readiness_score": readiness_ratio,
        "months_to_job_ready": months_needed,
        "gaps": gaps,
        "career_path_benchmarks": simulations,
        "explanation": {
            "summary": f"You are currently {int(readiness_ratio*100)}% aligned with requirements for {role}.",
            "advice": (
                f"To secure interview readiness within the projected {months_needed} months, "
                f"focus heavily on clearing the {len(gaps)} missing concept gaps, specifically "
                f"'{gaps[0]['title']}' which represents your largest remaining delta." if gaps else
                "You have cleared all key concept baselines for this role! Focus on portfolio mock-interviews."
            )
        }
    }
