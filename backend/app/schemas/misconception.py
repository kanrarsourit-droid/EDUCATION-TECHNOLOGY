"""Misconception schemas for API responses."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class MisconceptionResponse(BaseModel):
    """Schema representing a misconception returned from the database."""

    id: UUID
    concept_id: UUID
    name: str
    description: str
    canonical_example: Optional[str] = None
    severity: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
