"""
Unit and integration tests for Stage 14: Student Learning API.
Tests safe question retrieval, deterministic evaluation, attempt submission,
retry attempt chaining, attempt history isolation, and regressions.
"""

import unittest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from starlette.testclient import TestClient

from app.api.routes.auth import get_current_user
from app.main import app
from app.schemas.auth import AuthenticatedUserResponse


class TestLearningEndpoints(unittest.TestCase):
    """Test suite covering the student learning routes and logic."""

    def setUp(self):
        self.client = TestClient(app)
        self.test_user_id = uuid4()
        self.test_student_id = uuid4()
        self.test_concept_id = uuid4()
        self.test_question_id = uuid4()

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

    def tearDown(self):
        # Clear any dependency overrides
        app.dependency_overrides.clear()

    # =========================================================================
    # PART 1: UNAUTHENTICATED REQUESTS (401)
    # =========================================================================

    def test_get_questions_without_token_returns_401(self):
        """GET /api/v1/learning/concepts/{id}/questions without auth returns 401."""
        response = self.client.get(f"/api/v1/learning/concepts/{self.test_concept_id}/questions")
        self.assertEqual(response.status_code, 401)
        self.assertIn("Authentication required", response.json()["detail"])

    def test_post_attempt_without_token_returns_401(self):
        """POST /api/v1/learning/attempts without auth returns 401."""
        response = self.client.post(
            "/api/v1/learning/attempts",
            json={
                "question_id": str(self.test_question_id),
                "student_answer": "x^2 + 4x + 4",
            },
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Authentication required", response.json()["detail"])

    def test_get_attempts_without_token_returns_401(self):
        """GET /api/v1/learning/attempts without auth returns 401."""
        response = self.client.get("/api/v1/learning/attempts")
        self.assertEqual(response.status_code, 401)
        self.assertIn("Authentication required", response.json()["detail"])

    # =========================================================================
    # PART 2: REQUEST VALIDATION (422 / 400)
    # =========================================================================

    def test_empty_student_answer_returns_422(self):
        """Empty student_answer should fail validation with 422."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        with patch("app.api.routes.learning.get_student_by_auth_user_id", return_value=self.mock_student):
            # Whitespace only
            response = self.client.post(
                "/api/v1/learning/attempts",
                json={
                    "question_id": str(self.test_question_id),
                    "student_answer": "   ",
                },
            )
            self.assertEqual(response.status_code, 422)

            # Empty string
            response2 = self.client.post(
                "/api/v1/learning/attempts",
                json={
                    "question_id": str(self.test_question_id),
                    "student_answer": "",
                },
            )
            self.assertEqual(response2.status_code, 422)

    def test_confidence_score_out_of_bounds_returns_422(self):
        """confidence_score outside [0.0, 1.0] should fail validation with 422."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        with patch("app.api.routes.learning.get_student_by_auth_user_id", return_value=self.mock_student):
            # Greater than 1.0
            response = self.client.post(
                "/api/v1/learning/attempts",
                json={
                    "question_id": str(self.test_question_id),
                    "student_answer": "valid answer",
                    "confidence_score": 1.5,
                },
            )
            self.assertEqual(response.status_code, 422)

            # Less than 0.0
            response2 = self.client.post(
                "/api/v1/learning/attempts",
                json={
                    "question_id": str(self.test_question_id),
                    "student_answer": "valid answer",
                    "confidence_score": -0.1,
                },
            )
            self.assertEqual(response2.status_code, 422)

    def test_attempt_submission_forbids_extra_student_identity_fields(self):
        """Submitting client-provided student_id or auth_user_id fails validation."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        with patch("app.api.routes.learning.get_student_by_auth_user_id", return_value=self.mock_student):
            response = self.client.post(
                "/api/v1/learning/attempts",
                json={
                    "question_id": str(self.test_question_id),
                    "student_answer": "answer",
                    "student_id": str(uuid4()),
                },
            )
            self.assertEqual(response.status_code, 422)

    def test_invalid_uuid_returns_422(self):
        """Invalid UUID parameters return 422 Unprocessable Entity."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        with patch("app.api.routes.learning.get_student_by_auth_user_id", return_value=self.mock_student):
            response = self.client.get("/api/v1/learning/concepts/invalid-uuid-format/questions")
            self.assertEqual(response.status_code, 422)

    # =========================================================================
    # PART 3: STUDENT PROFILE REQUIREMENT (404)
    # =========================================================================

    def test_authenticated_user_without_student_profile_returns_404(self):
        """If user is authenticated with Supabase but has no student record, returns 404."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        with patch("app.api.routes.learning.get_student_by_auth_user_id", return_value=None):
            response = self.client.get(f"/api/v1/learning/concepts/{self.test_concept_id}/questions")
            self.assertEqual(response.status_code, 404)
            self.assertIn("No student profile is linked", response.json()["detail"])

    # =========================================================================
    # PART 4: SAFE QUESTION RETRIEVAL (NO ANSWERS LEAKED)
    # =========================================================================

    @patch("app.api.routes.learning.get_safe_questions_by_concept")
    @patch("app.api.routes.learning.get_concept_by_id")
    def test_safe_question_retrieval_does_not_expose_answers_or_rubrics(
        self, mock_get_concept, mock_get_safe_questions
    ):
        """Safe question endpoint hides expected_answer and private rubric fields."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        with patch("app.api.routes.learning.get_student_by_auth_user_id", return_value=self.mock_student):
            mock_get_concept.return_value = {"id": str(self.test_concept_id), "name": "Algebra Concept"}

            mcq_id = str(uuid4())
            open_id = str(uuid4())

            # Service returns sanitized questions
            mock_get_safe_questions.return_value = [
                {
                    "id": mcq_id,
                    "concept_id": str(self.test_concept_id),
                    "title": "MCQ Question",
                    "prompt": "Which expression is equal to (x+2)^2?",
                    "question_type": "multiple_choice",
                    "difficulty": "beginner",
                    "created_at": "2026-10-01T00:00:00Z",
                    "rubric": {
                        "choices": [
                            {"label": "A", "text": "x^2 + 4"},
                            {"label": "B", "text": "x^2 + 4x + 4"},
                        ]
                    },
                },
                {
                    "id": open_id,
                    "concept_id": str(self.test_concept_id),
                    "title": "Open Response Question",
                    "prompt": "Expand (x+3)^2.",
                    "question_type": "open_response",
                    "difficulty": "intermediate",
                    "created_at": "2026-10-01T00:00:00Z",
                    "rubric": None,
                },
            ]

            response = self.client.get(f"/api/v1/learning/concepts/{self.test_concept_id}/questions")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(len(data), 2)

            for item in data:
                # CRITICAL: expected_answer must NEVER be present
                self.assertNotIn("expected_answer", item)

                if item["question_type"] == "multiple_choice":
                    # Choices should contain label and text only
                    choices = item["rubric"]["choices"]
                    for choice in choices:
                        self.assertIn("label", choice)
                        self.assertIn("text", choice)
                        self.assertNotIn("is_correct", choice)
                        self.assertNotIn("associated_misconception", choice)

    # =========================================================================
    # PART 5: DETERMINISTIC EVALUATION & ATTEMPTS
    # =========================================================================

    @patch("app.services.learning_service.get_supabase_client")
    def test_correct_mcq_attempt_sets_is_correct_true(self, mock_get_supabase):
        """Correct MCQ attempt sets is_correct=True and attempt_number=1."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        with patch("app.api.routes.learning.get_student_by_auth_user_id", return_value=self.mock_student):
            # Mock question in DB
            mock_question = {
                "id": str(self.test_question_id),
                "concept_id": str(self.test_concept_id),
                "question_type": "multiple_choice",
                "expected_answer": "x^2 + 4x + 4",
                "rubric": {
                    "choices": [
                        {"label": "A", "text": "x^2 + 4", "is_correct": False},
                        {"label": "B", "text": "x^2 + 4x + 4", "is_correct": True},
                    ]
                },
            }

            mock_sb = MagicMock()
            mock_get_supabase.return_value = mock_sb

            # Question lookup mock
            mock_sb.table("questions").select("*").eq("id", str(self.test_question_id)).limit(1).execute.return_value.data = [mock_question]

            # Attempt insert mock
            attempt_id = str(uuid4())
            mock_sb.table("student_attempts").insert.return_value.execute.return_value.data = [
                {
                    "id": attempt_id,
                    "student_id": str(self.test_student_id),
                    "question_id": str(self.test_question_id),
                    "parent_attempt_id": None,
                    "attempt_number": 1,
                    "student_answer": "B",
                    "student_reasoning": "I expanded the binomial",
                    "is_correct": True,
                    "confidence_score": 0.9,
                    "detected_misconception_id": None,
                    "analysis_reasoning": None,
                    "created_at": "2026-10-01T00:00:00Z",
                }
            ]

            response = self.client.post(
                "/api/v1/learning/attempts",
                json={
                    "question_id": str(self.test_question_id),
                    "student_answer": "B",
                    "student_reasoning": "I expanded the binomial",
                    "confidence_score": 0.9,
                },
            )
            self.assertEqual(response.status_code, 201)
            data = response.json()
            self.assertTrue(data["is_correct"])
            self.assertEqual(data["attempt_number"], 1)
            self.assertIsNone(data["parent_attempt_id"])
            self.assertNotIn("expected_answer", data)

    @patch("app.services.learning_service.get_supabase_client")
    def test_incorrect_mcq_attempt_sets_is_correct_false(self, mock_get_supabase):
        """Incorrect MCQ attempt sets is_correct=False."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        with patch("app.api.routes.learning.get_student_by_auth_user_id", return_value=self.mock_student):
            mock_question = {
                "id": str(self.test_question_id),
                "concept_id": str(self.test_concept_id),
                "question_type": "multiple_choice",
                "expected_answer": "x^2 + 4x + 4",
                "rubric": {
                    "choices": [
                        {"label": "A", "text": "x^2 + 4", "is_correct": False},
                        {"label": "B", "text": "x^2 + 4x + 4", "is_correct": True},
                    ]
                },
            }

            mock_sb = MagicMock()
            mock_get_supabase.return_value = mock_sb
            mock_sb.table("questions").select("*").eq("id", str(self.test_question_id)).limit(1).execute.return_value.data = [mock_question]

            attempt_id = str(uuid4())
            mock_sb.table("student_attempts").insert.return_value.execute.return_value.data = [
                {
                    "id": attempt_id,
                    "student_id": str(self.test_student_id),
                    "question_id": str(self.test_question_id),
                    "parent_attempt_id": None,
                    "attempt_number": 1,
                    "student_answer": "A",
                    "student_reasoning": "Square both parts",
                    "is_correct": False,
                    "confidence_score": 0.8,
                    "detected_misconception_id": None,
                    "analysis_reasoning": None,
                    "created_at": "2026-10-01T00:00:00Z",
                }
            ]

            response = self.client.post(
                "/api/v1/learning/attempts",
                json={
                    "question_id": str(self.test_question_id),
                    "student_answer": "A",
                    "confidence_score": 0.8,
                },
            )
            self.assertEqual(response.status_code, 201)
            data = response.json()
            self.assertFalse(data["is_correct"])

    @patch("app.services.learning_service.get_supabase_client")
    def test_open_response_sets_is_correct_null(self, mock_get_supabase):
        """Open-response questions do not perform AI grading in Stage 14, leaving is_correct=None."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        with patch("app.api.routes.learning.get_student_by_auth_user_id", return_value=self.mock_student):
            mock_question = {
                "id": str(self.test_question_id),
                "concept_id": str(self.test_concept_id),
                "question_type": "open_response",
                "expected_answer": "x^2 + 6x + 9",
                "rubric": {},
            }

            mock_sb = MagicMock()
            mock_get_supabase.return_value = mock_sb
            mock_sb.table("questions").select("*").eq("id", str(self.test_question_id)).limit(1).execute.return_value.data = [mock_question]

            attempt_id = str(uuid4())
            mock_sb.table("student_attempts").insert.return_value.execute.return_value.data = [
                {
                    "id": attempt_id,
                    "student_id": str(self.test_student_id),
                    "question_id": str(self.test_question_id),
                    "parent_attempt_id": None,
                    "attempt_number": 1,
                    "student_answer": "x^2 + 6x + 9",
                    "student_reasoning": "Expanded FOIL method",
                    "is_correct": None,
                    "confidence_score": 1.0,
                    "detected_misconception_id": None,
                    "analysis_reasoning": None,
                    "created_at": "2026-10-01T00:00:00Z",
                }
            ]

            response = self.client.post(
                "/api/v1/learning/attempts",
                json={
                    "question_id": str(self.test_question_id),
                    "student_answer": "x^2 + 6x + 9",
                    "student_reasoning": "Expanded FOIL method",
                    "confidence_score": 1.0,
                },
            )
            self.assertEqual(response.status_code, 201)
            data = response.json()
            self.assertIsNone(data["is_correct"])

    # =========================================================================
    # PART 6: RETRY ATTEMPTS (PARENT ATTEMPT CHAINING)
    # =========================================================================

    @patch("app.services.learning_service.get_supabase_client")
    def test_retry_attempt_increments_attempt_number(self, mock_get_supabase):
        """A retry submission increments attempt_number to 2 and sets parent_attempt_id."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        with patch("app.api.routes.learning.get_student_by_auth_user_id", return_value=self.mock_student):
            parent_attempt_id = str(uuid4())
            mock_question = {
                "id": str(self.test_question_id),
                "concept_id": str(self.test_concept_id),
                "question_type": "multiple_choice",
                "expected_answer": "x^2 + 4x + 4",
                "rubric": {
                    "choices": [
                        {"label": "A", "text": "x^2 + 4", "is_correct": False},
                        {"label": "B", "text": "x^2 + 4x + 4", "is_correct": True},
                    ]
                },
            }

            mock_parent_attempt = {
                "id": parent_attempt_id,
                "student_id": str(self.test_student_id),
                "question_id": str(self.test_question_id),
                "attempt_number": 1,
            }

            mock_sb = MagicMock()
            mock_get_supabase.return_value = mock_sb

            # Table queries routing
            def mock_table(table_name):
                t_mock = MagicMock()
                if table_name == "questions":
                    t_mock.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [mock_question]
                elif table_name == "student_attempts":
                    t_mock.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [mock_parent_attempt]
                    # Insert mock returns attempt #2
                    new_attempt_id = str(uuid4())
                    t_mock.insert.return_value.execute.return_value.data = [
                        {
                            "id": new_attempt_id,
                            "student_id": str(self.test_student_id),
                            "question_id": str(self.test_question_id),
                            "parent_attempt_id": parent_attempt_id,
                            "attempt_number": 2,
                            "student_answer": "B",
                            "student_reasoning": "Corrected my mistake",
                            "is_correct": True,
                            "confidence_score": 1.0,
                            "detected_misconception_id": None,
                            "analysis_reasoning": None,
                            "created_at": "2026-10-01T00:05:00Z",
                        }
                    ]
                return t_mock

            mock_sb.table.side_effect = mock_table

            response = self.client.post(
                "/api/v1/learning/attempts",
                json={
                    "question_id": str(self.test_question_id),
                    "student_answer": "B",
                    "student_reasoning": "Corrected my mistake",
                    "confidence_score": 1.0,
                    "parent_attempt_id": parent_attempt_id,
                },
            )
            self.assertEqual(response.status_code, 201)
            data = response.json()
            self.assertEqual(data["attempt_number"], 2)
            self.assertEqual(data["parent_attempt_id"], parent_attempt_id)
            self.assertTrue(data["is_correct"])

    @patch("app.services.learning_service.get_supabase_client")
    def test_retry_attempt_rejects_parent_attempt_of_different_student(self, mock_get_supabase):
        """A retry submission pointing to another student's attempt is rejected with 409."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        with patch("app.api.routes.learning.get_student_by_auth_user_id", return_value=self.mock_student):
            other_student_id = str(uuid4())
            parent_attempt_id = str(uuid4())

            mock_question = {
                "id": str(self.test_question_id),
                "concept_id": str(self.test_concept_id),
                "question_type": "multiple_choice",
                "expected_answer": "x^2 + 4x + 4",
            }

            # Parent attempt belongs to other_student_id!
            mock_parent_attempt = {
                "id": parent_attempt_id,
                "student_id": other_student_id,
                "question_id": str(self.test_question_id),
                "attempt_number": 1,
            }

            mock_sb = MagicMock()
            mock_get_supabase.return_value = mock_sb

            def mock_table(table_name):
                t_mock = MagicMock()
                if table_name == "questions":
                    t_mock.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [mock_question]
                elif table_name == "student_attempts":
                    t_mock.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [mock_parent_attempt]
                return t_mock

            mock_sb.table.side_effect = mock_table

            response = self.client.post(
                "/api/v1/learning/attempts",
                json={
                    "question_id": str(self.test_question_id),
                    "student_answer": "B",
                    "parent_attempt_id": parent_attempt_id,
                },
            )
            self.assertEqual(response.status_code, 409)
            self.assertIn("different student", response.json()["detail"])

    @patch("app.services.learning_service.get_supabase_client")
    def test_retry_attempt_rejects_parent_referencing_different_question(self, mock_get_supabase):
        """A retry submission pointing to an attempt on a different question is rejected with 409."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        with patch("app.api.routes.learning.get_student_by_auth_user_id", return_value=self.mock_student):
            parent_attempt_id = str(uuid4())
            different_question_id = str(uuid4())

            mock_question = {
                "id": str(self.test_question_id),
                "concept_id": str(self.test_concept_id),
                "question_type": "multiple_choice",
                "expected_answer": "x^2 + 4x + 4",
            }

            # Parent attempt references different_question_id
            mock_parent_attempt = {
                "id": parent_attempt_id,
                "student_id": str(self.test_student_id),
                "question_id": different_question_id,
                "attempt_number": 1,
            }

            mock_sb = MagicMock()
            mock_get_supabase.return_value = mock_sb

            def mock_table(table_name):
                t_mock = MagicMock()
                if table_name == "questions":
                    t_mock.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [mock_question]
                elif table_name == "student_attempts":
                    t_mock.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [mock_parent_attempt]
                return t_mock

            mock_sb.table.side_effect = mock_table

            response = self.client.post(
                "/api/v1/learning/attempts",
                json={
                    "question_id": str(self.test_question_id),
                    "student_answer": "B",
                    "parent_attempt_id": parent_attempt_id,
                },
            )
            self.assertEqual(response.status_code, 409)
            self.assertIn("different question", response.json()["detail"])

    # =========================================================================
    # PART 7: ATTEMPT HISTORY ISOLATION
    # =========================================================================

    @patch("app.api.routes.learning.get_student_attempts")
    def test_get_attempts_returns_only_authenticated_student_attempts(self, mock_get_attempts):
        """GET /api/v1/learning/attempts returns only the authenticated student's attempts."""
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        with patch("app.api.routes.learning.get_student_by_auth_user_id", return_value=self.mock_student):
            attempt_id = str(uuid4())
            mock_get_attempts.return_value = [
                {
                    "id": attempt_id,
                    "student_id": str(self.test_student_id),
                    "question_id": str(self.test_question_id),
                    "parent_attempt_id": None,
                    "attempt_number": 1,
                    "student_answer": "B",
                    "student_reasoning": "Explanation",
                    "is_correct": True,
                    "confidence_score": 0.85,
                    "detected_misconception_id": None,
                    "analysis_reasoning": None,
                    "created_at": "2026-10-01T00:00:00Z",
                }
            ]

            response = self.client.get("/api/v1/learning/attempts")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["id"], attempt_id)
            mock_get_attempts.assert_called_once_with(
                student_id=str(self.test_student_id),
                question_id=None,
                concept_id=None,
                limit=50,
            )

    # =========================================================================
    # PART 8: REGRESSION CHECKS
    # =========================================================================

    def test_root_endpoint_regression(self):
        """GET / returns 200."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_health_endpoints_regression(self):
        """Health endpoints work as expected."""
        r1 = self.client.get("/api/v1/health")
        self.assertEqual(r1.status_code, 200)

        r2 = self.client.get("/api/v1/storage/health")
        self.assertEqual(r2.status_code, 200)

        r3 = self.client.get("/api/v1/auth/health")
        self.assertEqual(r3.status_code, 200)

    def test_auth_me_without_token_returns_401(self):
        """GET /api/v1/auth/me without token returns 401."""
        response = self.client.get("/api/v1/auth/me")
        self.assertEqual(response.status_code, 401)

    def test_auth_profile_without_token_returns_401(self):
        """GET /api/v1/auth/profile without token returns 401."""
        response = self.client.get("/api/v1/auth/profile")
        self.assertEqual(response.status_code, 401)

    # =========================================================================
    # PART 9: DETERMINISTIC EVALUATOR UNIT TESTS
    # =========================================================================

    def test_evaluator_unit_logic(self):
        """Test evaluate_deterministic_correctness logic thoroughly."""
        from app.services.learning_service import evaluate_deterministic_correctness

        mcq_q = {
            "question_type": "multiple_choice",
            "expected_answer": "x^2 + 4x + 4",
            "rubric": {
                "choices": [
                    {"label": "A", "text": "x^2 + 4", "is_correct": False},
                    {"label": "B", "text": "x^2 + 2x + 4", "is_correct": False},
                    {"label": "C", "text": "x^2 + 4x + 4", "is_correct": True},
                    {"label": "D", "text": "x^2 + 4x + 2", "is_correct": False},
                ]
            },
        }

        # Correct by label (case-insensitive)
        self.assertTrue(evaluate_deterministic_correctness(mcq_q, "C"))
        self.assertTrue(evaluate_deterministic_correctness(mcq_q, "c"))

        # Correct by exact text
        self.assertTrue(evaluate_deterministic_correctness(mcq_q, "x^2 + 4x + 4"))

        # Incorrect by label
        self.assertFalse(evaluate_deterministic_correctness(mcq_q, "A"))
        self.assertFalse(evaluate_deterministic_correctness(mcq_q, "B"))

        # Incorrect by text
        self.assertFalse(evaluate_deterministic_correctness(mcq_q, "x^2 + 4"))

        # Unmatched answer
        self.assertFalse(evaluate_deterministic_correctness(mcq_q, "random nonsense"))

        # Open response returns None
        open_q = {"question_type": "open_response", "expected_answer": "42"}
        self.assertIsNone(evaluate_deterministic_correctness(open_q, "42"))

        # Code returns None
        code_q = {"question_type": "code", "expected_answer": "def foo(): pass"}
        self.assertIsNone(evaluate_deterministic_correctness(code_q, "def foo(): pass"))


if __name__ == "__main__":
    unittest.main()
