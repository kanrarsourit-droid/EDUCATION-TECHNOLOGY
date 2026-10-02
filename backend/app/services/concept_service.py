"""Service layer for concept data operations."""

import logging
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from postgrest.exceptions import APIError
from app.core.supabase import get_supabase_client

logger = logging.getLogger(__name__)


def get_concepts_by_topic(topic_id: Union[UUID, str]) -> List[Dict[str, Any]]:
    """
    Retrieve all concepts belonging to a specific topic, ordered alphabetically by name.

    Args:
        topic_id: UUID or string representation of the topic ID.

    Returns:
        List[Dict[str, Any]]: List of concept records.

    Raises:
        APIError: If the PostgREST / Supabase request returns an error.
        RuntimeError: If Supabase configuration is missing or invalid.
        Exception: For other unexpected errors.
    """
    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("concepts")
            .select("*")
            .eq("topic_id", str(topic_id))
            .order("name", desc=False)
            .execute()
        )
        return response.data or []
    except APIError as exc:
        logger.error("Supabase API error while fetching concepts for topic %s: %s", topic_id, exc)
        raise
    except RuntimeError as exc:
        logger.error("Supabase configuration error: %s", exc)
        raise
    except Exception as exc:
        logger.error("Unexpected error while fetching concepts for topic %s: %s", topic_id, exc)
        raise


def get_concept_by_id(concept_id: Union[UUID, str]) -> Optional[Dict[str, Any]]:
    """
    Retrieve a single concept by its ID.

    Args:
        concept_id: UUID or string representation of the concept ID.

    Returns:
        Optional[Dict[str, Any]]: Concept record if found, else None.
    """
    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("concepts")
            .select("*")
            .eq("id", str(concept_id))
            .limit(1)
            .execute()
        )
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except APIError as exc:
        logger.error("Supabase API error while fetching concept %s: %s", concept_id, exc)
        raise
    except RuntimeError as exc:
        logger.error("Supabase configuration error: %s", exc)
        raise
    except Exception as exc:
        logger.error("Unexpected error while fetching concept %s: %s", concept_id, exc)
        raise
