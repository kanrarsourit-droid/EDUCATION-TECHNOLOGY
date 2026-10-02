"""Subject schemas for API responses."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class SubjectResponse(BaseModel):
    """Schema representing a subject returned from the database."""

    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
