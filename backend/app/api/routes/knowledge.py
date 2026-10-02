"""API routes for Knowledge Domain (Topics, Concepts, Misconceptions, Questions, Interventions)."""

import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from postgrest.exceptions import APIError

from app.schemas.concept import ConceptResponse
from app.schemas.intervention import InterventionResponse
from app.schemas.misconception import MisconceptionResponse
from app.schemas.question import QuestionResponse
from app.schemas.topic import TopicResponse
from app.services.concept_service import get_concepts_by_topic
from app.services.knowledge_service import (
    get_interventions_by_misconception,
    get_misconceptions_by_concept,
    get_questions_by_concept,
)
from app.services.topic_service import get_topics_by_subject

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/subjects/{subject_id}/topics",
    response_model=List[TopicResponse],
    summary="List Topics for a Subject",
    description="Retrieve all topics associated with a given subject ID, ordered by order_index.",
    tags=["topics"],
)
async def list_topics_by_subject(subject_id: UUID) -> List[TopicResponse]:
    """Retrieve topics for a given subject."""
    try:
        topics = get_topics_by_subject(subject_id)
        return topics
    except APIError as exc:
        logger.error("Database query failed while fetching topics for subject %s: %s", subject_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Database service error while retrieving topics.",
        )
    except RuntimeError as exc:
        logger.error("Configuration error while fetching topics: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Unexpected error while fetching topics for subject %s: %s", subject_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving topics.",
        )


@router.get(
    "/topics/{topic_id}/concepts",
    response_model=List[ConceptResponse],
    summary="List Concepts for a Topic",
    description="Retrieve all concepts associated with a given topic ID, ordered alphabetically.",
    tags=["concepts"],
)
async def list_concepts_by_topic(topic_id: UUID) -> List[ConceptResponse]:
    """Retrieve concepts for a given topic."""
    try:
        concepts = get_concepts_by_topic(topic_id)
        return concepts
    except APIError as exc:
        logger.error("Database query failed while fetching concepts for topic %s: %s", topic_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Database service error while retrieving concepts.",
        )
    except RuntimeError as exc:
        logger.error("Configuration error while fetching concepts: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Unexpected error while fetching concepts for topic %s: %s", topic_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving concepts.",
        )


@router.get(
    "/concepts/{concept_id}/misconceptions",
    response_model=List[MisconceptionResponse],
    summary="List Misconceptions for a Concept",
    description="Retrieve all known misconceptions associated with a given concept ID.",
    tags=["misconceptions"],
)
async def list_misconceptions_by_concept(concept_id: UUID) -> List[MisconceptionResponse]:
    """Retrieve misconceptions for a given concept."""
    try:
        misconceptions = get_misconceptions_by_concept(concept_id)
        return misconceptions
    except APIError as exc:
        logger.error("Database query failed while fetching misconceptions for concept %s: %s", concept_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Database service error while retrieving misconceptions.",
        )
    except RuntimeError as exc:
        logger.error("Configuration error while fetching misconceptions: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Unexpected error while fetching misconceptions for concept %s: %s", concept_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving misconceptions.",
        )


@router.get(
    "/concepts/{concept_id}/questions",
    response_model=List[QuestionResponse],
    summary="List Questions for a Concept",
    description="Retrieve all diagnostic questions associated with a given concept ID.",
    tags=["questions"],
)
async def list_questions_by_concept(concept_id: UUID) -> List[QuestionResponse]:
    """Retrieve questions for a given concept."""
    try:
        questions = get_questions_by_concept(concept_id)
        return questions
    except APIError as exc:
        logger.error("Database query failed while fetching questions for concept %s: %s", concept_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Database service error while retrieving questions.",
        )
    except RuntimeError as exc:
        logger.error("Configuration error while fetching questions: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Unexpected error while fetching questions for concept %s: %s", concept_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving questions.",
        )


@router.get(
    "/misconceptions/{misconception_id}/interventions",
    response_model=List[InterventionResponse],
    summary="List Interventions for a Misconception",
    description="Retrieve all remedial interventions associated with a given misconception ID.",
    tags=["interventions"],
)
async def list_interventions_by_misconception(misconception_id: UUID) -> List[InterventionResponse]:
    """Retrieve interventions for a given misconception."""
    try:
        interventions = get_interventions_by_misconception(misconception_id)
        return interventions
    except APIError as exc:
        logger.error(
            "Database query failed while fetching interventions for misconception %s: %s",
            misconception_id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Database service error while retrieving interventions.",
        )
    except RuntimeError as exc:
        logger.error("Configuration error while fetching interventions: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error(
            "Unexpected error while fetching interventions for misconception %s: %s",
            misconception_id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving interventions.",
        )
