from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey
from core.config import settings
import logging

logger = logging.getLogger(__name__)

_client: CosmosClient = None


async def get_cosmos_client() -> CosmosClient:
    global _client
    if _client is None:
        _client = CosmosClient(url=settings.COSMOS_DB_URL, credential=settings.COSMOS_DB_KEY)
    return _client


async def get_database():
    client = await get_cosmos_client()
    return client.get_database_client(settings.COSMOS_DB_NAME)


async def get_container(container_name: str):
    db = await get_database()
    return db.get_container_client(container_name)


async def ensure_containers():
    """Create containers if they don't exist (dev/init utility)."""
    try:
        client = await get_cosmos_client()
        db = await client.create_database_if_not_exists(settings.COSMOS_DB_NAME)
        containers = [
            (settings.COSMOS_PROJECTS_CONTAINER, "/projectId"),
            (settings.COSMOS_ARTIFACTS_CONTAINER, "/projectId"),
            (settings.COSMOS_SESSIONS_CONTAINER, "/sessionId"),
        ]
        for name, partition_key in containers:
            await db.create_container_if_not_exists(
                id=name, partition_key=PartitionKey(path=partition_key)
            )
        logger.info("Cosmos DB containers ensured.")
    except Exception as e:
        logger.warning(f"Could not ensure Cosmos containers: {e}")
