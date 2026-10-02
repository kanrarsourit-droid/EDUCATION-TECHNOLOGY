-- ==============================================================================
-- Migration: 002_seed_development_data.sql
-- Description: Development seed dataset for testing the Learning Debugger.
--              Populates the global knowledge domain with a sample subject,
--              topic, concept, misconceptions, diagnostic questions, and
--              targeted interventions.
--
-- NOTE:
-- This is development/test seed data only. It is not production student data.
--
-- Target: PostgreSQL / Supabase
-- Idempotent: Yes (safe to execute multiple times without creating duplicates)
-- ==============================================================================

DO $$
DECLARE
    v_subject_id UUID;
    v_topic_id UUID;
    v_concept_id UUID;
    v_misc_1_id UUID;
    v_misc_2_id UUID;
BEGIN
    -- --------------------------------------------------------------------------
    -- 1. Subject: Mathematics
    -- --------------------------------------------------------------------------
    SELECT id INTO v_subject_id FROM subjects WHERE slug = 'mathematics';
    IF v_subject_id IS NULL THEN
        INSERT INTO subjects (name, slug, description)
        VALUES (
            'Mathematics',
            'mathematics',
            'Mathematics concepts used for testing the Learning Debugger'
        )
        RETURNING id INTO v_subject_id;
    END IF;

    -- --------------------------------------------------------------------------
    -- 2. Topic: Algebra (under Mathematics)
    -- --------------------------------------------------------------------------
    SELECT id INTO v_topic_id FROM topics WHERE subject_id = v_subject_id AND name = 'Algebra';
    IF v_topic_id IS NULL THEN
        INSERT INTO topics (subject_id, name, description, order_index)
        VALUES (
            v_subject_id,
            'Algebra',
            'Fundamental algebraic reasoning and expressions',
            1
        )
        RETURNING id INTO v_topic_id;
    END IF;

    -- --------------------------------------------------------------------------
    -- 3. Concept: Expanding the Square of a Binomial (under Algebra)
    -- --------------------------------------------------------------------------
    SELECT id INTO v_concept_id FROM concepts WHERE topic_id = v_topic_id AND name = 'Expanding the Square of a Binomial';
    IF v_concept_id IS NULL THEN
        INSERT INTO concepts (topic_id, name, description)
        VALUES (
            v_topic_id,
            'Expanding the Square of a Binomial',
            'Understanding why (a + b)^2 expands to a^2 + 2ab + b^2'
        )
        RETURNING id INTO v_concept_id;
    END IF;

    -- --------------------------------------------------------------------------
    -- 4. Misconceptions (under Concept)
    -- --------------------------------------------------------------------------

    -- Misconception 1: Missing the cross term
    SELECT id INTO v_misc_1_id FROM misconceptions
    WHERE concept_id = v_concept_id AND name = 'Missing the cross term when squaring a binomial';

    IF v_misc_1_id IS NULL THEN
        INSERT INTO misconceptions (concept_id, name, description, canonical_example, severity)
        VALUES (
            v_concept_id,
            'Missing the cross term when squaring a binomial',
            'Student believes (a + b)^2 = a^2 + b^2 and does not account for the two ab terms.',
            '(x + 3)^2 = x^2 + 9',
            'fundamental'
        )
        RETURNING id INTO v_misc_1_id;
    END IF;

    -- Misconception 2: Treating square of a sum as sum of squares
    SELECT id INTO v_misc_2_id FROM misconceptions
    WHERE concept_id = v_concept_id AND name = 'Treating a square of a sum as a sum of squares';

    IF v_misc_2_id IS NULL THEN
        INSERT INTO misconceptions (concept_id, name, description, canonical_example, severity)
        VALUES (
            v_concept_id,
            'Treating a square of a sum as a sum of squares',
            'Student applies the square operation independently to each term of a sum.',
            '(x + 2)^2 = x^2 + 4',
            'fundamental'
        )
        RETURNING id INTO v_misc_2_id;
    END IF;

    -- --------------------------------------------------------------------------
    -- 5. Diagnostic Questions (under Concept)
    -- --------------------------------------------------------------------------

    -- Question 1: Open Response
    IF NOT EXISTS (
        SELECT 1 FROM questions WHERE concept_id = v_concept_id AND title = 'Expand a binomial square'
    ) THEN
        INSERT INTO questions (concept_id, title, prompt, question_type, expected_answer, rubric, difficulty)
        VALUES (
            v_concept_id,
            'Expand a binomial square',
            'Expand (x + 3)^2.',
            'open_response',
            'x^2 + 6x + 9',
            '{"instructions": "Evaluate whether student reasoning reveals an understanding of the 2ab cross term."}'::jsonb,
            'beginner'
        );
    END IF;

    -- Question 2: Multiple Choice with Rubric
    IF NOT EXISTS (
        SELECT 1 FROM questions WHERE concept_id = v_concept_id AND title = 'Identify the correct expansion'
    ) THEN
        INSERT INTO questions (concept_id, title, prompt, question_type, expected_answer, rubric, difficulty)
        VALUES (
            v_concept_id,
            'Identify the correct expansion',
            'Which expression is equal to (x + 2)^2?',
            'multiple_choice',
            'x^2 + 4x + 4',
            '{
                "choices": [
                    {"label": "A", "text": "x^2 + 4", "is_correct": false, "associated_misconception": "Treating a square of a sum as a sum of squares"},
                    {"label": "B", "text": "x^2 + 2x + 4", "is_correct": false, "associated_misconception": "Missing the factor of 2 in 2ab"},
                    {"label": "C", "text": "x^2 + 4x + 4", "is_correct": true},
                    {"label": "D", "text": "x^2 + 4x + 2", "is_correct": false, "associated_misconception": "Multiplying constant by 2 instead of squaring"}
                ]
            }'::jsonb,
            'beginner'
        );
    END IF;

    -- --------------------------------------------------------------------------
    -- 6. Targeted Interventions (associated with Misconceptions)
    -- --------------------------------------------------------------------------

    -- Intervention 1: For Misconception 1
    IF NOT EXISTS (
        SELECT 1 FROM interventions WHERE misconception_id = v_misc_1_id AND title = 'Visualize the missing cross term'
    ) THEN
        INSERT INTO interventions (misconception_id, title, intervention_type, content)
        VALUES (
            v_misc_1_id,
            'Visualize the missing cross term',
            'conceptual_explainer',
            'Explain using the area model of a square that (a+b)^2 contains four regions: a², ab, ab, and b². Therefore the two ab regions combine into 2ab.'
        );
    END IF;

    -- Intervention 2: For Misconception 2
    IF NOT EXISTS (
        SELECT 1 FROM interventions WHERE misconception_id = v_misc_2_id AND title = 'Challenge the sum-of-squares rule'
    ) THEN
        INSERT INTO interventions (misconception_id, title, intervention_type, content)
        VALUES (
            v_misc_2_id,
            'Challenge the sum-of-squares rule',
            'counter_example',
            'Use a simple numerical counterexample such as (2+3)^2 = 25 while 2²+3² = 13, showing that squaring a sum is not the same as adding the individual squares.'
        );
    END IF;

END $$;
