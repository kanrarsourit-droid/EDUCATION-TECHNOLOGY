"""Question schemas for API responses."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class QuestionResponse(BaseModel):
    """Schema representing a diagnostic question returned from the database."""

    id: UUID
    concept_id: UUID
    title: str
    prompt: str
    question_type: str
    expected_answer: str
    rubric: Optional[Dict[str, Any]] = None
    difficulty: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
