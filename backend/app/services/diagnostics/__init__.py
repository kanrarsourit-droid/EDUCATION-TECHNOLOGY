"""Diagnostics adapter package for subject-specific reasoning and misconception detection."""

from typing import Dict, Type
from app.services.diagnostics.base import BaseSubjectDiagnostic, DiagnosticEvaluation
from app.services.diagnostics.mathematics import MathematicsDiagnostic

_ADAPTER_REGISTRY: Dict[str, BaseSubjectDiagnostic] = {
    "mathematics": MathematicsDiagnostic(),
    "math": MathematicsDiagnostic(),
    "algebra": MathematicsDiagnostic(),
}


def get_diagnostic_adapter(subject_slug_or_name: str = "mathematics") -> BaseSubjectDiagnostic:
    """
    Retrieve the appropriate diagnostic adapter for a given subject.
    Defaults to MathematicsDiagnostic if unspecified or unrecognized.
    """
    key = (subject_slug_or_name or "").strip().lower()
    return _ADAPTER_REGISTRY.get(key, MathematicsDiagnostic())


__all__ = [
    "BaseSubjectDiagnostic",
    "DiagnosticEvaluation",
    "MathematicsDiagnostic",
    "get_diagnostic_adapter",
]
