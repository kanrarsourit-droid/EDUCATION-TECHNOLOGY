"""Service layer for Supabase Storage operations."""

import logging
from typing import Any, Dict
from storage3.exceptions import StorageApiError
from app.core.supabase import get_supabase_client

logger = logging.getLogger(__name__)

LEARNING_MATERIALS_BUCKET = "learning-materials"


def ensure_learning_materials_bucket() -> Dict[str, Any]:
    """
    Ensures the private 'learning-materials' storage bucket exists.

    Checks whether the bucket already exists in Supabase Storage.
    If not present, creates it as a private bucket (public=False).
    Idempotent and safe: never deletes or replaces existing buckets.

    Returns:
        Dict[str, Any]: Status summary of the bucket.

    Raises:
        StorageApiError: If a Supabase Storage API error occurs.
        RuntimeError: If configuration is missing or invalid.
        Exception: For unexpected network or runtime errors.
    """
    client = get_supabase_client()

    # Check if bucket already exists
    try:
        buckets = client.storage.list_buckets()
        existing = next(
            (
                b
                for b in buckets
                if getattr(b, "id", None) == LEARNING_MATERIALS_BUCKET
                or getattr(b, "name", None) == LEARNING_MATERIALS_BUCKET
            ),
            None,
        )
        if existing:
            return {
                "status": "exists",
                "bucket": LEARNING_MATERIALS_BUCKET,
                "public": getattr(existing, "public", False),
            }
    except Exception as exc:
        logger.warning("Could not list storage buckets: %s", exc)

    # Bucket not found in list, attempt creation with public=False
    try:
        client.storage.create_bucket(
            id=LEARNING_MATERIALS_BUCKET,
            name=LEARNING_MATERIALS_BUCKET,
            options={"public": False},
        )
        logger.info("Successfully created private storage bucket: %s", LEARNING_MATERIALS_BUCKET)
        return {
            "status": "created",
            "bucket": LEARNING_MATERIALS_BUCKET,
            "public": False,
        }
    except Exception as exc:
        # Handle concurrent creation race condition safely
        err_msg = str(exc).lower()
        if "already exists" in err_msg or "duplicate" in err_msg or "409" in err_msg:
            logger.info("Storage bucket %s already exists (concurrent create)", LEARNING_MATERIALS_BUCKET)
            return {
                "status": "exists",
                "bucket": LEARNING_MATERIALS_BUCKET,
                "public": False,
            }
        logger.error("Failed to ensure storage bucket %s: %s", LEARNING_MATERIALS_BUCKET, exc)
        raise
