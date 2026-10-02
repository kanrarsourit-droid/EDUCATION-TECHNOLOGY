"""Service layer for topic data operations."""

import logging
from typing import Any, Dict, List, Union
from uuid import UUID
from postgrest.exceptions import APIError
from app.core.supabase import get_supabase_client

logger = logging.getLogger(__name__)


def get_topics_by_subject(subject_id: Union[UUID, str]) -> List[Dict[str, Any]]:
    """
    Retrieve all topics belonging to a specific subject, ordered by order_index.

    Args:
        subject_id: UUID or string representation of the subject ID.

    Returns:
        List[Dict[str, Any]]: List of topic records.

    Raises:
        APIError: If the PostgREST / Supabase request returns an error.
        RuntimeError: If Supabase configuration is missing or invalid.
        Exception: For other unexpected errors.
    """
    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("topics")
            .select("*")
            .eq("subject_id", str(subject_id))
            .order("order_index", desc=False)
            .execute()
        )
        return response.data or []
    except APIError as exc:
        logger.error("Supabase API error while fetching topics for subject %s: %s", subject_id, exc)
        raise
    except RuntimeError as exc:
        logger.error("Supabase configuration error: %s", exc)
        raise
    except Exception as exc:
        logger.error("Unexpected error while fetching topics for subject %s: %s", subject_id, exc)
        raise
