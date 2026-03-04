from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Azure Storage
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_STORAGE_CONTAINER_NAME: str = "requirement-docs"

    # Cosmos DB (direct SDK)
    COSMOS_DB_URL: str = ""
    COSMOS_DB_KEY: str = ""
    COSMOS_DB_NAME: str = "ai-test-generator"
    COSMOS_PROJECTS_CONTAINER: str = "projects"
    COSMOS_ARTIFACTS_CONTAINER: str = "artifacts"
    COSMOS_SESSIONS_CONTAINER: str = "sessions"

    # OpenAI
    OPENAI_API_KEY: str = ""
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4o"
    AZURE_OPENAI_API_VERSION: str = "2024-02-01"

    # Jira (direct SDK fallback)
    JIRA_SERVER: str = ""
    JIRA_EMAIL: str = ""
    JIRA_API_TOKEN: str = ""

    # ─── MCP Server endpoints ───────────────────────────────────────────────
    # Jira MCP Server  (HTTP SSE transport)
    JIRA_MCP_SERVER_URL: str = "http://localhost:3100/sse"
    JIRA_MCP_ENABLED: bool = False

    # CosmosDB MCP Server (HTTP SSE transport)
    COSMOS_MCP_SERVER_URL: str = "http://localhost:3101/sse"
    COSMOS_MCP_ENABLED: bool = False

    # App
    APP_ENV: str = "development"
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
