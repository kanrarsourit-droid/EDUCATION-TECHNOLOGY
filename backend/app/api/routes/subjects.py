"""API routes for subjects."""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, status
from postgrest.exceptions import APIError
from app.schemas.subject import SubjectResponse
from app.services.subject_service import get_all_subjects

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/subjects",
    response_model=List[SubjectResponse],
    summary="List All Subjects",
    description="Retrieve all available subject domains from the database.",
)
async def list_subjects() -> List[SubjectResponse]:
    """
    Retrieves all subjects from the database.
    Returns an empty list if no subjects have been created yet.
    """
    try:
        subjects = get_all_subjects()
        return subjects
    except APIError as exc:
        logger.error("Database query failed while fetching subjects: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Database service error while retrieving subjects. Please verify database connectivity and credentials.",
        )
    except RuntimeError as exc:
        logger.error("Configuration error while fetching subjects: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Unexpected error while fetching subjects: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving subjects.",
        )
