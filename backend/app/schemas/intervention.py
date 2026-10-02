"""Intervention schemas for API responses."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class InterventionResponse(BaseModel):
    """Schema representing an intervention returned from the database."""

    id: UUID
    misconception_id: UUID
    title: str
    intervention_type: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
