"""Service layer for Supabase Authentication and student profile resolution."""

import logging
from typing import Any, Dict, Optional, Union
from uuid import UUID
from postgrest.exceptions import APIError
from supabase_auth.errors import AuthApiError
from app.core.supabase import get_supabase_client

logger = logging.getLogger(__name__)


def get_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validates a Supabase access token and retrieves the authenticated user's profile.

    Args:
        token: Raw JWT access token string (Bearer token).

    Returns:
        Optional[Dict[str, Any]]: User identity dictionary containing id, email,
        user_metadata, and created_at if valid; None if invalid or expired.
    """
    if not token or not token.strip():
        return None

    try:
        supabase = get_supabase_client()
        response = supabase.auth.get_user(token.strip())
        if not response or not response.user:
            return None

        user = response.user
        return {
            "id": user.id,
            "email": user.email,
            "user_metadata": user.user_metadata or {},
            "created_at": getattr(user, "created_at", None),
        }
    except AuthApiError as exc:
        # Log message safely without exposing the token
        logger.warning("Supabase Auth token validation failed: %s", getattr(exc, "message", type(exc).__name__))
        return None
    except Exception as exc:
        logger.error("Unexpected error validating token: %s", type(exc).__name__)
        return None


def get_student_by_auth_user_id(auth_user_id: Union[UUID, str]) -> Optional[Dict[str, Any]]:
    """
    Look up a student profile associated with a Supabase Auth user ID.

    Args:
        auth_user_id: Supabase Auth user UUID.

    Returns:
        Optional[Dict[str, Any]]: Student profile record if found, else None.
    """
    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("students")
            .select("*")
            .eq("auth_user_id", str(auth_user_id))
            .limit(1)
            .execute()
        )
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except APIError as exc:
        logger.warning("Database query error looking up student by auth_user_id: %s", getattr(exc, "message", type(exc).__name__))
        return None
    except Exception as exc:
        logger.error("Unexpected error looking up student by auth_user_id: %s", type(exc).__name__)
        return None


def provision_or_link_student_profile(
    auth_user_id: Union[UUID, str],
    email: Optional[str],
    full_name: Optional[str] = None,
    user_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Provisions or links a student profile for an authenticated Supabase user.

    Resolution Strategy:
    1. If a student is already linked to auth_user_id, returns it (updating full_name if provided).
    2. If not linked by auth_user_id, searches by verified email. If exactly one matching student exists:
       - Links auth_user_id to that student and returns it.
    3. If no matching student exists, inserts a new student record using auth_user_id, verified email,
       and safe user metadata/name.
    4. Safely handles unique constraint collisions and race conditions by re-fetching.

    Args:
        auth_user_id: Supabase Auth user ID (from validated JWT).
        email: Verified email from Supabase Auth user.
        full_name: Optional custom full_name provided in request body.
        user_metadata: Optional user_metadata dictionary from Supabase Auth token.

    Returns:
        Dict[str, Any]: The linked or created student record.

    Raises:
        ValueError: If email is missing or empty.
        RuntimeError: If student with email is already linked to another account.
        APIError: For database query failures.
    """
    if not email or not email.strip():
        raise ValueError("Authenticated account does not have a valid email address.")

    email_clean = email.strip().lower()
    auth_uid_str = str(auth_user_id)
    supabase = get_supabase_client()

    # 1. Search students by auth_user_id
    existing_by_auth = get_student_by_auth_user_id(auth_uid_str)
    if existing_by_auth:
        if full_name and full_name.strip():
            cleaned_name = full_name.strip()
            if existing_by_auth.get("full_name") != cleaned_name:
                try:
                    update_res = (
                        supabase.table("students")
                        .update({"full_name": cleaned_name})
                        .eq("id", existing_by_auth["id"])
                        .execute()
                    )
                    if update_res.data and len(update_res.data) > 0:
                        return update_res.data[0]
                except Exception as exc:
                    logger.warning("Could not update full_name for existing student: %s", exc)
        return existing_by_auth

    # 2. Search students by email
    try:
        res_by_email = (
            supabase.table("students")
            .select("*")
            .ilike("email", email_clean)
            .execute()
        )
        students_with_email = res_by_email.data or []
    except Exception as exc:
        logger.error("Error querying students by email: %s", exc)
        raise

    if len(students_with_email) == 1:
        matched = students_with_email[0]
        matched_auth_id = matched.get("auth_user_id")

        if matched_auth_id and str(matched_auth_id) != auth_uid_str:
            raise RuntimeError("A student profile with this email is already linked to a different account.")

        update_fields = {"auth_user_id": auth_uid_str}
        if full_name and full_name.strip() and matched.get("full_name") != full_name.strip():
            update_fields["full_name"] = full_name.strip()

        try:
            update_res = (
                supabase.table("students")
                .update(update_fields)
                .eq("id", matched["id"])
                .execute()
            )
            if update_res.data and len(update_res.data) > 0:
                return update_res.data[0]
            return matched
        except APIError as exc:
            err_text = str(exc).lower()
            if "unique" in err_text or "uq_students_auth_user_id" in err_text:
                refetched = get_student_by_auth_user_id(auth_uid_str)
                if refetched:
                    return refetched
            raise

    # 3. Create new student profile
    name_to_use = None
    if full_name and full_name.strip():
        name_to_use = full_name.strip()
    elif user_metadata:
        name_to_use = user_metadata.get("full_name") or user_metadata.get("name")
    if not name_to_use or not name_to_use.strip():
        name_to_use = email_clean.split("@")[0].capitalize()

    safe_metadata = {}
    if user_metadata:
        for k in ["avatar_url", "picture", "locale", "name", "full_name"]:
            if k in user_metadata and user_metadata[k]:
                safe_metadata[k] = user_metadata[k]

    new_record = {
        "auth_user_id": auth_uid_str,
        "email": email_clean,
        "full_name": name_to_use,
        "metadata": safe_metadata,
    }

    try:
        insert_res = supabase.table("students").insert(new_record).execute()
        if insert_res.data and len(insert_res.data) > 0:
            return insert_res.data[0]

        refetched = get_student_by_auth_user_id(auth_uid_str)
        if refetched:
            return refetched
        raise RuntimeError("Student profile creation did not return a record.")
    except APIError as exc:
        err_text = str(exc).lower()
        if "unique" in err_text or "uq_students_auth_user_id" in err_text or "23505" in err_text:
            logger.info("Unique constraint hit during student creation, re-fetching...")
            refetched = get_student_by_auth_user_id(auth_uid_str)
            if refetched:
                return refetched
            # Try fetching by email if email uniqueness conflicted
            res_by_email = (
                supabase.table("students")
                .select("*")
                .ilike("email", email_clean)
                .execute()
            )
            if res_by_email.data and len(res_by_email.data) > 0:
                return res_by_email.data[0]
        raise
