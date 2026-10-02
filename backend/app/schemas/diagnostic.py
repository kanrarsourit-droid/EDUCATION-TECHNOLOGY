"""Schemas for the Learning Debugger diagnostic engine."""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class DiagnosticResponse(BaseModel):
    """
    Diagnostic result returned after analyzing a student attempt.
    Excludes sensitive fields like expected answers or internal rubrics.
    """

    attempt_id: UUID
    is_correct: Optional[bool] = None
    diagnostic_status: str = Field(
        ...,
        description="One of: correct, misconception_detected, insufficient_evidence, retry_required, repaired",
    )
    detected_misconception: bool = False
    misconception_id: Optional[UUID] = None
    misconception_name: Optional[str] = None
    misconception_description: Optional[str] = None
    severity: Optional[str] = None
    intervention: Optional[bool] = False
    intervention_id: Optional[UUID] = None
    intervention_type: Optional[str] = None
    intervention_content: Optional[str] = None
    mastery_score: float = Field(..., ge=0.0, le=1.0)
    mastery_status: str = Field(
        ...,
        description="One of: unstarted, in_progress, mastered, needs_review",
    )
    next_action: str = Field(
        ...,
        description="Recommended next step, e.g. retry, proceed, review_intervention",
    )

    model_config = ConfigDict(from_attributes=True)
