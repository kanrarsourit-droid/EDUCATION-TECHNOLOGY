"""
Temporary development endpoint for verifying Supabase connectivity.
"""

import logging
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.core.supabase import get_supabase_client

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/supabase/health", summary="Supabase Health Check")
async def supabase_health() -> JSONResponse:
    """
    Verification endpoint for the Supabase integration.

    Safely verifies client initialization and network connectivity
    without creating tables or modifying data.
    Never exposes API keys, URLs, tokens, or other sensitive details.
    """
    try:
        client = get_supabase_client()
    except RuntimeError as exc:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_configured",
                "service": "supabase",
                "message": "Supabase client not initialized. Missing or placeholder credentials in backend/.env",
            },
        )
    except Exception as exc:
        logger.error("Supabase client initialization error: %s", type(exc).__name__)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "service": "supabase",
                "message": "Failed to initialize Supabase client",
            },
        )

    # Safe network verification without modifying data or requiring tables
    network_verified = False
    verification_message = "Supabase client initialized, but network connection could not be verified"
    try:
        # Check authentication service reachability with service role / secret key
        client.auth.admin.list_users(page=1, per_page=1)
        network_verified = True
    except Exception as exc:
        err_text = str(exc).lower()
        if "unregistered api key" in err_text or "invalid api key" in err_text or "401" in err_text:
            verification_message = (
                "Supabase client initialized, but the API key was rejected by Supabase "
                "(invalid or unregistered API key for this project). "
                "Please verify your Secret key in backend/.env."
            )
        logger.warning("Supabase network verification check failed: %s", type(exc).__name__)

    if network_verified:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "connected",
                "service": "supabase",
                "connection": "database network connection verified",
            },
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={
                "status": "client_initialized",
                "service": "supabase",
                "connection": "network verification failed",
                "message": verification_message,
            },
        )
