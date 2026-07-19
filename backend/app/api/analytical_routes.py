import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
from backend.app.core.database import get_db
from backend.app.core.security import get_current_user
from backend.app.core.events import event_broker
from backend.app.models.database_models import User, KnowledgeNode, LearningSession, MemoryItem, DecisionLog, ReflectionLog
from backend.app.schemas import schemas
from backend.app.engines.assessment import generate_adaptive_quiz, evaluate_assessment_submission
from backend.app.engines.mentor import generate_mentor_response
from backend.app.engines.personalized_learning import generate_learning_plan
from backend.app.engines.simulator import simulate_trajectories
from backend.app.engines.prediction import generate_predictions

router = APIRouter(tags=["analytics"])

# --- ASSESSMENT ---
@router.get("/assessment/quiz", response_model=List[Dict[str, Any]])
def get_quiz(concept_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Generates an adaptive quiz for a specific concept tailored to current user mastery."""
    return generate_adaptive_quiz(db, current_user.id, concept_id)

@router.post("/assessment/submit", response_model=Dict[str, Any])
async def submit_quiz(concept_id: str, submission: Dict[str, str], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Scores responses, registers a quiz session, and broadcasts events to update memory curves."""
    results = evaluate_assessment_submission(db, current_user.id, concept_id, submission)
    
    # Save quiz session in DB
    session = LearningSession(
        user_id=current_user.id,
        session_type="quiz",
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow(),
        data={
            "concept_id": concept_id,
            "score": results["score"],
            "feedback": results["feedback"],
            "incorrect_answers": results["incorrect_answers"],
            "tags": [concept_id, "assessment"]
        }
    )
    db.add(session)
    db.commit()
    
    # Broadcast event asynchronously to activate MemoryAgent SM2 decay & CareerAgent update
    await event_broker.publish("assessment.completed", {
        "user_id": current_user.id,
        "concept_id": concept_id,
        "score": results["score"],
        "grade_sm2": results["grade_sm2"]
    })
    
    return results

# --- AI MENTOR ---
@router.post("/mentor/chat", response_model=schemas.MentorChatResponse)
def mentor_chat(chat_in: schemas.MentorChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Communicates with the AI Mentor with current Digital Twin state context."""
    # Convert list of schemas to dictionaries
    messages_list = [{"role": m.role, "content": m.content} for m in chat_in.messages]
    return generate_mentor_response(db, current_user.id, messages_list, chat_in.current_topic)

# --- LEARNING PLAN ---
@router.get("/learning/plan", response_model=Dict[str, Any])
def get_plan(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Generates custom daily/weekly roadmaps and queued revision cards."""
    return generate_learning_plan(db, current_user.id)

# --- SIMULATOR ---
@router.post("/simulator/run", response_model=schemas.SimulationResult)
def run_simulation(sim_in: schemas.SimulationRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Simulates 12-month mastery, retention, and burnout forecasts under a custom strategy."""
    return simulate_trajectories(
        db=db,
        user_id=current_user.id,
        study_minutes_daily=sim_in.study_minutes_daily,
        practice_frequency=sim_in.practice_frequency,
        skip_revision=sim_in.skip_revision,
        strategy=sim_in.strategy,
        months=sim_in.months or 12
    )

# --- PREDICTIONS ---
@router.get("/predictions", response_model=schemas.PredictionResponse)
def get_predictions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Calculates burnout risks and forecasts knowledge forgetting trends."""
    return generate_predictions(db, current_user.id)

# --- BACKUP EXPORT & IMPORT ---
@router.get("/backup/export", response_model=Dict[str, Any])
def export_backup(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Exports all user relational nodes, sessions, decisions, and twin state as a single JSON file."""
    nodes = db.query(KnowledgeNode).filter(KnowledgeNode.user_id == current_user.id).all()
    sessions = db.query(LearningSession).filter(LearningSession.user_id == current_user.id).all()
    decisions = db.query(DecisionLog).filter(DecisionLog.user_id == current_user.id).all()
    reflections = db.query(ReflectionLog).filter(ReflectionLog.user_id == current_user.id).all()
    memory = db.query(MemoryItem).filter(MemoryItem.user_id == current_user.id).all()
    
    # Export serialized structures
    return {
        "twin_state": current_user.twin.state if current_user.twin else {},
        "nodes": [{
            "concept_id": n.concept_id, "title": n.title, "difficulty": n.difficulty,
            "mastery": n.mastery, "confidence": n.confidence, "status": n.status
        } for n in nodes],
        "sessions": [{
            "session_type": s.session_type, "start_time": s.start_time.isoformat(),
            "end_time": s.end_time.isoformat() if s.end_time else None, "data": s.data
        } for s in sessions],
        "decisions": [{
            "title": d.title, "choice_made": d.choice_made, "risk_level": d.risk_level,
            "evidence_collected": d.evidence_collected, "confidence": d.confidence
        } for d in decisions],
        "reflections": [{
            "reflection_type": r.reflection_type, "content": r.content,
            "reflection_date": r.reflection_date.isoformat()
        } for r in reflections]
    }

@router.post("/backup/import")
def import_backup(backup_data: Dict[str, Any], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Parses and loads a backup JSON file, restoring all digital twin states."""
    try:
        # Restore twin state
        if "twin_state" in backup_data:
            twin = current_user.twin
            if twin:
                twin.state = backup_data["twin_state"]
                db.add(twin)
                
        # Restore nodes
        if "nodes" in backup_data:
            # Clear existing user nodes first to prevent primary key issues
            db.query(KnowledgeNode).filter(KnowledgeNode.user_id == current_user.id).delete()
            for n in backup_data["nodes"]:
                node = KnowledgeNode(
                    user_id=current_user.id,
                    concept_id=n["concept_id"],
                    title=n["title"],
                    difficulty=n.get("difficulty", 1.0),
                    mastery=n.get("mastery", 0.0),
                    confidence=n.get("confidence", 0.0),
                    status=n.get("status", "not_started")
                )
                db.add(node)
                
        # Restore sessions
        if "sessions" in backup_data:
            for s in backup_data["sessions"]:
                session = LearningSession(
                    user_id=current_user.id,
                    session_type=s["session_type"],
                    start_time=datetime.fromisoformat(s["start_time"]),
                    end_time=datetime.fromisoformat(s["end_time"]) if s.get("end_time") else None,
                    data=s.get("data", {})
                )
                db.add(session)
                
        db.commit()
        return {"status": "success", "detail": "Backup imported successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to restore backup: {e}")
