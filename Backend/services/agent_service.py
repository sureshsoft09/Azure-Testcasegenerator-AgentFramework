"""
Agent Service

Manages the AgentOrchestrator lifecycle:
- Initializes once at application startup (setup_agents + initialize_workflow)
- Exposes agent_workflow_run() for per-request workflow execution
"""

import logging
from typing import List

from app_agents.agent_orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)

# Module-level singleton — initialized once at startup
_orchestrator: AgentOrchestrator | None = None


async def initialize_agent_service() -> None:
    """
    Initialize the AgentOrchestrator once at application startup.
    Creates agents in Azure AI Foundry and builds the Handoff workflow.
    Call this from the FastAPI lifespan startup handler.
    """
    global _orchestrator

    logger.info("Initializing AgentOrchestrator...")
    orchestrator = AgentOrchestrator()

    logger.info("Setting up agents in Azure AI Foundry...")
    await orchestrator.setup_agents()

    logger.info("Initializing Handoff workflow...")
    await orchestrator.initialize_workflow()

    _orchestrator = orchestrator
    logger.info("AgentOrchestrator ready.")


async def agent_workflow_run(user_request: str) -> List[str]:
    """
    Run the agent workflow for a given user request.

    Args:
        user_request: The user's input string.

    Returns:
        List of formatted message strings: "[AgentName]: content"

    Raises:
        RuntimeError: If the service has not been initialized yet.
        Exception: Propagates any workflow execution errors.
    """
    if _orchestrator is None:
        raise RuntimeError(
            "Agent service is not initialized. "
            "Ensure initialize_agent_service() was called at startup."
        )

    logger.info(f"Running workflow for request: {user_request[:100]}...")

    messages = await _orchestrator.run_workflow(user_request)

    formatted: List[str] = []
    for msg in messages:
        if isinstance(msg, dict):
            agent_name = msg.get("agent", "agent")
            content = msg.get("content", str(msg))
            formatted.append(f"[{agent_name}]: {content}")
        else:
            formatted.append(str(msg))

    logger.info(f"Workflow completed with {len(formatted)} messages.")
    return formatted


async def shutdown_agent_service() -> None:
    """
    Clean up the AgentOrchestrator at application shutdown.
    Call this from the FastAPI lifespan shutdown handler.
    """
    global _orchestrator
    if _orchestrator is not None:
        await _orchestrator.cleanup()
        _orchestrator = None
        logger.info("AgentOrchestrator cleaned up.")
