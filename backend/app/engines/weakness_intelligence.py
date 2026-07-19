from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.database_models import KnowledgeNode, MemoryItem, KnowledgeEdge
import networkx as nx
from backend.app.engines.knowledge_graph import build_nx_graph

def diagnose_weaknesses(db: Session, user_id: int) -> List[Dict[str, Any]]:
    """Analyzes the user's digital twin state and logs to identify learning weaknesses
    and cognitive discrepancies.
    """
    nodes = db.query(KnowledgeNode).filter(KnowledgeNode.user_id == user_id).all()
    edges = db.query(KnowledgeEdge).filter(KnowledgeEdge.user_id == user_id).all()
    memory_items = db.query(MemoryItem).filter(MemoryItem.user_id == user_id).all()
    
    G = build_nx_graph(nodes, edges)
    weaknesses = []
    
    # Map memory items for easy lookups
    mem_map = {m.concept_id: m for m in memory_items}
    
    # 1. Detect Repeated Mistakes & Memory Decay
    for concept_id, mem in mem_map.items():
        node = G.nodes.get(concept_id)
        if not node:
            continue
            
        # Repetitions reset to 0 indicate failure to recall on the last attempt
        if mem.repetitions == 0 and mem.interval == 1:
            # Check practice history length to see if they've failed repeatedly
            history = node.get("practice_history", [])
            recent_failures = [x for x in history[-3:] if x.get("score", 1.0) < 0.5]
            if len(recent_failures) >= 2:
                weaknesses.append({
                    "category": "repeated_mistakes",
                    "concept_id": concept_id,
                    "title": node.get("title", concept_id),
                    "severity": 0.8,
                    "explanation": f"You have failed assessment checks on '{node.get('title')}' multiple times recently.",
                    "action_item": "Schedule an AI Mentor session for this concept and review its fundamental examples before taking another test."
                })
                
    # 2. Detect Knowledge Bottlenecks
    # A bottleneck is a low-mastery node (< 0.5) that is a prerequisite for many other nodes.
    for node_id in G.nodes():
        node_data = G.nodes[node_id]
        mastery = node_data.get("mastery", 0.0)
        
        if mastery < 0.5:
            # Out-degree in the prerequisite tree tells us how many nodes depend on this
            dependents = len(list(G.successors(node_id)))
            if dependents >= 2:
                weaknesses.append({
                    "category": "knowledge_bottleneck",
                    "concept_id": node_id,
                    "title": node_data.get("title", node_id),
                    "severity": 0.9,
                    "explanation": f"'{node_data.get('title')}' blocks {dependents} subsequent concepts. Mastery is only {int(mastery*100)}%.",
                    "action_item": "Prioritize mastering this node. Succeeding here will unlock pathways to multiple advanced topics."
                })
                
    # 3. Detect Avoided Topics
    # Concept is not started, but ALL its prerequisites are mastered (> 0.75).
    for node_id in G.nodes():
        node_data = G.nodes[node_id]
        if node_data.get("status") == "not_started":
            predecessors = list(G.predecessors(node_id))
            if predecessors:
                all_prereqs_mastered = True
                for pred in predecessors:
                    pred_data = G.nodes[pred]
                    if pred_data.get("mastery", 0.0) < 0.75:
                        all_prereqs_mastered = False
                        break
                        
                if all_prereqs_mastered:
                    weaknesses.append({
                        "category": "avoided_topic",
                        "concept_id": node_id,
                        "title": node_data.get("title", node_id),
                        "severity": 0.4,
                        "explanation": f"You have fully unlocked '{node_data.get('title')}' by mastering its prerequisites, but have not initiated study.",
                        "action_item": "Take the introductory reading session or try a practice challenge to break the barrier."
                    })
                    
    # 4. Confidence Mismatch
    # Mismatch between self-reported quiz confidence and actual performance
    for node_id in G.nodes():
        node_data = G.nodes[node_id]
        mastery = node_data.get("mastery", 0.0)
        confidence = node_data.get("confidence", 0.0)
        
        # We look at nodes with some history
        if node_data.get("status") != "not_started":
            diff = confidence - mastery
            if diff > 0.4:
                weaknesses.append({
                    "category": "overconfidence_gap",
                    "concept_id": node_id,
                    "title": node_data.get("title", node_id),
                    "severity": 0.6,
                    "explanation": f"You feel highly confident ({int(confidence*100)}%) in '{node_data.get('title')}' but your mastery checks indicate a level of {int(mastery*100)}%.",
                    "action_item": "Try a coding or problem-solving test. This will help expose specific edge-cases you might be glossing over."
                })
            elif diff < -0.4:
                weaknesses.append({
                    "category": "underconfidence_gap",
                    "concept_id": node_id,
                    "title": node_data.get("title", node_id),
                    "severity": 0.5,
                    "explanation": f"You have achieved high mastery ({int(mastery*100)}%) in '{node_data.get('title')}' but express low subjective confidence ({int(confidence*100)}%).",
                    "action_item": "Try teaching this concept or solving a higher-tier scenario simulation to build self-efficacy."
                })
                
    # Sort weaknesses by severity descending
    return sorted(weaknesses, key=lambda x: x["severity"], reverse=True)
