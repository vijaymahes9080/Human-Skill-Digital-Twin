import networkx as nx
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.app.models.database_models import KnowledgeNode, KnowledgeEdge

def build_nx_graph(nodes: List[KnowledgeNode], edges: List[KnowledgeEdge]) -> nx.DiGraph:
    """Builds a NetworkX Directed Graph from SQLAlchemy node and edge entities."""
    G = nx.DiGraph()
    
    # Add nodes with metadata
    for n in nodes:
        G.add_node(
            n.concept_id,
            id=n.id,
            title=n.title,
            difficulty=n.difficulty,
            mastery=n.mastery,
            confidence=n.confidence,
            status=n.status,
            examples=n.examples,
            projects=n.projects
        )
        
    # Add edges
    for e in edges:
        G.add_edge(e.source_id, e.target_id, relation=e.relation_type)
        
    return G

def get_hierarchical_layout(G: nx.DiGraph) -> Dict[str, Tuple[float, float]]:
    """Calculates hierarchical coordinates (x, y) based on prerequisite depth.
    
    X is spacing within layer, Y is depth layer (height).
    """
    # Find root nodes (in-degree is 0)
    roots = [n for n, d in G.in_degree() if d == 0]
    
    # Calculate depth using shortest paths from any root
    depths = {}
    for node in G.nodes():
        min_depth = 0
        for root in roots:
            try:
                path_len = len(nx.shortest_path(G, source=root, target=node)) - 1
                min_depth = max(min_depth, path_len)
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                pass
        depths[node] = min_depth
        
    # Group nodes by depth
    levels: Dict[int, List[str]] = {}
    for node, d in depths.items():
        if d not in levels:
            levels[d] = []
        levels[d].append(node)
        
    coords = {}
    max_depth = max(levels.keys()) if levels else 1
    
    # Generate coordinates mapping to a nice space e.g. [0, 800] width, [0, 600] height
    y_step = 120
    for level, nodes_in_level in levels.items():
        num_nodes = len(nodes_in_level)
        x_step = 800 / (num_nodes + 1)
        for idx, node in enumerate(sorted(nodes_in_level)):
            coords[node] = (
                x_step * (idx + 1),  # x coordinate
                level * y_step + 50  # y coordinate
            )
            
    return coords

def detect_gaps(G: nx.DiGraph, target_concept_id: str) -> List[Dict[str, Any]]:
    """Detects concepts that are prerequisites of target, but have low mastery (< 0.5)."""
    if target_concept_id not in G:
        return []
        
    # Find all predecessors (direct and indirect)
    predecessors = nx.ancestors(G, target_concept_id)
    gaps = []
    
    for pred in predecessors:
        node_data = G.nodes[pred]
        mastery = node_data.get("mastery", 0.0)
        if mastery < 0.5:
            gaps.append({
                "concept_id": pred,
                "title": node_data.get("title", pred),
                "mastery": mastery,
                "confidence": node_data.get("confidence", 0.0),
                "status": node_data.get("status", "not_started"),
                "reason": f"Required prerequisite for '{G.nodes[target_concept_id].get('title')}' is not mastered."
            })
            
    # Sort gaps by mastery ascending (worst gaps first)
    return sorted(gaps, key=lambda x: x["mastery"])

def get_learning_path(G: nx.DiGraph, target_concept_id: str) -> List[Dict[str, Any]]:
    """Computes an ordered checklist of prerequisite concepts to master the target."""
    if target_concept_id not in G:
        return []
        
    # Get subgraph of all ancestors + the target itself
    ancestors = nx.ancestors(G, target_concept_id)
    ancestors.add(target_concept_id)
    subgraph = G.subgraph(ancestors)
    
    # Perform topological sort on dependencies (directed acyclic prerequisites)
    try:
        ordered_concepts = list(nx.topological_sort(subgraph))
    except nx.NetworkXUnfeasible:
        # Cyclic dependency fallback
        ordered_concepts = list(subgraph.nodes())
        
    path_nodes = []
    for concept in ordered_concepts:
        nd = G.nodes[concept]
        path_nodes.append({
            "concept_id": concept,
            "title": nd.get("title", concept),
            "mastery": nd.get("mastery", 0.0),
            "confidence": nd.get("confidence", 0.0),
            "status": nd.get("status", "not_started")
        })
        
    return path_nodes

def sync_knowledge_graph_data(db: Session, user_id: int) -> Dict[str, Any]:
    """Queries DB and builds graph JSON for visual rendering on the frontend."""
    nodes = db.query(KnowledgeNode).filter(KnowledgeNode.user_id == user_id).all()
    edges = db.query(KnowledgeEdge).filter(KnowledgeEdge.user_id == user_id).all()
    
    G = build_nx_graph(nodes, edges)
    coords = get_hierarchical_layout(G)
    
    nodes_json = []
    for n in nodes:
        x, y = coords.get(n.concept_id, (100, 100))
        nodes_json.append({
            "id": n.concept_id,
            "type": "conceptNode",
            "position": {"x": x, "y": y},
            "data": {
                "title": n.title,
                "difficulty": n.difficulty,
                "mastery": n.mastery,
                "confidence": n.confidence,
                "status": n.status,
                "examples": n.examples,
                "projects": n.projects
            }
        })
        
    edges_json = []
    for idx, e in enumerate(edges):
        edges_json.append({
            "id": f"e-{e.source_id}-{e.target_id}",
            "source": e.source_id,
            "target": e.target_id,
            "type": "smoothstep",
            "animated": G.nodes[e.source_id].get("mastery", 0) > 0.8 and G.nodes[e.target_id].get("mastery", 0) < 0.2,
            "label": e.relation_type,
            "style": {"stroke": "#4f46e5", "strokeWidth": 2}
        })
        
    return {"nodes": nodes_json, "edges": edges_json}
