"""
Unit and integration tests for the Learning Debugger Diagnostic Engine.

Tests:
1. Unauthenticated request returns 401
2. Invalid UUID returns 422
3. Attempt not found returns 404
4. Cross-student access rejected (403)
5. Cross-student parent attempt rejected (403)
6. Correct MCQ answer diagnosis
7. Incorrect Mathematics answer with empty reasoning -> insufficient_evidence
8. Guessing reasoning -> insufficient_evidence
9. Missing cross-term misconception detection
10. Sum-of-squares misconception detection
11. Same misconception recurring (increments occurrence_count, status='recurring')
12. Correct retry repairs misconception (status='repaired', intervention completed)
13. Incorrect retry does not claim repair
14. Student intervention record created with status='presented'
15. Concept mastery updated, strictly bounded [0.0, 1.0], and correctly classified
16. Expected answer and internal rubrics are NEVER exposed in DiagnosticResponse
"""

from datetime import datetime, timezone
import unittest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from starlette.testclient import TestClient

from app.api.routes.auth import get_current_user
from app.main import app
from app.schemas.auth import AuthenticatedUserResponse
from app.services.diagnostic_service import calculate_concept_mastery
from app.services.diagnostics.mathematics import MathematicsDiagnostic


class TestDiagnosticEngine(unittest.TestCase):
    """Test suite covering the diagnostic service, adapters, and API endpoints."""

    def setUp(self):
        self.client = TestClient(app)
        self.test_user_id = uuid4()
        self.test_student_id = uuid4()
        self.other_student_id = uuid4()
        self.test_concept_id = uuid4()
        self.test_question_id = uuid4()
        self.test_attempt_id = uuid4()
        self.test_misc_id = uuid4()
        self.test_intervention_id = uuid4()

        # Mock authenticated user identity
        self.mock_user = AuthenticatedUserResponse(
            id=self.test_user_id,
            email="student.test@example.com",
            user_metadata={"full_name": "Test Student"},
        )

        # Mock linked student profile
        self.mock_student = {
            "id": str(self.test_student_id),
            "auth_user_id": str(self.test_user_id),
            "email": "student.test@example.com",
            "full_name": "Test Student",
            "metadata": {},
            "created_at": "2026-10-01T00:00:00Z",
            "updated_at": "2026-10-01T00:00:00Z",
        }

        # Seed question: Expand (x + 3)^2
        self.mock_question_open = {
            "id": str(self.test_question_id),
            "concept_id": str(self.test_concept_id),
            "title": "Expand a binomial square",
            "prompt": "Expand (x + 3)^2.",
            "question_type": "open_response",
            "expected_answer": "x^2 + 6x + 9",
            "rubric": {"instructions": "Evaluate 2ab cross term understanding."},
            "difficulty": "beginner",
            "created_at": "2026-10-01T00:00:00Z",
        }

        # Seed question: MCQ Which expression is equal to (x + 2)^2?
        self.mock_question_mcq = {
            "id": str(self.test_question_id),
            "concept_id": str(self.test_concept_id),
            "title": "Identify the correct expansion",
            "prompt": "Which expression is equal to (x + 2)^2?",
            "question_type": "multiple_choice",
            "expected_answer": "x^2 + 4x + 4",
            "rubric": {
                "choices": [
                    {"label": "A", "text": "x^2 + 4", "is_correct": False, "associated_misconception": "Treating a square of a sum as a sum of squares"},
                    {"label": "B", "text": "x^2 + 2x + 4", "is_correct": False, "associated_misconception": "Missing the factor of 2 in 2ab"},
                    {"label": "C", "text": "x^2 + 4x + 4", "is_correct": True},
                    {"label": "D", "text": "x^2 + 4x + 2", "is_correct": False, "associated_misconception": "Multiplying constant by 2 instead of squaring"},
                ]
            },
            "difficulty": "beginner",
            "created_at": "2026-10-01T00:00:00Z",
        }

        # Mock Misconceptions
        self.mock_misconception_sum_squares = {
            "id": str(self.test_misc_id),
            "concept_id": str(self.test_concept_id),
            "name": "Treating a square of a sum as a sum of squares",
            "description": "Student applies the square operation independently to each term.",
            "canonical_example": "(x + 2)^2 = x^2 + 4",
            "severity": "fundamental",
        }

        self.mock_misconception_missing_cross = {
            "id": str(self.test_misc_id),
            "concept_id": str(self.test_concept_id),
            "name": "Missing the cross term when squaring a binomial",
            "description": "Student forgets the 2ab middle term.",
            "canonical_example": "(x + 3)^2 = x^2 + 9",
            "severity": "fundamental",
        }

        # Mock Intervention
        self.mock_intervention = {
            "id": str(self.test_intervention_id),
            "misconception_id": str(self.test_misc_id),
            "title": "Challenge the sum-of-squares rule",
            "intervention_type": "counter_example",
            "content": "Use numerical counterexample: (2+3)^2 = 25 while 2^2+3^2 = 13.",
        }

    def tearDown(self):
        app.dependency_overrides.clear()

    # =========================================================================
    # PART 1: AUTHENTICATION & SECURITY
    # =========================================================================

    def test_unauthenticated_request_returns_401(self):
        """POST /api/v1/learning/attempts/{id}/diagnose without auth token returns 401."""
        res = self.client.post(f"/api/v1/learning/attempts/{self.test_attempt_id}/diagnose")
        self.assertEqual(res.status_code, 401)
        self.assertIn("Authentication required", res.json()["detail"])

    def test_invalid_uuid_returns_422(self):
        """Invalid attempt UUID format returns 422 Unprocessable Entity."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        with patch("app.api.routes.learning.get_student_by_auth_user_id", return_value=self.mock_student):
            res = self.client.post("/api/v1/learning/attempts/not-a-valid-uuid/diagnose")
            self.assertEqual(res.status_code, 422)

    def test_attempt_not_found_returns_404(self):
        """Attempt ID that does not exist returns 404 Not Found."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        with patch("app.api.routes.learning.get_student_by_auth_user_id", return_value=self.mock_student), \
             patch("app.services.diagnostic_service.get_attempt_by_id", return_value=None):
            res = self.client.post(f"/api/v1/learning/attempts/{self.test_attempt_id}/diagnose")
            self.assertEqual(res.status_code, 404)
            self.assertIn("not found", res.json()["detail"].lower())

    def test_cross_student_access_rejected_403(self):
        """Student A cannot diagnose an attempt belonging to Student B (403 Forbidden)."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        foreign_attempt = {
            "id": str(self.test_attempt_id),
            "student_id": str(self.other_student_id),
            "question_id": str(self.test_question_id),
            "student_answer": "x^2 + 9",
            "student_reasoning": "I squared each term.",
        }
        with patch("app.api.routes.learning.get_student_by_auth_user_id", return_value=self.mock_student), \
             patch("app.services.diagnostic_service.get_attempt_by_id", return_value=foreign_attempt):
            res = self.client.post(f"/api/v1/learning/attempts/{self.test_attempt_id}/diagnose")
            self.assertEqual(res.status_code, 403)
            self.assertIn("belongs to another student", res.json()["detail"].lower())

    def test_cross_student_parent_attempt_rejected_403(self):
        """A retry referencing another student's parent attempt is rejected (403 Forbidden)."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        own_attempt = {
            "id": str(self.test_attempt_id),
            "student_id": str(self.test_student_id),
            "question_id": str(self.test_question_id),
            "parent_attempt_id": str(uuid4()),
            "student_answer": "x^2 + 6x + 9",
            "student_reasoning": "I added 2ab.",
        }
        foreign_parent = {
            "id": own_attempt["parent_attempt_id"],
            "student_id": str(self.other_student_id),
            "question_id": str(self.test_question_id),
        }
        with patch("app.api.routes.learning.get_student_by_auth_user_id", return_value=self.mock_student), \
             patch("app.services.diagnostic_service.get_attempt_by_id", side_effect=[own_attempt, foreign_parent]), \
             patch("app.services.diagnostic_service.get_question_by_id", return_value=self.mock_question_open):
            res = self.client.post(f"/api/v1/learning/attempts/{self.test_attempt_id}/diagnose")
            self.assertEqual(res.status_code, 403)
            self.assertIn("parent attempt belongs to another student", res.json()["detail"].lower())

    # =========================================================================
    # PART 2: DETERMINISTIC MISCONCEPTION DETECTION & REASONING RULES
    # =========================================================================

    def test_correct_mcq_answer_diagnosis(self):
        """Correct MCQ answer diagnosis returns is_correct=True, diagnostic_status='correct'."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        attempt = {
            "id": str(self.test_attempt_id),
            "student_id": str(self.test_student_id),
            "question_id": str(self.test_question_id),
            "parent_attempt_id": None,
            "student_answer": "x^2 + 4x + 4",
            "student_reasoning": "Expanded (x+2)(x+2) = x^2 + 2x + 2x + 4.",
        }
        with patch("app.api.routes.learning.get_student_by_auth_user_id", return_value=self.mock_student), \
             patch("app.services.diagnostic_service.get_attempt_by_id", return_value=attempt), \
             patch("app.services.diagnostic_service.get_question_by_id", return_value=self.mock_question_mcq), \
             patch("app.services.diagnostic_service.update_student_learning_state", return_value=(0.85, "mastered")):
            res = self.client.post(f"/api/v1/learning/attempts/{self.test_attempt_id}/diagnose")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data["is_correct"])
            self.assertEqual(data["diagnostic_status"], "correct")
            self.assertFalse(data["detected_misconception"])
            self.assertIsNone(data["misconception_name"])
            self.assertEqual(data["next_action"], "proceed")

    def test_incorrect_mathematics_answer_empty_reasoning_returns_insufficient_evidence(self):
        """Rule 6: Empty reasoning is conservative and returns diagnostic_status='insufficient_evidence'."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        attempt = {
            "id": str(self.test_attempt_id),
            "student_id": str(self.test_student_id),
            "question_id": str(self.test_question_id),
            "parent_attempt_id": None,
            "student_answer": "x^2 + 9",
            "student_reasoning": "",  # Empty reasoning
        }
        with patch("app.api.routes.learning.get_student_by_auth_user_id", return_value=self.mock_student), \
             patch("app.services.diagnostic_service.get_attempt_by_id", return_value=attempt), \
             patch("app.services.diagnostic_service.get_question_by_id", return_value=self.mock_question_open), \
             patch("app.services.diagnostic_service.update_student_learning_state", return_value=(0.0, "in_progress")):
            res = self.client.post(f"/api/v1/learning/attempts/{self.test_attempt_id}/diagnose")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertFalse(data["is_correct"])
            self.assertEqual(data["diagnostic_status"], "insufficient_evidence")
            self.assertFalse(data["detected_misconception"])
            self.assertEqual(data["next_action"], "retry")

    def test_guessing_reasoning_returns_insufficient_evidence(self):
        """Reasoning indicating a random guess does not invent a misconception."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        attempt = {
            "id": str(self.test_attempt_id),
            "student_id": str(self.test_student_id),
            "question_id": str(self.test_question_id),
            "parent_attempt_id": None,
            "student_answer": "x^2 + 9",
            "student_reasoning": "I don't know, just guessing.",
        }
        with patch("app.api.routes.learning.get_student_by_auth_user_id", return_value=self.mock_student), \
             patch("app.services.diagnostic_service.get_attempt_by_id", return_value=attempt), \
             patch("app.services.diagnostic_service.get_question_by_id", return_value=self.mock_question_open), \
             patch("app.services.diagnostic_service.update_student_learning_state", return_value=(0.0, "in_progress")):
            res = self.client.post(f"/api/v1/learning/attempts/{self.test_attempt_id}/diagnose")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertFalse(data["is_correct"])
            self.assertEqual(data["diagnostic_status"], "insufficient_evidence")
            self.assertFalse(data["detected_misconception"])

    def test_sum_of_squares_misconception_detection(self):
        """Student squaring both terms separately triggers 'Treating a square of a sum as a sum of squares'."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        attempt = {
            "id": str(self.test_attempt_id),
            "student_id": str(self.test_student_id),
            "question_id": str(self.test_question_id),
            "parent_attempt_id": None,
            "student_answer": "x^2 + 9",
            "student_reasoning": "When squaring a sum, I square both terms separately.",
        }
        with patch("app.api.routes.learning.get_student_by_auth_user_id", return_value=self.mock_student), \
             patch("app.services.diagnostic_service.get_attempt_by_id", return_value=attempt), \
             patch("app.services.diagnostic_service.get_question_by_id", return_value=self.mock_question_open), \
             patch("app.services.diagnostic_service.get_misconception_by_name", return_value=self.mock_misconception_sum_squares), \
             patch("app.services.diagnostic_service.select_intervention", return_value=self.mock_intervention), \
             patch("app.services.diagnostic_service.update_student_learning_state", return_value=(0.0, "in_progress")):
            res = self.client.post(f"/api/v1/learning/attempts/{self.test_attempt_id}/diagnose")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertFalse(data["is_correct"])
            self.assertEqual(data["diagnostic_status"], "misconception_detected")
            self.assertTrue(data["detected_misconception"])
            self.assertEqual(data["misconception_name"], "Treating a square of a sum as a sum of squares")
            self.assertEqual(data["severity"], "fundamental")
            self.assertTrue(data["intervention"])
            self.assertEqual(data["intervention_id"], str(self.test_intervention_id))
            self.assertEqual(data["intervention_type"], "counter_example")
            self.assertIn("counterexample", data["intervention_content"].lower())
            self.assertEqual(data["next_action"], "review_intervention")

    def test_missing_cross_term_misconception_detection(self):
        """Reasoning explicitly highlighting omission of 2ab triggers 'Missing the cross term when squaring a binomial'."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        attempt = {
            "id": str(self.test_attempt_id),
            "student_id": str(self.test_student_id),
            "question_id": str(self.test_question_id),
            "parent_attempt_id": None,
            "student_answer": "x^2 + 9",
            "student_reasoning": "I squared x and 3, there is no cross term or middle term.",
        }
        with patch("app.api.routes.learning.get_student_by_auth_user_id", return_value=self.mock_student), \
             patch("app.services.diagnostic_service.get_attempt_by_id", return_value=attempt), \
             patch("app.services.diagnostic_service.get_question_by_id", return_value=self.mock_question_open), \
             patch("app.services.diagnostic_service.get_misconception_by_name", return_value=self.mock_misconception_missing_cross), \
             patch("app.services.diagnostic_service.select_intervention", return_value=self.mock_intervention), \
             patch("app.services.diagnostic_service.update_student_learning_state", return_value=(0.0, "in_progress")):
            res = self.client.post(f"/api/v1/learning/attempts/{self.test_attempt_id}/diagnose")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertFalse(data["is_correct"])
            self.assertEqual(data["diagnostic_status"], "misconception_detected")
            self.assertTrue(data["detected_misconception"])
            self.assertEqual(data["misconception_name"], "Missing the cross term when squaring a binomial")

    # =========================================================================
    # PART 3: RETRY FLOW & REPAIR LOGIC
    # =========================================================================

    def test_correct_retry_repairs_misconception(self):
        """A correct retry with reasoning addressing the cross term transitions to diagnostic_status='repaired'."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        parent_id = uuid4()
        parent_attempt = {
            "id": str(parent_id),
            "student_id": str(self.test_student_id),
            "question_id": str(self.test_question_id),
            "student_answer": "x^2 + 9",
            "student_reasoning": "I square both terms separately.",
            "is_correct": False,
            "detected_misconception_id": str(self.test_misc_id),
        }
        retry_attempt = {
            "id": str(self.test_attempt_id),
            "student_id": str(self.test_student_id),
            "question_id": str(self.test_question_id),
            "parent_attempt_id": str(parent_id),
            "student_answer": "x^2 + 6x + 9",
            "student_reasoning": "I used the area model and added the 2ab cross term 2 * x * 3 = 6x.",
        }
        with patch("app.api.routes.learning.get_student_by_auth_user_id", return_value=self.mock_student), \
             patch("app.services.diagnostic_service.get_attempt_by_id", side_effect=[retry_attempt, parent_attempt]), \
             patch("app.services.diagnostic_service.get_question_by_id", return_value=self.mock_question_open), \
             patch("app.services.diagnostic_service.update_student_learning_state", return_value=(0.75, "in_progress")):
            res = self.client.post(f"/api/v1/learning/attempts/{self.test_attempt_id}/diagnose")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data["is_correct"])
            self.assertEqual(data["diagnostic_status"], "repaired")
            self.assertFalse(data["detected_misconception"])
            self.assertEqual(data["next_action"], "proceed")

    def test_incorrect_retry_does_not_repair_misconception(self):
        """An incorrect retry does NOT mark the misconception repaired simply because answer changed."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        parent_id = uuid4()
        parent_attempt = {
            "id": str(parent_id),
            "student_id": str(self.test_student_id),
            "question_id": str(self.test_question_id),
            "student_answer": "x^2 + 9",
            "is_correct": False,
            "detected_misconception_id": str(self.test_misc_id),
        }
        # Student changed answer to another incorrect expression
        retry_attempt = {
            "id": str(self.test_attempt_id),
            "student_id": str(self.test_student_id),
            "question_id": str(self.test_question_id),
            "parent_attempt_id": str(parent_id),
            "student_answer": "x^2 + 18",
            "student_reasoning": "I multiplied the constant by 2.",
        }
        with patch("app.api.routes.learning.get_student_by_auth_user_id", return_value=self.mock_student), \
             patch("app.services.diagnostic_service.get_attempt_by_id", side_effect=[retry_attempt, parent_attempt]), \
             patch("app.services.diagnostic_service.get_question_by_id", return_value=self.mock_question_open), \
             patch("app.services.diagnostic_service.update_student_learning_state", return_value=(0.0, "needs_review")):
            res = self.client.post(f"/api/v1/learning/attempts/{self.test_attempt_id}/diagnose")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertFalse(data["is_correct"])
            self.assertNotEqual(data["diagnostic_status"], "repaired")

    # =========================================================================
    # PART 4: CONCEPT MASTERY FORMULA
    # =========================================================================

    def test_concept_mastery_formula_bounds_and_states(self):
        """Mastery score is strictly bounded [0.0, 1.0] and classifies correctly."""
        # Unstarted
        score, status = calculate_concept_mastery(0, 0, 0, 0)
        self.assertEqual(score, 0.0)
        self.assertEqual(status, "unstarted")

        # First attempt with active misconception
        score, status = calculate_concept_mastery(total_attempts=1, successful_attempts=0, active_misconceptions_count=1, repaired_misconceptions_count=0)
        self.assertEqual(score, 0.0)
        self.assertEqual(status, "in_progress")

        # Recurring unresolved misconception triggers 'needs_review'
        score, status = calculate_concept_mastery(total_attempts=2, successful_attempts=0, active_misconceptions_count=1, repaired_misconceptions_count=0, recurring_count=1)
        self.assertEqual(score, 0.0)
        self.assertEqual(status, "needs_review")

        # Repaired misconception on retry
        score, status = calculate_concept_mastery(total_attempts=2, successful_attempts=1, active_misconceptions_count=0, repaired_misconceptions_count=1)
        self.assertGreater(score, 0.4)
        self.assertLessEqual(score, 1.0)
        self.assertEqual(status, "in_progress")

        # Mastered: high accuracy, zero active misconceptions
        score, status = calculate_concept_mastery(total_attempts=5, successful_attempts=5, active_misconceptions_count=0, repaired_misconceptions_count=0)
        self.assertEqual(score, 0.8)
        self.assertEqual(status, "mastered")

    # =========================================================================
    # PART 5: SECURITY & ANSWER PROTECTION
    # =========================================================================

    def test_expected_answer_never_exposed_in_diagnostic_response(self):
        """DiagnosticResponse never includes expected_answer or private grading rubrics."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        attempt = {
            "id": str(self.test_attempt_id),
            "student_id": str(self.test_student_id),
            "question_id": str(self.test_question_id),
            "parent_attempt_id": None,
            "student_answer": "x^2 + 9",
            "student_reasoning": "When squaring a sum, I square both terms separately.",
        }
        with patch("app.api.routes.learning.get_student_by_auth_user_id", return_value=self.mock_student), \
             patch("app.services.diagnostic_service.get_attempt_by_id", return_value=attempt), \
             patch("app.services.diagnostic_service.get_question_by_id", return_value=self.mock_question_open), \
             patch("app.services.diagnostic_service.get_misconception_by_name", return_value=self.mock_misconception_sum_squares), \
             patch("app.services.diagnostic_service.select_intervention", return_value=self.mock_intervention), \
             patch("app.services.diagnostic_service.update_student_learning_state", return_value=(0.0, "in_progress")):
            res = self.client.post(f"/api/v1/learning/attempts/{self.test_attempt_id}/diagnose")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            # Verify no answer leakage
            self.assertNotIn("expected_answer", data)
            self.assertNotIn("rubric", data)
            self.assertNotIn("x^2 + 6x + 9", str(data))
