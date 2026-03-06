import os


import logging
from contextlib import asynccontextmanager
from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.agent_service import (
    initialize_agent_service,
    shutdown_agent_service,
    agent_workflow_run
)
from api.routes import dashboard, generate, enhance, migrate, analytics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress verbose Azure SDK HTTP logging
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
logging.getLogger("azure.core").setLevel(logging.WARNING)
logging.getLogger("azure").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan handler.
    - Startup: initializes the AgentOrchestrator once (creates agents + workflow).
    - Shutdown: cleans up the orchestrator.
    """
    logger.info("Application startup: initializing agent service...")
    await initialize_agent_service()
    logger.info("Agent service ready. API is accepting requests.")

    yield  # Application runs here

    logger.info("Application shutdown: cleaning up agent service...")
    await shutdown_agent_service()


app = FastAPI(
    title="AI Test Generator API",
    description="Multi-Agent AI Test Case Generator Backend",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(generate.router, prefix="/api/generate", tags=["Generate"])
app.include_router(enhance.router, prefix="/api/enhance", tags=["Enhance"])
app.include_router(migrate.router, prefix="/api/migrate", tags=["Migrate"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }

@app.post("/pushtoJIRA")
async def pushDataToJIRA(jira_project_key: str, epics: str = Body(..., embed=True)):
    """Push generated artifacts to Jira using the MCP tool."""
    try:
        prompt = (
            f"ROUTE TO: testcasegenerator_testcasegenerator_agent\n"
            f"Connect to the JIRA MCP Server and push the following artifacts to Jira project '{jira_project_key}' "
            f"in FOUR sequential steps. Wait for each step to complete and capture the returned Jira keys and URLs before proceeding.\n\n"
            f"ARTIFACTS:\n{epics}\n\n"
            f"Consider Priority Highest for Critical\n"
            f"STEP 1 - Create Epics\n"
            f"  Call jira_batch_create_issues:\n"
            f"    issue_type  = 'Epic'\n"
            f"    summary     = epic name\n"
            f"    description = epic description\n"
            f"  Save each returned jira_issue_key and jira_issue_url as that epic's Jira fields.\n\n"
            f"STEP 2 - Create Features\n"
            f"  Call jira_batch_create_issues:\n"
            f"    issue_type  = 'New Feature'\n"
            f"    summary     = feature name\n"
            f"    description = feature description\n"
            f"    epic_link   = parent epic's Jira key from Step 1\n"
            f"  Save each returned jira_issue_key and jira_issue_url as that feature's Jira fields.\n\n"
            f"STEP 3 - Create Use Cases\n"
            f"  Call jira_batch_create_issues:\n"
            f"    issue_type  = 'Improvement'\n"
            f"    summary     = use case title\n"
            f"    description = use case description (include acceptance criteria) + append at the end:\n"
            f"                  '\\n\\nRelated Feature: <feature_jira_url>' using the parent feature URL from Step 2\n"
            f"  No epic_link or parent_key needed.\n"
            f"  Save each returned jira_issue_key and jira_issue_url as that use case's Jira fields.\n\n"
            f"STEP 4 - Create Test Cases\n"
            f"  Call jira_batch_create_issues:\n"
            f"    issue_type  = 'Task'\n"
            f"    summary     = test case title\n"
            f"    description = full test case text (preconditions, steps, expected result, compliance) + append at the end:\n"
            f"                  '\\n\\nRelated Use Case: <use_case_jira_url>' using the parent use case URL from Step 3\n"
            f"  No epic_link or parent_key needed.\n"
            f"  Save each returned jira_issue_key and jira_issue_url as that test case's Jira fields.\n\n"
            f"After all four steps, update every artifact with its Jira fields "
            f"(jira_issue_key, jira_issue_id, jira_issue_url) and return the fully updated artifact JSON."
        )
        messages = await agent_workflow_run(prompt)
        print("Artifacts\n".join(messages))  # Log the agent's response for debugging
        
        return {"status": "success", "message": messages}
    
    except Exception as e:
        logger.error(f"Error pushing artifacts to Jira: {e}")
        return {"status": "error", "message": str(e)}