"""Concept schemas for API responses."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ConceptResponse(BaseModel):
    """Schema representing a concept returned from the database."""

    id: UUID
    topic_id: UUID
    name: str
    description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
