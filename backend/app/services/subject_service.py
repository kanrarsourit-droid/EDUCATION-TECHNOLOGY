"""Service layer for subject data operations."""

import logging
from typing import Any, Dict, List
from postgrest.exceptions import APIError
from app.core.supabase import get_supabase_client

logger = logging.getLogger(__name__)


def get_all_subjects() -> List[Dict[str, Any]]:
    """
    Retrieve all subject rows from the Supabase database.

    Returns:
        List[Dict[str, Any]]: List of subject records.

    Raises:
        APIError: If the PostgREST / Supabase request returns an error.
        RuntimeError: If Supabase configuration is missing or invalid.
        Exception: For other network or client errors.
    """
    try:
        supabase = get_supabase_client()
        response = supabase.table("subjects").select("*").order("name").execute()
        return response.data or []
    except APIError as exc:
        logger.error("Supabase API error while fetching subjects: %s", exc)
        raise
    except RuntimeError as exc:
        logger.error("Supabase configuration error: %s", exc)
        raise
    except Exception as exc:
        logger.error("Unexpected error while fetching subjects: %s", exc)
        raise
