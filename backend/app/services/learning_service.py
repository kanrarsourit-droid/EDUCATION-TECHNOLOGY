"""Service layer for student learning workflows: question retrieval and attempt tracking."""

import logging
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from postgrest.exceptions import APIError
from app.core.supabase import get_supabase_client

logger = logging.getLogger(__name__)


class QuestionNotFoundError(Exception):
    """Raised when a specified question cannot be found."""
    pass


class ConceptNotFoundError(Exception):
    """Raised when a specified concept cannot be found."""
    pass


class ParentAttemptNotFoundError(Exception):
    """Raised when a specified parent attempt does not exist."""
    pass


class InvalidRetryAttemptError(Exception):
    """Raised when a retry attempt does not match the parent's student or question."""
    pass


def sanitize_safe_question(question: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize a question dictionary for safe delivery to a student.
    Strips expected answers and grading hints while preserving MCQ choices.

    Args:
        question: Raw database question record.

    Returns:
        Dict[str, Any]: Safe question representation without sensitive answer keys.
    """
    safe_data: Dict[str, Any] = {
        "id": question["id"],
        "concept_id": question["concept_id"],
        "title": question["title"],
        "prompt": question["prompt"],
        "question_type": question["question_type"],
        "difficulty": question.get("difficulty", "intermediate"),
        "created_at": question["created_at"],
        "rubric": None,
    }

    raw_rubric = question.get("rubric")
    if question.get("question_type") == "multiple_choice" and isinstance(raw_rubric, dict):
        raw_choices = raw_rubric.get("choices") or raw_rubric.get("options") or []
        safe_choices = []
        for choice in raw_choices:
            if isinstance(choice, dict):
                safe_choice = {
                    "label": choice.get("label"),
                    "text": choice.get("text"),
                }
                safe_choices.append(safe_choice)
        if safe_choices:
            safe_data["rubric"] = {"choices": safe_choices}

    return safe_data


def get_safe_questions_by_concept(concept_id: Union[UUID, str]) -> List[Dict[str, Any]]:
    """
    Retrieve all questions for a concept in student-safe format.

    Args:
        concept_id: UUID or string of the concept.

    Returns:
        List[Dict[str, Any]]: List of sanitized question records.
    """
    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("questions")
            .select("*")
            .eq("concept_id", str(concept_id))
            .order("created_at", desc=False)
            .execute()
        )
        questions = response.data or []
        return [sanitize_safe_question(q) for q in questions]
    except APIError as exc:
        logger.error("Supabase API error while fetching questions for concept %s: %s", concept_id, exc)
        raise
    except RuntimeError as exc:
        logger.error("Supabase configuration error: %s", exc)
        raise
    except Exception as exc:
        logger.error("Unexpected error while fetching questions for concept %s: %s", concept_id, exc)
        raise


def get_question_by_id(question_id: Union[UUID, str]) -> Optional[Dict[str, Any]]:
    """
    Retrieve a question by ID including internal fields for server-side evaluation.

    Args:
        question_id: UUID or string of the question.

    Returns:
        Optional[Dict[str, Any]]: Question record if found, else None.
    """
    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("questions")
            .select("*")
            .eq("id", str(question_id))
            .limit(1)
            .execute()
        )
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except APIError as exc:
        logger.error("Supabase API error fetching question %s: %s", question_id, exc)
        raise
    except RuntimeError as exc:
        logger.error("Supabase configuration error: %s", exc)
        raise
    except Exception as exc:
        logger.error("Unexpected error fetching question %s: %s", question_id, exc)
        raise


def get_attempt_by_id(attempt_id: Union[UUID, str]) -> Optional[Dict[str, Any]]:
    """
    Retrieve an attempt by its ID.

    Args:
        attempt_id: UUID or string of the attempt.

    Returns:
        Optional[Dict[str, Any]]: Attempt record if found, else None.
    """
    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("student_attempts")
            .select("*")
            .eq("id", str(attempt_id))
            .limit(1)
            .execute()
        )
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except APIError as exc:
        logger.error("Supabase API error fetching attempt %s: %s", attempt_id, exc)
        raise
    except RuntimeError as exc:
        logger.error("Supabase configuration error: %s", exc)
        raise
    except Exception as exc:
        logger.error("Unexpected error fetching attempt %s: %s", attempt_id, exc)
        raise


def evaluate_deterministic_correctness(question: Dict[str, Any], student_answer: str) -> Optional[bool]:
    """
    Deterministically evaluates correctness for supported question types.
    Multiple-choice evaluates against rubric choices and expected_answer.
    Open-response and code return None (deferred to AI/manual grading).

    Args:
        question: Full database question record.
        student_answer: Submitted answer from student.

    Returns:
        Optional[bool]: True/False for multiple-choice; None for open-response/code.
    """
    q_type = question.get("question_type")

    if q_type == "multiple_choice":
        clean_answer = student_answer.strip().lower()
        expected = question.get("expected_answer", "").strip().lower()

        # Check direct text match with expected_answer
        if expected and clean_answer == expected:
            return True

        # Check rubric choices
        rubric = question.get("rubric") or {}
        if isinstance(rubric, dict):
            choices = rubric.get("choices") or rubric.get("options") or []
            for choice in choices:
                if isinstance(choice, dict):
                    label = str(choice.get("label", "")).strip().lower()
                    text = str(choice.get("text", "")).strip().lower()
                    is_correct = bool(choice.get("is_correct", False))

                    if clean_answer in (label, text):
                        return is_correct

        return False

    # Open-response and code questions leave is_correct as NULL for Stage 14
    return None


def create_student_attempt(
    student_id: Union[UUID, str],
    question_id: Union[UUID, str],
    student_answer: str,
    student_reasoning: Optional[str] = None,
    confidence_score: Optional[float] = None,
    parent_attempt_id: Optional[Union[UUID, str]] = None,
) -> Dict[str, Any]:
    """
    Creates and records a student attempt on a question with safe deterministic evaluation.

    Args:
        student_id: UUID of the authenticated student profile.
        question_id: UUID of the question being attempted.
        student_answer: Non-empty answer text.
        student_reasoning: Optional reasoning behind the answer.
        confidence_score: Optional confidence rating [0.0, 1.0].
        parent_attempt_id: Optional parent attempt for retry chains.

    Returns:
        Dict[str, Any]: The newly created attempt record.

    Raises:
        QuestionNotFoundError: If the question does not exist.
        ParentAttemptNotFoundError: If the specified parent attempt does not exist.
        InvalidRetryAttemptError: If parent attempt does not match student or question.
    """
    supabase = get_supabase_client()

    # 1. Verify question exists
    question = get_question_by_id(question_id)
    if not question:
        raise QuestionNotFoundError(f"Question with ID '{question_id}' does not exist.")

    # 2. Check retry chain if parent_attempt_id provided
    attempt_number = 1
    if parent_attempt_id:
        parent = get_attempt_by_id(parent_attempt_id)
        if not parent:
            raise ParentAttemptNotFoundError(f"Parent attempt '{parent_attempt_id}' not found.")

        # Ensure parent attempt belongs to this student
        if str(parent["student_id"]) != str(student_id):
            raise InvalidRetryAttemptError("Parent attempt belongs to a different student.")

        # Ensure parent attempt references the same question
        if str(parent["question_id"]) != str(question["id"]):
            raise InvalidRetryAttemptError("Parent attempt references a different question.")

        attempt_number = int(parent.get("attempt_number", 1)) + 1

    # 3. Evaluate deterministic correctness
    is_correct = evaluate_deterministic_correctness(question, student_answer)

    # 4. Prepare insert payload
    record = {
        "student_id": str(student_id),
        "question_id": str(question_id),
        "parent_attempt_id": str(parent_attempt_id) if parent_attempt_id else None,
        "attempt_number": attempt_number,
        "student_answer": student_answer.strip(),
        "student_reasoning": (student_reasoning or "").strip(),
        "is_correct": is_correct,
        "detected_misconception_id": None,
        "analysis_reasoning": None,
        "confidence_score": confidence_score,
    }

    try:
        response = supabase.table("student_attempts").insert(record).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        raise RuntimeError("Failed to insert student attempt record.")
    except APIError as exc:
        logger.error("Supabase API error inserting attempt: %s", exc)
        raise
    except RuntimeError as exc:
        logger.error("Configuration error inserting attempt: %s", exc)
        raise
    except Exception as exc:
        logger.error("Unexpected error inserting student attempt: %s", exc)
        raise


def get_student_attempts(
    student_id: Union[UUID, str],
    question_id: Optional[Union[UUID, str]] = None,
    concept_id: Optional[Union[UUID, str]] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Retrieve attempts belonging exclusively to the authenticated student.

    Args:
        student_id: Authenticated student UUID.
        question_id: Optional question filter.
        concept_id: Optional concept filter.
        limit: Max attempts to return.

    Returns:
        List[Dict[str, Any]]: List of attempts belonging to the student.
    """
    try:
        supabase = get_supabase_client()

        # If concept_id provided, resolve question IDs first
        if concept_id:
            q_res = (
                supabase.table("questions")
                .select("id")
                .eq("concept_id", str(concept_id))
                .execute()
            )
            q_ids = [q["id"] for q in (q_res.data or [])]
            if not q_ids:
                return []

        query = (
            supabase.table("student_attempts")
            .select("*")
            .eq("student_id", str(student_id))
        )

        if concept_id:
            query = query.in_("question_id", q_ids)

        if question_id:
            query = query.eq("question_id", str(question_id))

        query = query.order("created_at", desc=True).limit(limit)
        response = query.execute()
        return response.data or []
    except APIError as exc:
        logger.error("Supabase API error fetching student attempts: %s", exc)
        raise
    except RuntimeError as exc:
        logger.error("Configuration error fetching student attempts: %s", exc)
        raise
    except Exception as exc:
        logger.error("Unexpected error fetching student attempts: %s", exc)
        raise
