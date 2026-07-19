import pytest
from datetime import datetime, timedelta
import networkx as nx
from backend.app.engines.memory_intelligence import sm2_update, calculate_retention
from backend.app.engines.knowledge_graph import build_nx_graph, detect_gaps, get_learning_path
from backend.app.engines.simulator import simulate_trajectories
from backend.app.models.database_models import KnowledgeNode, KnowledgeEdge

def test_sm2_spaced_repetition_calculation():
    # Test perfect grade (q=5) initial check
    interval, ease_factor, reps = sm2_update(q=5, interval=0, ease_factor=2.5, repetitions=0)
    assert interval == 1
    assert reps == 1
    assert ease_factor > 2.5
    
    # Test repetition updates for multiple correct checks
    interval, ease_factor, reps = sm2_update(q=5, interval=1, ease_factor=ease_factor, repetitions=1)
    assert interval == 6
    assert reps == 2

    # Test failure grade (q=1) resets interval and reps
    interval, ease_factor, reps = sm2_update(q=1, interval=6, ease_factor=ease_factor, repetitions=2)
    assert interval == 1
    assert reps == 0

def test_forgetting_retention_curve():
    last_reviewed = datetime.utcnow()
    # Test perfect retention immediately after review
    retention_fresh = calculate_retention(last_reviewed, interval=1, ease_factor=2.5, repetitions=1)
    assert retention_fresh > 0.99
    
    # Test decay over 10 days since review
    decayed_date = datetime.utcnow() - timedelta(days=10)
    retention_decayed = calculate_retention(decayed_date, interval=1, ease_factor=2.5, repetitions=1)
    assert retention_decayed < 0.50

def test_knowledge_graph_traversal_and_gaps():
    # Construct mock nodes
    class MockNode:
        def __init__(self, cid, title, mastery, status):
            self.id = 1
            self.concept_id = cid
            self.title = title
            self.difficulty = 2.0
            self.mastery = mastery
            self.confidence = 0.5
            self.status = status
            self.examples = []
            self.projects = []
            
    class MockEdge:
        def __init__(self, src, tgt):
            self.source_id = src
            self.target_id = tgt
            self.relation_type = "prerequisite"

    nodes = [
        MockNode("node_a", "Node A Core", 0.9, "mastered"),
        MockNode("node_b", "Node B Medium", 0.35, "in_progress"),
        MockNode("node_c", "Node C Advanced", 0.0, "not_started")
    ]
    
    edges = [
        MockEdge("node_a", "node_b"),
        MockEdge("node_b", "node_c")
    ]
    
    G = build_nx_graph(nodes, edges) # type: ignore
    
    # Test gap detection for Node C (Node B is a gap since mastery 0.35 < 0.5)
    gaps = detect_gaps(G, "node_c")
    assert len(gaps) == 1
    assert gaps[0]["concept_id"] == "node_b"
    
    # Test learning paths (must be topologically sorted list [Node A, Node B, Node C])
    path = get_learning_path(G, "node_c")
    assert len(path) == 3
    assert path[0]["concept_id"] == "node_a"
    assert path[1]["concept_id"] == "node_b"
    assert path[2]["concept_id"] == "node_c"

from backend.app.engines.arena import get_scenarios_metadata, evaluate_arena_run
from backend.app.schemas.schemas import ArenaScenarioSubmit, ArenaStepSubmit
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.core.database import Base
from backend.app.models.database_models import User, DigitalTwin

def test_cognitive_arena_evaluation():
    # 1. Setup in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    
    # 2. Seed a user and their digital twin
    user = User(email="test@example.com", hashed_password="hashedpassword", full_name="Test User")
    db.add(user)
    db.commit()
    db.refresh(user)
    
    twin = DigitalTwin(user_id=user.id, state={"decision_profile": {
        "analytical_thinking": 0.5,
        "risk_tolerance": 0.5,
        "decision_speed": 0.5,
        "bias_index": 0.1,
        "decision_confidence": 0.5
    }})
    db.add(twin)
    db.commit()
    
    # 3. Test get scenarios metadata
    scenarios = get_scenarios_metadata()
    assert len(scenarios) == 3
    assert scenarios[0]["id"] == "production_outage"
    # Ensure hidden scoring weights are stripped
    assert "biases" not in scenarios[0]["steps"][0]["options"][0]
    
    # 4. Construct a mock arena submission (impulsive choices, no clues, high confidence)
    submission = ArenaScenarioSubmit(
        scenario_id="production_outage",
        steps=[
            ArenaStepSubmit(step_id=1, option_selected="A", confidence=1.0, time_spent_seconds=2.0, evidence_collected=[]),
            ArenaStepSubmit(step_id=2, option_selected="A", confidence=1.0, time_spent_seconds=3.0, evidence_collected=[]),
            ArenaStepSubmit(step_id=3, option_selected="A", confidence=1.0, time_spent_seconds=1.0, evidence_collected=[])
        ]
    )
    
    # 5. Evaluate the run
    result = evaluate_arena_run(db, user.id, submission)
    
    # Assert result structure and logic
    assert "score" in result
    assert "metrics" in result
    assert "biases_detected" in result
    
    # Check that biases are detected (Impulsiveness & Overconfidence should be flagged)
    biases = result["biases_detected"]
    assert "impulsiveness" in biases or "overconfidence" in biases
    
    # Ensure the digital twin state has been updated via EMA
    db.refresh(twin)
    assert twin.state["decision_profile"]["analytical_thinking"] != 0.5
    
    db.close()

