import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.agent_service import (
    initialize_agent_service,
    shutdown_agent_service,
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
