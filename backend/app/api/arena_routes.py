from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.app.core.database import get_db
from backend.app.core.security import get_current_user
from backend.app.models.database_models import User
from backend.app.schemas import schemas
from backend.app.engines.arena import get_scenarios_metadata, evaluate_arena_run

router = APIRouter(tags=["arena"])

@router.get("/arena/scenarios", response_model=List[Dict[str, Any]])
def get_arena_scenarios(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Exposes details of all active timed simulation scenarios for the client."""
    try:
        return get_scenarios_metadata()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch scenarios: {e}")

@router.post("/arena/submit", response_model=schemas.ArenaScenarioResult)
def submit_arena_run(submission: schemas.ArenaScenarioSubmit, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Receives and evaluates responses to a completed scenario, updates the twin profile, and returns analysis."""
    try:
        result = evaluate_arena_run(db, current_user.id, submission)
        return result
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scenario evaluation failed: {e}")
