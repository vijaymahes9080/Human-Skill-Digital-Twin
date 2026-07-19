import logging
from backend.app.core.events import event_broker
from backend.app.agents.specialized_agents import (
    memory_agent,
    learning_agent,
    analytics_agent,
    career_agent
)

logger = logging.getLogger("AgentCoordinator")
logger.setLevel(logging.INFO)

def initialize_agent_coordinator():
    """Binds event subscribers to their asynchronous agent callbacks."""
    logger.info("Initializing Agent Coordinator & Registering Subscribers...")
    
    # 1. Bind session completions
    event_broker.subscribe(
        "session.completed", 
        learning_agent.process_session_completion
    )
    
    # 2. Bind skills analysis updates
    event_broker.subscribe(
        "session.completed",
        analytics_agent.process_skill_update
    )
    
    # 3. Bind assessment score updates
    event_broker.subscribe(
        "assessment.completed",
        memory_agent.process_quiz_event
    )
    
    # 4. Bind career readiness triggers
    event_broker.subscribe(
        "assessment.completed",
        career_agent.process_readiness_recalc
    )
    
    event_broker.subscribe(
        "node.mastery_updated",
        career_agent.process_readiness_recalc
    )
    
    logger.info("All specialized cognitive agents registered successfully.")
