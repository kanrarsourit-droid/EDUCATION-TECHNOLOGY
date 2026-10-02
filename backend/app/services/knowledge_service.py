"""Service layer for misconceptions, questions, and interventions."""

import logging
from typing import Any, Dict, List, Union
from uuid import UUID
from postgrest.exceptions import APIError
from app.core.supabase import get_supabase_client

logger = logging.getLogger(__name__)


def get_misconceptions_by_concept(concept_id: Union[UUID, str]) -> List[Dict[str, Any]]:
    """
    Retrieve all misconceptions associated with a specific concept.

    Args:
        concept_id: UUID or string representation of the concept ID.

    Returns:
        List[Dict[str, Any]]: List of misconception records.
    """
    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("misconceptions")
            .select("*")
            .eq("concept_id", str(concept_id))
            .order("created_at", desc=False)
            .execute()
        )
        return response.data or []
    except APIError as exc:
        logger.error("Supabase API error while fetching misconceptions for concept %s: %s", concept_id, exc)
        raise
    except RuntimeError as exc:
        logger.error("Supabase configuration error: %s", exc)
        raise
    except Exception as exc:
        logger.error("Unexpected error while fetching misconceptions for concept %s: %s", concept_id, exc)
        raise


def get_questions_by_concept(concept_id: Union[UUID, str]) -> List[Dict[str, Any]]:
    """
    Retrieve all diagnostic questions associated with a specific concept.

    Args:
        concept_id: UUID or string representation of the concept ID.

    Returns:
        List[Dict[str, Any]]: List of question records.
    """
    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("questions")
            .select("*")
            .eq("concept_id", str(concept_id))
            .order("created_at", desc=False)
            .execute()
        )
        return response.data or []
    except APIError as exc:
        logger.error("Supabase API error while fetching questions for concept %s: %s", concept_id, exc)
        raise
    except RuntimeError as exc:
        logger.error("Supabase configuration error: %s", exc)
        raise
    except Exception as exc:
        logger.error("Unexpected error while fetching questions for concept %s: %s", concept_id, exc)
        raise


def get_interventions_by_misconception(misconception_id: Union[UUID, str]) -> List[Dict[str, Any]]:
    """
    Retrieve all interventions associated with a specific misconception.

    Args:
        misconception_id: UUID or string representation of the misconception ID.

    Returns:
        List[Dict[str, Any]]: List of intervention records.
    """
    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("interventions")
            .select("*")
            .eq("misconception_id", str(misconception_id))
            .order("created_at", desc=False)
            .execute()
        )
        return response.data or []
    except APIError as exc:
        logger.error(
            "Supabase API error while fetching interventions for misconception %s: %s",
            misconception_id,
            exc,
        )
        raise
    except RuntimeError as exc:
        logger.error("Supabase configuration error: %s", exc)
        raise
    except Exception as exc:
        logger.error(
            "Unexpected error while fetching interventions for misconception %s: %s",
            misconception_id,
            exc,
        )
        raise
