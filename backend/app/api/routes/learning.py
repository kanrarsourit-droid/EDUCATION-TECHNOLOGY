"""API routes for student learning workflows: safe question retrieval and attempt tracking."""

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from postgrest.exceptions import APIError

from app.api.routes.auth import get_current_user
from app.schemas.auth import AuthenticatedUserResponse
from app.schemas.diagnostic import DiagnosticResponse
from app.schemas.learning import (
    AttemptResponse,
    AttemptSubmissionRequest,
    SafeQuestionResponse,
)
from app.services.auth_service import get_student_by_auth_user_id
from app.services.concept_service import get_concept_by_id
from app.services.diagnostic_service import (
    AttemptNotFoundError,
    AttemptOwnershipError,
    analyze_attempt,
)
from app.services.learning_service import (
    ConceptNotFoundError,
    InvalidRetryAttemptError,
    ParentAttemptNotFoundError,
    QuestionNotFoundError,
    create_student_attempt,
    get_safe_questions_by_concept,
    get_student_attempts,
)

router = APIRouter(prefix="/learning", tags=["learning"])
logger = logging.getLogger(__name__)


async def get_current_student(
    current_user: AuthenticatedUserResponse = Depends(get_current_user),
) -> dict:
    """
    Dependency that resolves the application student profile for the authenticated user.

    Raises:
        HTTPException(404): If no student profile is linked to this authenticated account.
    """
    student = get_student_by_auth_user_id(current_user.id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No student profile is linked to this authenticated account. Please provision a profile first.",
        )
    return student


@router.get(
    "/concepts/{concept_id}/questions",
    response_model=List[SafeQuestionResponse],
    summary="Get Safe Diagnostic Questions for a Concept",
    description=(
        "Retrieves diagnostic questions for a concept in student-safe format. "
        "Excludes expected answers and grading rubrics to prevent premature answer discovery."
    ),
)
async def get_concept_questions(
    concept_id: UUID,
    student: dict = Depends(get_current_student),
) -> List[SafeQuestionResponse]:
    """Retrieve safe questions for a concept, requiring authenticated student access."""
    try:
        concept = get_concept_by_id(concept_id)
        if not concept:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Concept with ID '{concept_id}' not found.",
            )

        questions = get_safe_questions_by_concept(concept_id)
        return [SafeQuestionResponse(**q) for q in questions]
    except HTTPException:
        raise
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
        logger.error("Unexpected error fetching questions for concept %s: %s", concept_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving questions.",
        )


@router.post(
    "/attempts",
    response_model=AttemptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Student Question Attempt",
    description=(
        "Records an authenticated student's attempt on a question with deterministic evaluation. "
        "Supports retry attempts by chaining to a valid parent attempt."
    ),
)
async def submit_attempt(
    payload: AttemptSubmissionRequest,
    student: dict = Depends(get_current_student),
) -> AttemptResponse:
    """Submit a question attempt for the authenticated student."""
    try:
        attempt = create_student_attempt(
            student_id=student["id"],
            question_id=payload.question_id,
            student_answer=payload.student_answer,
            student_reasoning=payload.student_reasoning,
            confidence_score=payload.confidence_score,
            parent_attempt_id=payload.parent_attempt_id,
        )
        return AttemptResponse(**attempt)
    except QuestionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except ParentAttemptNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except InvalidRetryAttemptError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except APIError as exc:
        logger.error("Database query failed while inserting attempt: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Database service error while recording attempt.",
        )
    except RuntimeError as exc:
        logger.error("Configuration error while recording attempt: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Unexpected error recording attempt: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while recording attempt.",
        )


@router.get(
    "/attempts",
    response_model=List[AttemptResponse],
    summary="List Student Attempt History",
    description=(
        "Retrieves past attempts belonging exclusively to the authenticated student. "
        "Cannot be used to view another student's history."
    ),
)
async def list_student_attempts(
    question_id: Optional[UUID] = Query(default=None, description="Filter by question ID"),
    concept_id: Optional[UUID] = Query(default=None, description="Filter by concept ID"),
    limit: int = Query(default=50, ge=1, le=100, description="Max attempts to return"),
    student: dict = Depends(get_current_student),
) -> List[AttemptResponse]:
    """Retrieve attempt history for the authenticated student."""
    try:
        attempts = get_student_attempts(
            student_id=student["id"],
            question_id=question_id,
            concept_id=concept_id,
            limit=limit,
        )
        return [AttemptResponse(**a) for a in attempts]
    except APIError as exc:
        logger.error("Database query failed while fetching student attempts: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Database service error while retrieving attempts.",
        )
    except RuntimeError as exc:
        logger.error("Configuration error while fetching attempts: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Unexpected error fetching student attempts: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving attempts.",
        )


@router.post(
    "/attempts/{attempt_id}/diagnose",
    response_model=DiagnosticResponse,
    status_code=status.HTTP_200_OK,
    summary="Run Diagnostic Analysis on Student Attempt",
    description=(
        "Analyzes an authenticated student's attempt to identify conceptual misconceptions, "
        "deliver targeted interventions, evaluate retry repairs, and update concept mastery."
    ),
)
async def diagnose_attempt(
    attempt_id: UUID,
    student: dict = Depends(get_current_student),
) -> DiagnosticResponse:
    """Execute diagnostic analysis on a recorded attempt."""
    try:
        return analyze_attempt(student_id=student["id"], attempt_id=attempt_id)
    except AttemptNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except AttemptOwnershipError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
    except QuestionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except APIError as exc:
        logger.error("Database query failed during attempt diagnosis: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Database service error during diagnosis.",
        )
    except RuntimeError as exc:
        logger.error("Configuration error during attempt diagnosis: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Unexpected error during attempt diagnosis: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during diagnostic analysis.",
        )

