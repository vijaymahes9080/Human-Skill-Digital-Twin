from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.engines.core_twin import get_or_create_twin
from backend.app.engines.memory_intelligence import get_revision_recommendations
from backend.app.engines.weakness_intelligence import diagnose_weaknesses
from backend.app.models.database_models import KnowledgeNode, KnowledgeEdge
from backend.app.engines.knowledge_graph import build_nx_graph, get_learning_path

# Standard resource databases mapped to styles
RESOURCE_POOL = {
    "visual": [
        {"title": "Visual Introduction and Animation Guide", "type": "Video Lecture", "url": "https://youtube.com/watch?v=intro"},
        {"title": "Video Walkthrough & Implementation Details", "type": "Screen Recording", "url": "https://youtube.com/watch?v=walkthrough"}
    ],
    "reading": [
        {"title": "Core Foundations & Concepts Guide", "type": "Documentation", "url": "https://docs.local/concepts"},
        {"title": "Deep-Dive Scholarly Literature & Implementation Details", "type": "Research Paper", "url": "https://arxiv.org/abs/example"}
    ],
    "project": [
        {"title": "Hands-on Programming Exercise & Challenge", "type": "Coding Sandbox Project", "url": "https://github.com/project-spec"},
        {"title": "Build a CLI / Application Implementing the Concept", "type": "Development Challenge", "url": "https://github.com/challenge-spec"}
    ],
    "experiment": [
        {"title": "Jupyter Notebook Sandbox Workspace", "type": "Notebook Sandbox", "url": "https://colab.research.google.com/notebook"}
    ]
}

def generate_learning_plan(db: Session, user_id: int) -> Dict[str, Any]:
    """Assembles a highly customized daily and weekly roadmap using cognitive weights."""
    twin = get_or_create_twin(db, user_id)
    dna = twin.state.get("learning_dna", {})
    
    # 1. Determine dominant learning style from DNA
    sorted_styles = sorted(
        [{"style": k, "score": v["score"], "conf": v["confidence"]} for k, v in dna.items() if k != "mixed"],
        key=lambda x: x["score"],
        reverse=True
    )
    dominant_style = sorted_styles[0]["style"] if sorted_styles else "reading"
    
    # 2. Collect revisions due
    revisions = get_revision_recommendations(db, user_id)
    
    # 3. Collect weaknesses / bottlenecks
    weaknesses = diagnose_weaknesses(db, user_id)
    
    # 4. Find next concepts to study (concepts in progress or unlocked)
    nodes = db.query(KnowledgeNode).filter(KnowledgeNode.user_id == user_id).all()
    edges = db.query(KnowledgeEdge).filter(KnowledgeEdge.user_id == user_id).all()
    G = build_nx_graph(nodes, edges)
    
    unlocked_concepts = []
    in_progress_concepts = []
    
    for n in nodes:
        if n.status == "in_progress":
            in_progress_concepts.append(n)
        elif n.status == "not_started":
            # Check if all prereqs are done
            prereqs = list(G.predecessors(n.concept_id))
            if not prereqs or all(G.nodes[p].get("mastery", 0.0) >= 0.7 for p in prereqs):
                unlocked_concepts.append(n)
                
    # Build recommendations based on dominant learning style
    resources = RESOURCE_POOL.get(dominant_style, RESOURCE_POOL["reading"])
    
    # 5. Assemble daily plan
    daily_tasks = []
    
    # Add 1 revision if due
    if revisions:
        daily_tasks.append({
            "type": "revision",
            "concept_id": revisions[0]["concept_id"],
            "title": f"Review {revisions[0]['title']}",
            "description": "Spaced repetition due today. Complete review cards or mock quizzes.",
            "duration_est": "15 mins",
            "urgency": revisions[0]["urgency"]
        })
        
    # Add active bottleneck or in-progress node
    next_study = None
    bottlenecks = [w for w in weaknesses if w["category"] == "knowledge_bottleneck"]
    
    if bottlenecks:
        next_study = bottlenecks[0]
        daily_tasks.append({
            "type": "bottleneck_remediation",
            "concept_id": next_study["concept_id"],
            "title": f"Strengthen Foundations: {next_study['title']}",
            "description": f"This node is a bottleneck blocking other concepts. Focus on: {next_study['action_item']}",
            "duration_est": "45 mins",
            "resources": resources
        })
    elif in_progress_concepts:
        next_study = in_progress_concepts[0]
        daily_tasks.append({
            "type": "core_study",
            "concept_id": next_study.concept_id,
            "title": f"Continue: {next_study.title}",
            "description": "Progress your understanding. Build out exercise scripts.",
            "duration_est": "30 mins",
            "resources": resources
        })
    elif unlocked_concepts:
        next_study = unlocked_concepts[0]
        daily_tasks.append({
            "type": "concept_introduction",
            "concept_id": next_study.concept_id,
            "title": f"Introduce Concept: {next_study.title}",
            "description": f"Ready to learn. Introduce yourself using recommended {dominant_style} materials.",
            "duration_est": "30 mins",
            "resources": resources
        })
        
    # Add active challenge / practice session
    daily_tasks.append({
        "type": "practice_challenge",
        "title": "Interactive Simulation Exercise",
        "description": "Take an adaptive quiz or coding challenge to reinforce today's updates.",
        "duration_est": "20 mins"
    })
    
    # 6. Assemble weekly plan
    weekly_goals = []
    if revisions:
        weekly_goals.append(f"Clear {len(revisions)} memory decay items in revision queue.")
    if bottlenecks:
        weekly_goals.append(f"Resolve foundational blockers for: {', '.join(b['title'] for b in bottlenecks[:2])}.")
    if unlocked_concepts:
        weekly_goals.append(f"Initiate study sessions for new paths: {', '.join(c.title for c in unlocked_concepts[:2])}.")
        
    return {
        "dominant_learning_style": dominant_style,
        "style_fit_explanation": (
            f"Your twin exhibits a strong {dominant_style} learning dynamic "
            f"(Score: {int(sorted_styles[0]['score']*100)}%, Confidence: {int(sorted_styles[0]['conf']*100)}%). "
            f"Consequently, study recommendations prioritize {dominant_style}-adapted resource profiles."
        ),
        "daily_plan": daily_tasks,
        "weekly_goals": weekly_goals,
        "flashcard_review_due_count": len(revisions)
    }
