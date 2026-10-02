"""Mathematics diagnostic adapter for evaluating algebraic reasoning and misconceptions."""

import re
from typing import Any, Dict, Optional, Set
from app.services.diagnostics.base import BaseSubjectDiagnostic, DiagnosticEvaluation


class MathematicsDiagnostic(BaseSubjectDiagnostic):
    """
    Diagnostic adapter specialized in evaluating algebraic expressions,
    specifically binomial expansion and related polynomial identities.
    """

    # Seeded misconception names
    MISC_MISSING_CROSS_TERM = "Missing the cross term when squaring a binomial"
    MISC_SUM_OF_SQUARES = "Treating a square of a sum as a sum of squares"

    def _normalize_expr(self, expr: str) -> str:
        """Strip spaces, lower case, and standardize exponents."""
        if not expr:
            return ""
        s = expr.strip().lower()
        s = s.replace(" ", "")
        s = s.replace("**", "^")
        return s

    def _is_correct_expansion(self, question: Dict[str, Any], student_answer: str) -> bool:
        """Determine if student answer matches the expected algebraic expansion."""
        norm_answer = self._normalize_expr(student_answer)
        expected = self._normalize_expr(question.get("expected_answer", ""))

        if norm_answer == expected:
            return True

        # Check for MCQ choice matching
        rubric = question.get("rubric") or {}
        if isinstance(rubric, dict):
            choices = rubric.get("choices") or rubric.get("options") or []
            for choice in choices:
                if isinstance(choice, dict):
                    label = self._normalize_expr(str(choice.get("label", "")))
                    text = self._normalize_expr(str(choice.get("text", "")))
                    is_correct = bool(choice.get("is_correct", False))
                    if norm_answer in (label, text):
                        return is_correct

        # Check known polynomial commutative variations for (x + 3)^2
        # e.g. x^2 + 6x + 9, 9 + 6x + x^2, x^2 + 9 + 6x, 6x + x^2 + 9
        if "x+3" in self._normalize_expr(question.get("prompt", "")) or "x+3" in self._normalize_expr(question.get("title", "")):
            valid_forms = {
                "x^2+6x+9",
                "9+6x+x^2",
                "x^2+9+6x",
                "6x+x^2+9",
                "9+x^2+6x",
                "6x+9+x^2",
                "x^2+6*x+9",
            }
            if norm_answer in valid_forms:
                return True

        # For (x + 2)^2:
        if "x+2" in self._normalize_expr(question.get("prompt", "")):
            valid_forms_2 = {
                "x^2+4x+4",
                "4+4x+x^2",
                "4x+x^2+4",
                "x^2+4*x+4",
            }
            if norm_answer in valid_forms_2:
                return True

        return False

    def evaluate(
        self,
        question: Dict[str, Any],
        student_answer: str,
        student_reasoning: Optional[str] = None,
        parent_attempt: Optional[Dict[str, Any]] = None,
    ) -> DiagnosticEvaluation:
        """
        Evaluate a student attempt on a Mathematics question with reasoning inspection.
        """
        is_correct = self._is_correct_expansion(question, student_answer)
        clean_reasoning = (student_reasoning or "").strip()
        reasoning_lower = clean_reasoning.lower()

        # ----------------------------------------------------------------------
        # CASE 1: Answer is CORRECT
        # ----------------------------------------------------------------------
        if is_correct:
            # Check if this was a retry attempting to repair a previously detected misconception
            if parent_attempt and (
                parent_attempt.get("detected_misconception_id") is not None
                or parent_attempt.get("is_correct") is False
            ):
                # Verify that reasoning demonstrates understanding or at least doesn't repeat the misconception
                cross_term_indicators = [
                    "cross term",
                    "middle term",
                    "2ab",
                    "6x",
                    "4x",
                    "2 * 3",
                    "2*3",
                    "2 * 2",
                    "2*2",
                    "foil",
                    "area model",
                    "twice the product",
                    "both terms",
                    "multiply",
                ]
                shows_cross_term = any(ind in reasoning_lower for ind in cross_term_indicators)
                does_not_repeat_error = "square each term separately" not in reasoning_lower

                if shows_cross_term or does_not_repeat_error:
                    return DiagnosticEvaluation(
                        is_correct=True,
                        diagnostic_status="repaired",
                        detected_misconception=False,
                        is_repaired=True,
                        confidence=1.0,
                        analysis_reasoning=(
                            "Student successfully corrected the algebraic expansion and demonstrated "
                            "repair of the previous misconception regarding the cross term."
                        ),
                        next_action="proceed",
                    )

            return DiagnosticEvaluation(
                is_correct=True,
                diagnostic_status="correct",
                detected_misconception=False,
                is_repaired=False,
                confidence=1.0,
                analysis_reasoning="Student provided the mathematically correct expansion.",
                next_action="proceed",
            )

        # ----------------------------------------------------------------------
        # CASE 2: Answer is INCORRECT — Evaluate Evidence & Reasoning
        # ----------------------------------------------------------------------

        # Rule 6: Reasoning MUST matter. If reasoning is empty, conservative insufficient evidence.
        if not clean_reasoning or len(clean_reasoning) < 3:
            return DiagnosticEvaluation(
                is_correct=False,
                diagnostic_status="insufficient_evidence",
                detected_misconception=False,
                confidence=0.5,
                analysis_reasoning=(
                    "Student submitted an incorrect answer without explanatory reasoning. "
                    "Evidence is insufficient to definitively diagnose an underlying cognitive misconception."
                ),
                next_action="retry",
            )

        # Non-informative guessing
        guessing_phrases = [
            "i don't know",
            "idk",
            "just guessing",
            "just a guess",
            "random guess",
            "not sure",
            "guessing",
            "i guessed",
        ]
        if any(gp in reasoning_lower for gp in guessing_phrases) and len(reasoning_lower.split()) <= 4:
            return DiagnosticEvaluation(
                is_correct=False,
                diagnostic_status="insufficient_evidence",
                detected_misconception=False,
                confidence=0.4,
                analysis_reasoning="Student reasoning indicates guessing rather than a systematic conceptual error.",
                next_action="retry",
            )

        # Check for known misconception signatures
        norm_ans = self._normalize_expr(student_answer)

        # Keywords indicating treating square of sum as sum of squares
        sum_of_squares_keywords = [
            "square both",
            "square each",
            "squared both",
            "squared each",
            "individually",
            "separately",
            "sum of squares",
            "square of sum",
            "square of a sum",
            "distribute the square",
            "distribute the power",
            "distribute power",
            "distribute square",
            "a^2 + b^2",
            "a^2+b^2",
            "x^2 and 9",
            "x^2 and 4",
            "square the first and second",
            "square the x and square the",
        ]

        # Keywords explicitly highlighting missing cross term
        missing_cross_keywords = [
            "missing cross",
            "missing the cross",
            "no cross term",
            "forgot the cross",
            "forgot cross",
            "no middle term",
            "forgot 2ab",
            "missing 2ab",
            "there is no 2ab",
            "there is no middle",
            "there is no cross",
        ]

        has_sum_of_squares_reasoning = any(k in reasoning_lower for k in sum_of_squares_keywords)
        has_missing_cross_reasoning = any(k in reasoning_lower for k in missing_cross_keywords)

        # MCQ check from rubric
        rubric = question.get("rubric") or {}
        mcq_associated_misc = None
        if isinstance(rubric, dict):
            choices = rubric.get("choices") or rubric.get("options") or []
            for choice in choices:
                if isinstance(choice, dict):
                    label = self._normalize_expr(str(choice.get("label", "")))
                    text = self._normalize_expr(str(choice.get("text", "")))
                    if norm_ans in (label, text) and choice.get("associated_misconception"):
                        mcq_associated_misc = choice.get("associated_misconception")

        detected_misc_name: Optional[str] = None

        # 1. Missing Cross Term pattern (e.g. x^2 + 9 or explicit mention)
        if has_missing_cross_reasoning:
            detected_misc_name = self.MISC_MISSING_CROSS_TERM
        # 2. Treating square of sum as sum of squares (e.g. "I square each term separately")
        elif has_sum_of_squares_reasoning:
            # If MCQ specifically names it, use that, otherwise default to sum of squares
            detected_misc_name = self.MISC_SUM_OF_SQUARES
        elif mcq_associated_misc:
            # For MCQ with reasoning provided, connect to the rubric's associated misconception
            detected_misc_name = mcq_associated_misc

        if detected_misc_name:
            return DiagnosticEvaluation(
                is_correct=False,
                diagnostic_status="misconception_detected",
                detected_misconception=True,
                misconception_name=detected_misc_name,
                confidence=0.95,
                analysis_reasoning=(
                    f"Student answer and reasoning clearly exhibit the misconception: '{detected_misc_name}'. "
                    f"Student applied an incorrect rule: '{clean_reasoning}'."
                ),
                next_action="review_intervention",
            )

        # Answer is incorrect, but does not match any recognized misconception pattern
        return DiagnosticEvaluation(
            is_correct=False,
            diagnostic_status="insufficient_evidence",
            detected_misconception=False,
            confidence=0.5,
            analysis_reasoning=(
                "Student submitted an incorrect response, but the answer and reasoning do not match "
                "any cataloged misconception for this concept."
            ),
            next_action="retry",
        )
