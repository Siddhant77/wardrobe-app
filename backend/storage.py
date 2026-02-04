"""
Storage abstraction layer for closetGPT.
Supports MinIO (local dev) and Cloudflare R2 (production).
Both use S3-compatible APIs via boto3.
"""

import io
from pathlib import Path
from typing import BinaryIO
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from config import get_settings


class StorageClient:
    """Unified storage client for MinIO and R2."""

    def __init__(self):
        """Initialize storage client based on configuration."""
        self.settings = get_settings()
        self.client = self._create_client()
        self.bucket = self._get_bucket_name()

    def _create_client(self):
        """Create boto3 S3 client based on storage provider."""
        if self.settings.storage_provider == "minio":
            # MinIO configuration
            return boto3.client(
                "s3",
                endpoint_url=f"http://{self.settings.minio_endpoint}",
                aws_access_key_id=self.settings.minio_access_key,
                aws_secret_access_key=self.settings.minio_secret_key,
                config=Config(signature_version="s3v4"),
                region_name=self.settings.minio_region,
            )

        elif self.settings.storage_provider == "r2":
            # Cloudflare R2 configuration
            account_id = self.settings.r2_account_id
            return boto3.client(
                "s3",
                endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
                aws_access_key_id=self.settings.r2_access_key_id,
                aws_secret_access_key=self.settings.r2_secret_access_key,
                config=Config(signature_version="s3v4"),
                region_name="auto",
            )

        else:
            raise ValueError(f"Unsupported storage provider: {self.settings.storage_provider}")

    def _get_bucket_name(self) -> str:
        """Get bucket name based on storage provider."""
        if self.settings.storage_provider == "minio":
            return self.settings.minio_bucket
        elif self.settings.storage_provider == "r2":
            return self.settings.r2_bucket
        else:
            raise ValueError(f"Unsupported storage provider: {self.settings.storage_provider}")

    def upload_file(
        self, file_data: bytes | BinaryIO, object_key: str, content_type: str = "application/octet-stream"
    ) -> tuple[str, str]:
        """
        Upload a file to storage.

        Args:
            file_data: File content as bytes or file-like object
            object_key: Object key (path) in the bucket
            content_type: MIME type of the file

        Returns:
            Tuple of (internal_url, public_url)
        """
        try:
            # Convert bytes to BytesIO if needed
            if isinstance(file_data, bytes):
                file_data = io.BytesIO(file_data)

            # Upload to storage
            self.client.upload_fileobj(
                file_data,
                self.bucket,
                object_key,
                ExtraArgs={"ContentType": content_type},
            )

            # Return both internal and public URLs
            return self.get_internal_url(object_key), self.get_public_url(object_key)

        except ClientError as e:
            raise RuntimeError(f"Failed to upload file: {e}")

    def download_file(self, object_key: str) -> bytes:
        """
        Download a file from storage.

        Args:
            object_key: Object key (path) in the bucket

        Returns:
            File content as bytes
        """
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=object_key)
            return response["Body"].read()

        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundError(f"Object not found: {object_key}")
            raise RuntimeError(f"Failed to download file: {e}")

    def delete_file(self, object_key: str) -> None:
        """
        Delete a file from storage.

        Args:
            object_key: Object key (path) in the bucket
        """
        try:
            self.client.delete_object(Bucket=self.bucket, Key=object_key)

        except ClientError as e:
            raise RuntimeError(f"Failed to delete file: {e}")

    def file_exists(self, object_key: str) -> bool:
        """
        Check if a file exists in storage.

        Args:
            object_key: Object key (path) in the bucket

        Returns:
            True if file exists, False otherwise
        """
        try:
            self.client.head_object(Bucket=self.bucket, Key=object_key)
            return True
        except ClientError:
            return False

    def get_internal_url(self, object_key: str) -> str:
        """
        Get internal URL for an object (for backend-to-storage communication).

        Args:
            object_key: Object key (path) in the bucket

        Returns:
            Internal URL for backend access
        """
        if self.settings.storage_provider == "minio":
            # MinIO internal URL (Docker network)
            protocol = "https" if self.settings.minio_use_ssl else "http"
            return f"{protocol}://{self.settings.minio_endpoint}/{self.bucket}/{object_key}"

        elif self.settings.storage_provider == "r2":
            # R2 uses same URL for internal/public
            account_id = self.settings.r2_account_id
            return f"https://{account_id}.r2.cloudflarestorage.com/{self.bucket}/{object_key}"

    def get_public_url(self, object_key: str) -> str:
        """
        Get public URL for an object.

        Args:
            object_key: Object key (path) in the bucket

        Returns:
            Public URL to access the file
        """
        if self.settings.storage_provider == "minio":
            # MinIO public URL (accessible from browser)
            endpoint = self.settings.minio_public_endpoint or self.settings.minio_endpoint
            protocol = "https" if self.settings.minio_use_ssl else "http"
            return f"{protocol}://{endpoint}/{self.bucket}/{object_key}"

        elif self.settings.storage_provider == "r2":
            # R2 public URL (use custom domain if configured)
            if self.settings.r2_public_url:
                base_url = self.settings.r2_public_url.rstrip("/")
                return f"{base_url}/{object_key}"
            else:
                # Default R2 URL format
                account_id = self.settings.r2_account_id
                return f"https://{account_id}.r2.cloudflarestorage.com/{self.bucket}/{object_key}"

    def list_files(self, prefix: str = "") -> list[str]:
        """
        List files in storage with optional prefix.

        Args:
            prefix: Optional prefix to filter files

        Returns:
            List of object keys
        """
        try:
            response = self.client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
            if "Contents" not in response:
                return []
            return [obj["Key"] for obj in response["Contents"]]

        except ClientError as e:
            raise RuntimeError(f"Failed to list files: {e}")

    def generate_presigned_url(self, object_key: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL for temporary access.

        Args:
            object_key: Object key (path) in the bucket
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            Presigned URL
        """
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": object_key},
                ExpiresIn=expiration,
            )
            return url

        except ClientError as e:
            raise RuntimeError(f"Failed to generate presigned URL: {e}")


# Global storage client instance
_storage_client: StorageClient | None = None


def get_storage_client() -> StorageClient:
    """Get the global storage client instance."""
    global _storage_client
    if _storage_client is None:
        _storage_client = StorageClient()
    return _storage_client


if __name__ == "__main__":
    # Test storage client
    storage = get_storage_client()
    print(f"Storage Provider: {storage.settings.storage_provider}")
    print(f"Bucket: {storage.bucket}")
    print("Storage client initialized successfully!")
