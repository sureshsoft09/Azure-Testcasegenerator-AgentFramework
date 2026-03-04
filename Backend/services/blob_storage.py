"""
Azure Blob Storage service for uploading and managing files.
"""
import logging
from azure.storage.blob import BlobServiceClient, ContentSettings
from core.config import settings

logger = logging.getLogger(__name__)


class BlobStorageService:
    """Service for interacting with Azure Blob Storage."""
    
    def __init__(self):
        """Initialize the blob storage service."""
        self.connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
        self.container_name = settings.AZURE_STORAGE_CONTAINER_NAME
        self.blob_service_client = None
        
        if self.connection_string:
            try:
                self.blob_service_client = BlobServiceClient.from_connection_string(
                    self.connection_string
                )
                logger.info(f"Blob storage client initialized for container: {self.container_name}")
            except Exception as e:
                logger.error(f"Failed to initialize blob storage client: {e}")
        else:
            logger.warning("Azure Storage connection string not configured")
    
    async def upload_blob(
        self, 
        content: bytes, 
        blob_name: str, 
        content_type: str = "application/octet-stream"
    ) -> str:
        """
        Upload a blob to Azure Storage.
        
        Args:
            content: The file content as bytes
            blob_name: The name of the blob
            content_type: The MIME type of the content
            
        Returns:
            The URL of the uploaded blob
            
        Raises:
            Exception: If upload fails
        """
        if not self.blob_service_client:
            raise Exception("Blob storage client not initialized. Check configuration.")
        
        try:
            # Get container client
            container_client = self.blob_service_client.get_container_client(
                self.container_name
            )
            
            # Create container if it doesn't exist
            try:
                container_client.get_container_properties()
            except Exception:
                container_client.create_container()
                logger.info(f"Created container: {self.container_name}")
            
            # Upload blob
            blob_client = container_client.get_blob_client(blob_name)
            blob_client.upload_blob(
                content,
                overwrite=True,
                content_settings=ContentSettings(content_type=content_type)
            )
            
            blob_url = blob_client.url
            logger.info(f"Uploaded blob: {blob_name} to {blob_url}")
            return blob_url
            
        except Exception as e:
            logger.error(f"Failed to upload blob {blob_name}: {e}")
            raise Exception(f"Failed to upload file: {str(e)}")
    
    async def delete_blob(self, blob_name: str) -> bool:
        """
        Delete a blob from Azure Storage.
        
        Args:
            blob_name: The name of the blob to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        if not self.blob_service_client:
            logger.error("Blob storage client not initialized")
            return False
        
        try:
            container_client = self.blob_service_client.get_container_client(
                self.container_name
            )
            blob_client = container_client.get_blob_client(blob_name)
            blob_client.delete_blob()
            logger.info(f"Deleted blob: {blob_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete blob {blob_name}: {e}")
            return False


# Singleton instance
blob_storage_service = BlobStorageService()


async def upload_blob(content: bytes, blob_name: str, content_type: str = "application/octet-stream") -> str:
    """
    Convenience function to upload a blob.
    
    Args:
        content: The file content as bytes
        blob_name: The name of the blob
        content_type: The MIME type of the content
        
    Returns:
        The URL of the uploaded blob
    """
    return await blob_storage_service.upload_blob(content, blob_name, content_type)
