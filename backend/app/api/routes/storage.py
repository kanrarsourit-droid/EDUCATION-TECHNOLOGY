"""API routes for Supabase Storage health and status verification."""

import logging
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from storage3.exceptions import StorageApiError

from app.services.storage_service import LEARNING_MATERIALS_BUCKET, ensure_learning_materials_bucket

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/storage/health",
    summary="Storage Health Check",
    description="Verify that the learning-materials private storage bucket exists and is accessible.",
    tags=["storage"],
)
async def storage_health() -> JSONResponse:
    """
    Verifies that the private 'learning-materials' storage bucket exists and is accessible.

    Returns:
        JSONResponse: status and bucket name.

    Raises:
        HTTPException: If bucket is inaccessible or an error occurs.
    """
    try:
        bucket_info = ensure_learning_materials_bucket()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "connected",
                "bucket": LEARNING_MATERIALS_BUCKET,
            },
        )
    except StorageApiError as exc:
        logger.error("Storage API error in storage health check: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Storage service error: Unable to verify storage bucket.",
        )
    except RuntimeError as exc:
        logger.error("Configuration error in storage health check: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Unexpected error in storage health check: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error verifying storage connectivity.",
        )
