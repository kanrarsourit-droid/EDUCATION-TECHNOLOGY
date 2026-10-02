"""Topic schemas for API responses."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class TopicResponse(BaseModel):
    """Schema representing a topic returned from the database."""

    id: UUID
    subject_id: UUID
    name: str
    description: Optional[str] = None
    order_index: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
