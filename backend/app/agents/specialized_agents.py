import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.app.core.database import SessionLocal
from backend.app.engines.memory_intelligence import update_memory_state
from backend.app.engines.skill_intelligence import update_skills_from_activity
from backend.app.engines.learning_dna import update_learning_dna_from_session
from backend.app.engines.career_intelligence import analyze_career_readiness
from backend.app.engines.core_twin import get_or_create_twin

logger = logging.getLogger("SpecializedAgents")
logger.setLevel(logging.INFO)

class BaseAgent:
    def __init__(self, name: str):
        self.name = name

    def get_db(self) -> Session:
        return SessionLocal()

class MemoryAgent(BaseAgent):
    async def process_quiz_event(self, payload: Dict[str, Any]):
        """Processes quiz score logging, updates decay, ease factors, and intervals."""
        logger.info(f"[{self.name}] Processing quiz event for user {payload.get('user_id')}")
        db = self.get_db()
        try:
            user_id = payload["user_id"]
            concept_id = payload["concept_id"]
            grade_sm2 = payload["grade_sm2"]
            
            update_memory_state(db, user_id, concept_id, grade_sm2)
            logger.info(f"[{self.name}] Memory state successfully updated for concept: {concept_id}")
        except Exception as e:
            logger.error(f"[{self.name}] Error processing quiz event: {e}", exc_info=True)
        finally:
            db.close()

class LearningAgent(BaseAgent):
    async def process_session_completion(self, payload: Dict[str, Any]):
        """Adjusts the user's learning style distributions based on focus hours."""
        logger.info(f"[{self.name}] Processing session completion for user {payload.get('user_id')}")
        db = self.get_db()
        try:
            user_id = payload["user_id"]
            session_type = payload["session_type"]
            duration = payload["duration_minutes"]
            perf = payload.get("performance", 0.5)
            
            update_learning_dna_from_session(db, user_id, session_type, duration, perf)
            logger.info(f"[{self.name}] Learning DNA successfully updated.")
        except Exception as e:
            logger.error(f"[{self.name}] Error updating DNA: {e}", exc_info=True)
        finally:
            db.close()

class AnalyticsAgent(BaseAgent):
    async def process_skill_update(self, payload: Dict[str, Any]):
        """Evaluates skill mastery levels from activity tags."""
        logger.info(f"[{self.name}] Processing skill update from activity.")
        db = self.get_db()
        try:
            user_id = payload["user_id"]
            activity_type = payload["activity_type"]
            tags = payload.get("tags", [])
            performance = payload.get("performance", 0.5)
            
            update_skills_from_activity(db, user_id, activity_type, tags, performance)
            logger.info(f"[{self.name}] Skills successfully updated.")
        except Exception as e:
            logger.error(f"[{self.name}] Error updating skills: {e}", exc_info=True)
        finally:
            db.close()

class CareerAgent(BaseAgent):
    async def process_readiness_recalc(self, payload: Dict[str, Any]):
        """Recalculates career roadmap scores whenever node mastery values shift."""
        logger.info(f"[{self.name}] Recalculating career readiness for user {payload.get('user_id')}")
        db = self.get_db()
        try:
            user_id = payload["user_id"]
            analyze_career_readiness(db, user_id)
            logger.info(f"[{self.name}] Career readiness updated.")
        except Exception as e:
            logger.error(f"[{self.name}] Error updating career readiness: {e}", exc_info=True)
        finally:
            db.close()

# Instantiate global agents
memory_agent = MemoryAgent("MemoryAgent")
learning_agent = LearningAgent("LearningAgent")
analytics_agent = AnalyticsAgent("AnalyticsAgent")
career_agent = CareerAgent("CareerAgent")
