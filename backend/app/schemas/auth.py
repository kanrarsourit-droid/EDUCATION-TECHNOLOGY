"""Authentication and user profile schemas."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class AuthenticatedUserResponse(BaseModel):
    """Schema representing an authenticated Supabase user."""

    id: UUID
    email: Optional[str] = None
    user_metadata: Dict[str, Any] = {}
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class StudentProfileResponse(BaseModel):
    """Schema representing an application student profile linked to an Auth user."""

    id: UUID
    auth_user_id: Optional[UUID] = None
    email: str
    full_name: str
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudentProfileProvisionRequest(BaseModel):
    """Request payload for provisioning or updating a student profile."""

    full_name: Optional[str] = None
