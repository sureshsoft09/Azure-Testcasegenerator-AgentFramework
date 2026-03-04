from azure.storage.blob.aio import BlobServiceClient
from core.config import settings
import logging

logger = logging.getLogger(__name__)

_blob_client: BlobServiceClient = None


async def get_blob_service_client() -> BlobServiceClient:
    global _blob_client
    if _blob_client is None:
        _blob_client = BlobServiceClient.from_connection_string(
            settings.AZURE_STORAGE_CONNECTION_STRING
        )
    return _blob_client


async def upload_blob(file_bytes: bytes, blob_name: str, content_type: str = "application/octet-stream") -> str:
    """Upload a file to Azure Blob Storage and return the blob URL."""
    try:
        client = await get_blob_service_client()
        container_client = client.get_container_client(settings.AZURE_STORAGE_CONTAINER_NAME)
        blob_client = container_client.get_blob_client(blob_name)
        await blob_client.upload_blob(
            file_bytes,
            overwrite=True,
            content_settings={"content_type": content_type},
        )
        return blob_client.url
    except Exception as e:
        logger.error(f"Blob upload failed for {blob_name}: {e}")
        raise


async def delete_blob(blob_name: str):
    try:
        client = await get_blob_service_client()
        container_client = client.get_container_client(settings.AZURE_STORAGE_CONTAINER_NAME)
        blob_client = container_client.get_blob_client(blob_name)
        await blob_client.delete_blob()
    except Exception as e:
        logger.warning(f"Could not delete blob {blob_name}: {e}")
