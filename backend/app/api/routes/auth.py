"""Authentication and user identity routes."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from postgrest.exceptions import APIError
from app.schemas.auth import (
    AuthenticatedUserResponse,
    StudentProfileProvisionRequest,
    StudentProfileResponse,
)
from app.services.auth_service import (
    get_student_by_auth_user_id,
    get_user_from_token,
    provision_or_link_student_profile,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Security scheme for Bearer token extraction without throwing 403 on missing headers
bearer_security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_security),
) -> AuthenticatedUserResponse:
    """
    Dependency that extracts and validates the Supabase access token from Authorization header.

    Raises:
        HTTPException(401): If the token is missing, malformed, expired, or invalid.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a Bearer access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_info = get_user_from_token(credentials.credentials)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or revoked authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthenticatedUserResponse(**user_info)


@router.get(
    "/auth/health",
    summary="Auth Service Health Check",
    description="Verifies that the backend authentication verification service is operational.",
    tags=["auth"],
)
async def auth_health() -> dict[str, str]:
    """Public health check confirming that Supabase Auth verification is active and configured."""
    return {
        "status": "configured",
        "provider": "supabase_auth",
    }


@router.get(
    "/auth/me",
    response_model=AuthenticatedUserResponse,
    summary="Get Current Authenticated User",
    description="Returns the Supabase Auth identity of the user authenticated by the Bearer access token.",
    tags=["auth"],
)
async def get_me(
    current_user: AuthenticatedUserResponse = Depends(get_current_user),
) -> AuthenticatedUserResponse:
    """Returns safe details of the authenticated Supabase user."""
    return current_user


@router.get(
    "/auth/profile",
    response_model=StudentProfileResponse,
    summary="Get Linked Student Profile",
    description="Retrieves the application student profile linked to the authenticated Supabase user ID.",
    tags=["auth"],
)
async def get_profile(
    current_user: AuthenticatedUserResponse = Depends(get_current_user),
) -> StudentProfileResponse:
    """
    Retrieves the student profile linked to the authenticated user's ID.
    Returns 404 if no linked student profile exists.
    """
    student = get_student_by_auth_user_id(current_user.id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No student profile is linked to this authenticated account.",
        )
    return StudentProfileResponse(**student)


@router.post(
    "/auth/profile",
    response_model=StudentProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Create or Link Student Profile",
    description=(
        "Provisions a student profile for the authenticated Supabase user. "
        "Links existing matching student records or creates a new profile safely."
    ),
    tags=["auth"],
)
async def provision_profile(
    payload: Optional[StudentProfileProvisionRequest] = None,
    current_user: AuthenticatedUserResponse = Depends(get_current_user),
) -> StudentProfileResponse:
    """
    Creates or links the application-level student profile for the authenticated user.
    Uses the verified identity from the Supabase access token (never trusts arbitrary client IDs).
    """
    try:
        student = provision_or_link_student_profile(
            auth_user_id=current_user.id,
            email=current_user.email,
            full_name=payload.full_name if payload else None,
            user_metadata=current_user.user_metadata,
        )
        return StudentProfileResponse(**student)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    except APIError as exc:
        logger.error("Database query failed during student provisioning: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Database service error while provisioning student profile.",
        )
    except Exception as exc:
        logger.error("Unexpected error during student provisioning: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while provisioning student profile.",
        )
