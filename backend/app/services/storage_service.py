"""
Storage abstraction for Vercel deployment.

Vercel serverless has ephemeral /tmp. This service uploads to Vercel Blob
when BLOB_READ_WRITE_TOKEN is configured, otherwise falls back to local disk.

Blob URL is stored in File.storage_path when blob is enabled (so DB survives
cold starts). ensure_local() downloads blob URL to /tmp on-demand for
ingestion/transcription which require a local file path.
"""

import os
import logging
import mimetypes
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def is_blob_url(path: str) -> bool:
    return path is not None and (
        path.startswith("http://") or path.startswith("https://")
    )


class StorageService:
    async def upload_to_blob(
        self, local_path: str, filename: str, content_type: Optional[str] = None
    ) -> Optional[str]:
        """
        Upload a local file to Vercel Blob.
        Returns blob URL on success, None on failure.
        """
        if not settings.is_blob_enabled:
            return None

        token = settings.BLOB_READ_WRITE_TOKEN.strip()
        # Vercel Blob REST API: PUT https://blob.vercel-storage.com/<pathname>
        # Docs: https://vercel.com/docs/storage/vercel-blob/using-blob-sdk
        # For raw REST, the hostname is blob.vercel-storage.com
        blob_pathname = f"uploads/{filename}"
        url = f"https://blob.vercel-storage.com/{blob_pathname}"

        if not content_type:
            content_type, _ = mimetypes.guess_type(filename)
            content_type = content_type or "application/octet-stream"

        try:
            file_size = os.path.getsize(local_path)
            # Vercel Blob has 500MB limit per file for hobby, matches our MAX_FILE_SIZE
            async with httpx.AsyncClient(timeout=60) as client:
                with open(local_path, "rb") as f:
                    data = f.read()
                resp = await client.put(
                    url,
                    content=data,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "x-content-type": content_type,
                        "x-add-random-suffix": "1",
                    },
                )
                if resp.status_code not in (200, 201):
                    logger.warning(
                        f"Vercel Blob upload failed {resp.status_code}: {resp.text}"
                    )
                    return None
                body = resp.json()
                blob_url = body.get("url")
                if blob_url:
                    logger.info(
                        f"Uploaded {filename} ({file_size} bytes) to Blob: {blob_url}"
                    )
                    return blob_url
                logger.warning(f"Blob upload no url in response: {body}")
                return None
        except Exception as e:
            logger.warning(f"Blob upload exception for {filename}: {e}")
            return None

    def ensure_local(self, storage_path: str) -> str:
        """
        Ensure storage_path is a local file path.
        If it's a blob URL, download to /tmp/blob_cache and return that path.
        If it's a local path that exists, return as-is.
        If it's a local path that is missing on Vercel, raise FileNotFoundError with context.
        Synchronous helper for ingestion_service (which already runs in threadpool/background).
        For blob URLs this does a blocking download via httpx sync.
        """
        if is_blob_url(storage_path):
            # Download to cache
            cache_dir = "/tmp/blob_cache"
            os.makedirs(cache_dir, exist_ok=True)
            # Derive filename from URL (strip query)
            filename = storage_path.split("/")[-1].split("?")[0] or "download"
            local_cached = os.path.join(cache_dir, filename)
            if os.path.exists(local_cached):
                return local_cached
            # Blocking download (ingestion runs in background task, okay to block)
            try:
                logger.info(f"Downloading blob {storage_path} to {local_cached}")
                with httpx.Client(timeout=60, follow_redirects=True) as client:
                    with client.stream("GET", storage_path) as resp:
                        resp.raise_for_status()
                        with open(local_cached, "wb") as out:
                            for chunk in resp.iter_bytes():
                                out.write(chunk)
                return local_cached
            except Exception as e:
                raise FileNotFoundError(
                    f"Failed to download blob {storage_path}: {e}"
                ) from e

        # Local path case
        if os.path.exists(storage_path):
            return storage_path

        # Missing local file - on Vercel this is expected after cold start
        if settings.is_vercel or settings.is_blob_enabled:
            # Provide actionable error
            raise FileNotFoundError(
                "File not found on ephemeral disk. "
                "On Vercel, files in /tmp do not persist across deployments/restarts. "
                "Re-upload the file or configure BLOB_READ_WRITE_TOKEN for persistent storage."
            )
        # Local dev/test: return path as-is so mocked parsers can run (file may not exist on disk in tests)
        # Caller (parse_pdf / transcription) will raise if it truly needs the file
        return storage_path

    async def ensure_local_async(self, storage_path: str) -> str:
        """Async version for use in async routes."""
        if not is_blob_url(storage_path):
            if os.path.exists(storage_path):
                return storage_path
            if settings.is_vercel or settings.is_blob_enabled:
                raise FileNotFoundError(
                    "File not found on ephemeral disk. Configure BLOB_READ_WRITE_TOKEN."
                )
            return storage_path

        cache_dir = "/tmp/blob_cache"
        os.makedirs(cache_dir, exist_ok=True)
        filename = storage_path.split("/")[-1].split("?")[0] or "download"
        local_cached = os.path.join(cache_dir, filename)
        if os.path.exists(local_cached):
            return local_cached
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            resp = await client.get(storage_path)
            resp.raise_for_status()
            with open(local_cached, "wb") as out:
                out.write(resp.content)
        return local_cached


storage_service = StorageService()
