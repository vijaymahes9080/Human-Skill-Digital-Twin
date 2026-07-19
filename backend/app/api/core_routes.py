from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
from backend.app.core.database import get_db
from backend.app.core.security import get_current_user
from backend.app.core.events import event_broker
from backend.app.models.database_models import User, LearningSession, DecisionLog, ReflectionLog, KnowledgeNode, KnowledgeEdge
from backend.app.schemas import schemas
from backend.app.engines.core_twin import get_or_create_twin, update_twin_state
from backend.app.engines.knowledge_graph import sync_knowledge_graph_data, build_nx_graph, detect_gaps, get_learning_path
from backend.app.engines.decision_intelligence import evaluate_decision_metrics
from backend.app.engines.reflection import generate_reflection

router = APIRouter(tags=["core"])

# --- TWIN ---
@router.get("/twin", response_model=schemas.DigitalTwinResponse)
def get_twin(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Fetches the user's active digital twin state object."""
    return get_or_create_twin(db, current_user.id)

@router.put("/twin", response_model=schemas.DigitalTwinResponse)
def update_twin(updates: schemas.DigitalTwinUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Directly updates/overwrites sections of the digital twin state."""
    twin = get_or_create_twin(db, current_user.id)
    twin.state = updates.state
    db.add(twin)
    db.commit()
    db.refresh(twin)
    return twin

# --- KNOWLEDGE GRAPH ---
@router.get("/knowledge/graph", response_model=Dict[str, Any])
def get_knowledge_graph(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Computes coordinates and formatting data to render the interactive Knowledge Graph."""
    return sync_knowledge_graph_data(db, current_user.id)

@router.get("/knowledge/gaps", response_model=List[Dict[str, Any]])
def get_knowledge_gaps(target_concept_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Evaluates low mastery prerequisite concepts blocking a specific concept."""
    nodes = db.query(KnowledgeNode).filter(KnowledgeNode.user_id == current_user.id).all()
    edges = db.query(KnowledgeEdge).filter(KnowledgeEdge.user_id == current_user.id).all()
    G = build_nx_graph(nodes, edges)
    return detect_gaps(G, target_concept_id)

@router.get("/knowledge/path/{concept_id}", response_model=List[Dict[str, Any]])
def get_concept_path(concept_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Computes a topological learning path list leading to the targeted concept."""
    nodes = db.query(KnowledgeNode).filter(KnowledgeNode.user_id == current_user.id).all()
    edges = db.query(KnowledgeEdge).filter(KnowledgeEdge.user_id == current_user.id).all()
    G = build_nx_graph(nodes, edges)
    return get_learning_path(G, concept_id)

# --- SESSIONS ---
@router.get("/sessions", response_model=List[schemas.LearningSessionResponse])
def get_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lists logged learning activities."""
    return db.query(LearningSession).filter(LearningSession.user_id == current_user.id).order_by(LearningSession.start_time.desc()).all()

@router.post("/sessions", response_model=schemas.LearningSessionResponse)
async def create_session(session_in: schemas.LearningSessionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Registers a completed learning session and asynchronously fires agent updates."""
    # Standardize end time if not set
    start = session_in.start_time or datetime.utcnow()
    end = session_in.end_time or datetime.utcnow()
    duration = max(1.0, (end - start).total_seconds() / 60.0)
    
    session = LearningSession(
        user_id=current_user.id,
        session_type=session_in.session_type,
        start_time=start,
        end_time=end,
        data=session_in.data
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Fire session.completed event
    await event_broker.publish("session.completed", {
        "user_id": current_user.id,
        "session_id": session.id,
        "session_type": session.session_type,
        "duration_minutes": duration,
        "performance": session.data.get("score", 0.5),
        "activity_type": session.session_type,
        "tags": session.data.get("tags", [])
    })
    
    return session

# --- DECISION LOGS ---
@router.get("/decisions", response_model=List[schemas.DecisionLogResponse])
def get_decisions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lists all decision records."""
    return db.query(DecisionLog).filter(DecisionLog.user_id == current_user.id).order_by(DecisionLog.created_at.desc()).all()

@router.post("/decisions", response_model=schemas.DecisionLogResponse)
def create_decision(decision_in: schemas.DecisionLogCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Creates a decision log, evaluates metrics/biases, and updates decision profile."""
    log = DecisionLog(
        user_id=current_user.id,
        title=decision_in.title,
        description=decision_in.description,
        choice_made=decision_in.choice_made,
        risk_level=decision_in.risk_level,
        evidence_collected=decision_in.evidence_collected,
        decision_speed_seconds=decision_in.decision_speed_seconds,
        confidence=decision_in.confidence,
        status=decision_in.status,
        outcome=decision_in.outcome
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    
    # Evaluate decision parameters and update the Twin state profile
    evaluate_decision_metrics(
        db=db,
        user_id=current_user.id,
        title=log.title,
        choice_made=log.choice_made,
        risk_level=log.risk_level,
        evidence_collected=log.evidence_collected,
        decision_speed_seconds=log.decision_speed_seconds or 10.0,
        confidence=log.confidence
    )
    
    return log

# --- REFLECTIONS ---
@router.get("/reflections", response_model=List[schemas.ReflectionLogResponse])
def get_reflections(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lists reflection logs."""
    return db.query(ReflectionLog).filter(ReflectionLog.user_id == current_user.id).order_by(ReflectionLog.reflection_date.desc()).all()

@router.post("/reflections", response_model=Dict[str, Any])
def run_reflection(reflection_type: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Triggers and stores a reflection analysis summarizing recent study records."""
    if reflection_type not in ["daily", "weekly", "monthly"]:
        raise HTTPException(status_code=400, detail="Invalid reflection type.")
    return generate_reflection(db, current_user.id, reflection_type)
