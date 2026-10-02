"""
Diagnostic Service Layer for Learning Debugger.

Implements the deterministic diagnostic pipeline:
1. Validates authenticated student ownership of attempt.
2. Evaluates student answer & reasoning via subject-specific diagnostic adapter.
3. Detects underlying misconceptions and queries targeted interventions.
4. Manages longitudinal student misconception states (active, recurring, repaired).
5. Records intervention delivery in student_interventions.
6. Evaluates retry repair status and marks interventions completed.
7. Computes bounded concept mastery and updates student_concept_mastery.
8. Returns safe DiagnosticResponse without leaking expected answers or rubrics.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID
from postgrest.exceptions import APIError

from app.core.supabase import get_supabase_client
from app.schemas.diagnostic import DiagnosticResponse
from app.services.diagnostics import get_diagnostic_adapter
from app.services.diagnostics.base import DiagnosticEvaluation
from app.services.learning_service import get_attempt_by_id, get_question_by_id

logger = logging.getLogger(__name__)


class AttemptNotFoundError(Exception):
    """Raised when an attempt does not exist."""
    pass


class AttemptOwnershipError(Exception):
    """Raised when a student tries to diagnose an attempt belonging to another student."""
    pass


class QuestionNotFoundError(Exception):
    """Raised when the question associated with an attempt cannot be found."""
    pass


class ConceptNotFoundError(Exception):
    """Raised when the concept associated with a question cannot be found."""
    pass


def calculate_concept_mastery(
    total_attempts: int,
    successful_attempts: int,
    active_misconceptions_count: int,
    repaired_misconceptions_count: int,
    recurring_count: int = 0,
) -> Tuple[float, str]:
    """
    Calculates deterministic, bounded concept mastery score and status.

    Formula:
    --------
    1. If total_attempts == 0:
       score = 0.0, status = 'unstarted'

    2. Base accuracy component (max 0.60):
       accuracy = successful_attempts / total_attempts
       base_score = accuracy * 0.60

    3. Success bonus (max 0.20):
       If successful_attempts >= 1:
           success_bonus = min(0.20, (successful_attempts / total_attempts) * 0.20)
       Else:
           success_bonus = 0.0

    4. Repair bonus (max 0.20):
       repair_bonus = min(0.20, repaired_misconceptions_count * 0.10)

    5. Misconception penalty:
       unresolved = active_misconceptions_count
       penalty = min(0.35, (unresolved * 0.15) + (recurring_count * 0.10))

    6. Score clamping:
       raw = base_score + success_bonus + repair_bonus - penalty
       mastery_score = max(0.0, min(1.0, round(raw, 3)))

    7. Status classification:
       - If recurring_count >= 1 or (unresolved >= 2 and mastery_score < 0.70):
           status = 'needs_review'
       - Else if mastery_score >= 0.80 and successful_attempts >= 1 and unresolved == 0:
           status = 'mastered'
       - Else if mastery_score > 0.0 or total_attempts > 0:
           status = 'in_progress'
       - Else:
           status = 'unstarted'

    Returns:
        Tuple[float, str]: (mastery_score, mastery_status)
    """
    if total_attempts <= 0:
        return 0.0, "unstarted"

    accuracy = successful_attempts / total_attempts
    base_score = accuracy * 0.60

    success_bonus = min(0.20, (successful_attempts / total_attempts) * 0.20) if successful_attempts > 0 else 0.0
    repair_bonus = min(0.20, repaired_misconceptions_count * 0.10)
    penalty = min(0.35, (active_misconceptions_count * 0.15) + (recurring_count * 0.10))

    raw_score = base_score + success_bonus + repair_bonus - penalty
    mastery_score = max(0.0, min(1.0, round(raw_score, 3)))

    if recurring_count >= 1 or (active_misconceptions_count >= 2 and mastery_score < 0.70):
        mastery_status = "needs_review"
    elif mastery_score >= 0.80 and successful_attempts >= 1 and active_misconceptions_count == 0:
        mastery_status = "mastered"
    elif mastery_score > 0.0 or total_attempts > 0:
        mastery_status = "in_progress"
    else:
        mastery_status = "unstarted"

    return mastery_score, mastery_status


def detect_misconception(
    question: Dict[str, Any],
    student_answer: str,
    student_reasoning: Optional[str] = None,
    parent_attempt: Optional[Dict[str, Any]] = None,
    subject_slug: str = "mathematics",
) -> DiagnosticEvaluation:
    """
    Dispatches to the modular subject diagnostic adapter to evaluate answer and reasoning.
    """
    adapter = get_diagnostic_adapter(subject_slug)
    return adapter.evaluate(
        question=question,
        student_answer=student_answer,
        student_reasoning=student_reasoning,
        parent_attempt=parent_attempt,
    )


def select_intervention(
    misconception_id: Union[UUID, str],
) -> Optional[Dict[str, Any]]:
    """
    Queries Supabase to retrieve the targeted educational intervention for a misconception.
    """
    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("interventions")
            .select("*")
            .eq("misconception_id", str(misconception_id))
            .limit(1)
            .execute()
        )
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as exc:
        logger.error("Failed to select intervention for misconception %s: %s", misconception_id, exc)
        return None


def get_misconception_by_name(
    concept_id: Union[UUID, str],
    name: str,
) -> Optional[Dict[str, Any]]:
    """
    Look up a cataloged misconception record by concept and name/pattern.
    """
    try:
        supabase = get_supabase_client()
        # Direct name match
        response = (
            supabase.table("misconceptions")
            .select("*")
            .eq("concept_id", str(concept_id))
            .ilike("name", f"%{name}%")
            .limit(1)
            .execute()
        )
        if response.data and len(response.data) > 0:
            return response.data[0]

        # Fallback to any misconception under this concept if specific name failed
        fallback_resp = (
            supabase.table("misconceptions")
            .select("*")
            .eq("concept_id", str(concept_id))
            .limit(1)
            .execute()
        )
        if fallback_resp.data and len(fallback_resp.data) > 0:
            return fallback_resp.data[0]
        return None
    except Exception as exc:
        logger.error("Failed to get misconception for concept %s: %s", concept_id, exc)
        return None


def update_student_learning_state(
    student_id: Union[UUID, str],
    attempt_id: Union[UUID, str],
    concept_id: Union[UUID, str],
    eval_result: DiagnosticEvaluation,
    misconception: Optional[Dict[str, Any]] = None,
    intervention: Optional[Dict[str, Any]] = None,
    parent_attempt: Optional[Dict[str, Any]] = None,
) -> Tuple[float, str]:
    """
    Persists student misconception state, intervention records, attempt evaluations,
    and recalculates concept mastery in Supabase.
    """
    supabase = get_supabase_client()
    now_iso = datetime.now(timezone.utc).isoformat()
    sid_str = str(student_id)
    cid_str = str(concept_id)
    att_str = str(attempt_id)

    # 1. Handle Misconception Detection
    if eval_result.detected_misconception and misconception:
        misc_id = str(misconception["id"])
        
        # Check existing student_misconceptions record
        existing_res = (
            supabase.table("student_misconceptions")
            .select("*")
            .eq("student_id", sid_str)
            .eq("misconception_id", misc_id)
            .limit(1)
            .execute()
        )
        existing_records = existing_res.data or []

        if not existing_records:
            # First occurrence
            supabase.table("student_misconceptions").insert({
                "student_id": sid_str,
                "misconception_id": misc_id,
                "occurrence_count": 1,
                "status": "under_intervention",
                "first_detected_at": now_iso,
                "last_detected_at": now_iso,
            }).execute()
        else:
            # Recurring occurrence
            rec = existing_records[0]
            new_count = int(rec.get("occurrence_count", 1)) + 1
            supabase.table("student_misconceptions").update({
                "occurrence_count": new_count,
                "status": "recurring",
                "last_detected_at": now_iso,
                "repaired_at": None,
            }).eq("id", rec["id"]).execute()

        # Insert student_interventions record if intervention available
        if intervention:
            supabase.table("student_interventions").insert({
                "student_id": sid_str,
                "attempt_id": att_str,
                "misconception_id": misc_id,
                "intervention_id": str(intervention["id"]),
                "delivered_content": intervention.get("content", ""),
                "status": "presented",
                "is_repaired": False,
            }).execute()

        # Update current student_attempts record with detected misconception
        supabase.table("student_attempts").update({
            "is_correct": False,
            "detected_misconception_id": misc_id,
            "analysis_reasoning": eval_result.analysis_reasoning,
        }).eq("id", att_str).execute()

    # 2. Handle Repair Flow (Successful Retry)
    elif eval_result.is_repaired and parent_attempt:
        parent_misc_id = parent_attempt.get("detected_misconception_id")
        
        # If parent attempt didn't explicitly store detected_misconception_id, look in interventions
        if not parent_misc_id:
            parent_int_res = (
                supabase.table("student_interventions")
                .select("misconception_id")
                .eq("attempt_id", str(parent_attempt["id"]))
                .limit(1)
                .execute()
            )
            if parent_int_res.data and len(parent_int_res.data) > 0:
                parent_misc_id = parent_int_res.data[0]["misconception_id"]

        if parent_misc_id:
            # Mark misconception as repaired
            supabase.table("student_misconceptions").update({
                "status": "repaired",
                "repaired_at": now_iso,
            }).eq("student_id", sid_str).eq("misconception_id", str(parent_misc_id)).execute()

            # Mark student_interventions completed
            supabase.table("student_interventions").update({
                "status": "completed",
                "is_repaired": True,
                "completed_at": now_iso,
            }).eq("student_id", sid_str).eq("attempt_id", str(parent_attempt["id"])).execute()

        # Update current student_attempts record
        supabase.table("student_attempts").update({
            "is_correct": True,
            "detected_misconception_id": None,
            "analysis_reasoning": eval_result.analysis_reasoning,
        }).eq("id", att_str).execute()

    # 3. Handle Correct / Insufficient Evidence / Other evaluations
    else:
        supabase.table("student_attempts").update({
            "is_correct": eval_result.is_correct,
            "detected_misconception_id": None,
            "analysis_reasoning": eval_result.analysis_reasoning,
        }).eq("id", att_str).execute()

    # 4. Calculate Concept Mastery
    # Fetch questions under concept
    q_res = supabase.table("questions").select("id").eq("concept_id", cid_str).execute()
    q_ids = [q["id"] for q in (q_res.data or [])]

    # Fetch all attempts for student on these questions
    if q_ids:
        att_res = (
            supabase.table("student_attempts")
            .select("id, is_correct")
            .eq("student_id", sid_str)
            .in_("question_id", q_ids)
            .execute()
        )
        student_atts = att_res.data or []
    else:
        student_atts = []

    total_attempts = len(student_atts)
    successful_attempts = len([a for a in student_atts if a.get("is_correct") is True])

    # Fetch misconceptions under concept
    m_res = supabase.table("misconceptions").select("id").eq("concept_id", cid_str).execute()
    m_ids = [m["id"] for m in (m_res.data or [])]

    if m_ids:
        sm_res = (
            supabase.table("student_misconceptions")
            .select("*")
            .eq("student_id", sid_str)
            .in_("misconception_id", m_ids)
            .execute()
        )
        student_miscs = sm_res.data or []
    else:
        student_miscs = []

    active_count = len([m for m in student_miscs if m.get("status") in ("active", "under_intervention", "recurring")])
    repaired_count = len([m for m in student_miscs if m.get("status") == "repaired"])
    recurring_count = len([m for m in student_miscs if m.get("status") == "recurring" or int(m.get("occurrence_count", 1)) > 1])

    mastery_score, mastery_status = calculate_concept_mastery(
        total_attempts=total_attempts,
        successful_attempts=successful_attempts,
        active_misconceptions_count=active_count,
        repaired_misconceptions_count=repaired_count,
        recurring_count=recurring_count,
    )

    # Upsert student_concept_mastery
    existing_mastery_res = (
        supabase.table("student_concept_mastery")
        .select("id")
        .eq("student_id", sid_str)
        .eq("concept_id", cid_str)
        .limit(1)
        .execute()
    )
    existing_mastery = existing_mastery_res.data or []

    if existing_mastery:
        supabase.table("student_concept_mastery").update({
            "mastery_score": mastery_score,
            "status": mastery_status,
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "last_attempt_at": now_iso,
            "updated_at": now_iso,
        }).eq("id", existing_mastery[0]["id"]).execute()
    else:
        supabase.table("student_concept_mastery").insert({
            "student_id": sid_str,
            "concept_id": cid_str,
            "mastery_score": mastery_score,
            "status": mastery_status,
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "last_attempt_at": now_iso,
        }).execute()

    return mastery_score, mastery_status


def analyze_attempt(
    student_id: Union[UUID, str],
    attempt_id: Union[UUID, str],
) -> DiagnosticResponse:
    """
    Executes the full diagnostic workflow for a student's attempt.

    Args:
        student_id: Authenticated student profile UUID.
        attempt_id: UUID of the attempt to diagnose.

    Returns:
        DiagnosticResponse: Evaluated diagnostic response including misconception & intervention.

    Raises:
        AttemptNotFoundError: If attempt does not exist.
        AttemptOwnershipError: If attempt belongs to a different student.
        QuestionNotFoundError: If question record is missing.
    """
    # 1. Fetch attempt
    attempt = get_attempt_by_id(attempt_id)
    if not attempt:
        raise AttemptNotFoundError(f"Attempt with ID '{attempt_id}' not found.")

    # 2. Strict ownership verification
    if str(attempt["student_id"]) != str(student_id):
        raise AttemptOwnershipError("Attempt belongs to another student.")

    # 3. Fetch question
    question = get_question_by_id(attempt["question_id"])
    if not question:
        raise QuestionNotFoundError(f"Question with ID '{attempt['question_id']}' not found.")

    concept_id = question["concept_id"]

    # 4. Fetch parent attempt if retry
    parent_attempt = None
    if attempt.get("parent_attempt_id"):
        parent_attempt = get_attempt_by_id(attempt["parent_attempt_id"])
        if parent_attempt and str(parent_attempt["student_id"]) != str(student_id):
            raise AttemptOwnershipError("Parent attempt belongs to another student.")

    # 5. Run diagnostic adapter
    eval_result = detect_misconception(
        question=question,
        student_answer=attempt["student_answer"],
        student_reasoning=attempt.get("student_reasoning"),
        parent_attempt=parent_attempt,
        subject_slug="mathematics",
    )

    # 6. Resolve Misconception and Intervention records if detected
    misconception_rec = None
    intervention_rec = None

    if eval_result.detected_misconception and eval_result.misconception_name:
        misconception_rec = get_misconception_by_name(concept_id, eval_result.misconception_name)
        if misconception_rec:
            intervention_rec = select_intervention(misconception_rec["id"])

    # 7. Update student state & mastery
    mastery_score, mastery_status = update_student_learning_state(
        student_id=student_id,
        attempt_id=attempt_id,
        concept_id=concept_id,
        eval_result=eval_result,
        misconception=misconception_rec,
        intervention=intervention_rec,
        parent_attempt=parent_attempt,
    )

    # 8. Construct student-safe DiagnosticResponse
    return DiagnosticResponse(
        attempt_id=UUID(str(attempt_id)),
        is_correct=eval_result.is_correct,
        diagnostic_status=eval_result.diagnostic_status,
        detected_misconception=eval_result.detected_misconception,
        misconception_id=UUID(str(misconception_rec["id"])) if misconception_rec else None,
        misconception_name=misconception_rec["name"] if misconception_rec else None,
        misconception_description=misconception_rec["description"] if misconception_rec else None,
        severity=misconception_rec.get("severity") if misconception_rec else None,
        intervention=True if intervention_rec else False,
        intervention_id=UUID(str(intervention_rec["id"])) if intervention_rec else None,
        intervention_type=intervention_rec.get("intervention_type") if intervention_rec else None,
        intervention_content=intervention_rec.get("content") if intervention_rec else None,
        mastery_score=mastery_score,
        mastery_status=mastery_status,
        next_action=eval_result.next_action,
    )
