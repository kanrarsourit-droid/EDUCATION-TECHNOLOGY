"""Schemas for student learning, safe question retrieval, and attempt tracking."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SafeQuestionResponse(BaseModel):
    """
    Schema representing a diagnostic question safe for student viewing.
    Excludes expected answers and private grading rubrics.
    """

    id: UUID
    concept_id: UUID
    title: str
    prompt: str
    question_type: str
    difficulty: str
    rubric: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttemptSubmissionRequest(BaseModel):
    """
    Request schema for a student submitting an attempt on a question.
    Student identity is derived strictly from the authenticated token.
    """

    question_id: UUID
    student_answer: str = Field(
        ...,
        min_length=1,
        description="The student's submitted answer text or selected option.",
    )
    student_reasoning: Optional[str] = Field(
        default=None,
        description="Optional student explanation or reasoning behind the answer.",
    )
    confidence_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional confidence rating between 0.0 and 1.0.",
    )
    parent_attempt_id: Optional[UUID] = Field(
        default=None,
        description="Optional UUID of a previous attempt if this submission is a retry.",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("student_answer")
    @classmethod
    def validate_student_answer(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("student_answer must not be empty or whitespace only.")
        return stripped


class AttemptResponse(BaseModel):
    """
    Safe response schema returning details of a recorded student attempt.
    """

    id: UUID
    question_id: UUID
    attempt_number: int
    parent_attempt_id: Optional[UUID] = None
    student_answer: str
    student_reasoning: Optional[str] = None
    is_correct: Optional[bool] = None
    confidence_score: Optional[float] = None
    detected_misconception_id: Optional[UUID] = None
    analysis_reasoning: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
