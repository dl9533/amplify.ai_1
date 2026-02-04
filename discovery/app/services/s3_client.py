"""S3 storage client for file uploads."""
import logging

import aioboto3
from botocore.exceptions import ClientError
from typing import Any

logger = logging.getLogger(__name__)


class S3Client:
    """Async S3 client for file storage operations."""

    def __init__(
        self,
        endpoint_url: str | None,
        bucket: str,
        access_key: str | None,
        secret_key: str | None,
        region: str,
    ) -> None:
        self.endpoint_url = endpoint_url
        self.bucket = bucket
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self._session = aioboto3.Session()

    def _get_client_config(self) -> dict[str, Any]:
        """Get boto3 client configuration."""
        config: dict[str, Any] = {
            "service_name": "s3",
            "region_name": self.region,
        }
        if self.endpoint_url:
            config["endpoint_url"] = self.endpoint_url
        if self.access_key and self.secret_key:
            config["aws_access_key_id"] = self.access_key
            config["aws_secret_access_key"] = self.secret_key
        return config

    async def upload_file(
        self,
        key: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> dict[str, str]:
        """Upload file to S3.

        Args:
            key: S3 object key (path).
            content: File content as bytes.
            content_type: MIME type of the file.

        Returns:
            Dict with url and key.

        Raises:
            ClientError: If the upload fails.
        """
        logger.debug("Uploading file to S3: %s (%d bytes)", key, len(content))
        async with self._session.client(**self._get_client_config()) as s3:
            await s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=content,
                ContentType=content_type,
            )

        url = f"s3://{self.bucket}/{key}"
        if self.endpoint_url:
            url = f"{self.endpoint_url}/{self.bucket}/{key}"

        logger.debug("Successfully uploaded file to S3: %s", key)
        return {"url": url, "key": key}

    async def download_file(self, key: str) -> bytes:
        """Download file from S3.

        Args:
            key: S3 object key.

        Returns:
            File content as bytes.

        Raises:
            ClientError: If the download fails.
        """
        logger.debug("Downloading file from S3: %s", key)
        async with self._session.client(**self._get_client_config()) as s3:
            response = await s3.get_object(Bucket=self.bucket, Key=key)
            content = await response["Body"].read()
            logger.debug("Successfully downloaded file from S3: %s (%d bytes)", key, len(content))
            return content

    async def delete_file(self, key: str) -> bool:
        """Delete file from S3.

        Args:
            key: S3 object key.

        Returns:
            True if deleted successfully.

        Raises:
            ClientError: If the deletion fails.
        """
        logger.debug("Deleting file from S3: %s", key)
        async with self._session.client(**self._get_client_config()) as s3:
            await s3.delete_object(Bucket=self.bucket, Key=key)
            logger.debug("Successfully deleted file from S3: %s", key)
            return True

    async def file_exists(self, key: str) -> bool:
        """Check if file exists in S3.

        Args:
            key: S3 object key.

        Returns:
            True if file exists, False if not found.

        Raises:
            ClientError: If there's an error other than 404 Not Found.
        """
        try:
            async with self._session.client(**self._get_client_config()) as s3:
                await s3.head_object(Bucket=self.bucket, Key=key)
                logger.debug("File exists in S3: %s", key)
                return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            # Handle both "404" and "NoSuchKey" as "not found"
            if error_code in ("404", "NoSuchKey"):
                logger.debug("File not found in S3: %s", key)
                return False
            # Re-raise non-404 errors (auth issues, network errors, etc.)
            logger.error("S3 error checking file existence for %s: %s", key, e)
            raise
