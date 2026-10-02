-- ==============================================================================
-- Migration: 001_initial_learning_debugger_schema.sql
-- Description: Core schema for the Learning Debugger platform.
--              Sets up global knowledge tables (subjects, topics, concepts,
--              misconceptions, questions, interventions) and student diagnostic
--              state tables (students, attempts, misconception tracking,
--              intervention tracking, mastery).
-- Target: PostgreSQL / Supabase
-- Idempotent: Yes (uses IF NOT EXISTS guards)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Helper Function: update_updated_at_column
-- Automatically sets updated_at = UTC now() on record updates
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = timezone('utc'::text, now());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- SECTION 1: GLOBAL KNOWLEDGE DOMAIN
-- ==============================================================================

-- 1. Subjects
CREATE TABLE IF NOT EXISTS subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 2. Topics
CREATE TABLE IF NOT EXISTS topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    order_index INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 3. Concepts
CREATE TABLE IF NOT EXISTS concepts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 4. Misconceptions (Global catalog of conceptual flaws)
CREATE TABLE IF NOT EXISTS misconceptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    canonical_example TEXT,
    severity TEXT NOT NULL DEFAULT 'moderate'
        CHECK (severity IN ('minor', 'moderate', 'fundamental')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 5. Questions (Diagnostic items targeting concepts)
CREATE TABLE IF NOT EXISTS questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    prompt TEXT NOT NULL,
    question_type TEXT NOT NULL DEFAULT 'open_response'
        CHECK (question_type IN ('multiple_choice', 'open_response', 'code')),
    expected_answer TEXT NOT NULL,
    rubric JSONB NOT NULL DEFAULT '{}'::jsonb,
    difficulty TEXT NOT NULL DEFAULT 'intermediate'
        CHECK (difficulty IN ('beginner', 'intermediate', 'advanced')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 6. Interventions (Targeted remedial content per misconception)
CREATE TABLE IF NOT EXISTS interventions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    misconception_id UUID NOT NULL REFERENCES misconceptions(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    intervention_type TEXT NOT NULL DEFAULT 'conceptual_explainer'
        CHECK (intervention_type IN ('socratic_question', 'counter_example', 'conceptual_explainer', 'guided_simulation')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ==============================================================================
-- SECTION 2: STUDENT STATE & DIAGNOSTICS
-- ==============================================================================

-- 7. Students (Profile entity - unlinked from auth.users until Auth stage)
CREATE TABLE IF NOT EXISTS students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 8. Student Attempts (Preserves student answer vs reasoning separately)
CREATE TABLE IF NOT EXISTS student_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE RESTRICT,
    parent_attempt_id UUID REFERENCES student_attempts(id) ON DELETE SET NULL,
    attempt_number INTEGER NOT NULL DEFAULT 1,
    student_answer TEXT NOT NULL,
    student_reasoning TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT NULL,
    detected_misconception_id UUID REFERENCES misconceptions(id) ON DELETE SET NULL,
    analysis_reasoning TEXT,
    confidence_score NUMERIC(4,3)
        CHECK (confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 9. Student Misconceptions (Longitudinal student-specific misconception tracker)
CREATE TABLE IF NOT EXISTS student_misconceptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    misconception_id UUID NOT NULL REFERENCES misconceptions(id) ON DELETE CASCADE,
    occurrence_count INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'under_intervention', 'repaired', 'recurring')),
    first_detected_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    last_detected_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    repaired_at TIMESTAMPTZ DEFAULT NULL,
    CONSTRAINT uq_student_misconceptions UNIQUE (student_id, misconception_id)
);

-- 10. Student Interventions (Records delivery, student interaction, and outcome)
CREATE TABLE IF NOT EXISTS student_interventions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    attempt_id UUID NOT NULL REFERENCES student_attempts(id) ON DELETE CASCADE,
    misconception_id UUID NOT NULL REFERENCES misconceptions(id) ON DELETE CASCADE,
    intervention_id UUID REFERENCES interventions(id) ON DELETE SET NULL,
    delivered_content TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'presented'
        CHECK (status IN ('presented', 'completed', 'skipped')),
    student_response TEXT DEFAULT NULL,
    is_repaired BOOLEAN DEFAULT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    completed_at TIMESTAMPTZ DEFAULT NULL
);

-- 11. Student Concept Mastery (Aggregated mastery metric per concept)
CREATE TABLE IF NOT EXISTS student_concept_mastery (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    mastery_score NUMERIC(4,3) NOT NULL DEFAULT 0.000
        CHECK (mastery_score >= 0.0 AND mastery_score <= 1.0),
    status TEXT NOT NULL DEFAULT 'unstarted'
        CHECK (status IN ('unstarted', 'in_progress', 'mastered', 'needs_review')),
    total_attempts INTEGER NOT NULL DEFAULT 0,
    successful_attempts INTEGER NOT NULL DEFAULT 0,
    last_attempt_at TIMESTAMPTZ DEFAULT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_student_concept_mastery UNIQUE (student_id, concept_id)
);

-- ==============================================================================
-- SECTION 3: TRIGGERS FOR UPDATED_AT
-- ==============================================================================

DROP TRIGGER IF EXISTS trigger_students_updated_at ON students;
CREATE TRIGGER trigger_students_updated_at
    BEFORE UPDATE ON students
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trigger_student_concept_mastery_updated_at ON student_concept_mastery;
CREATE TRIGGER trigger_student_concept_mastery_updated_at
    BEFORE UPDATE ON student_concept_mastery
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ==============================================================================
-- SECTION 4: PERFORMANCE INDEXES
-- ==============================================================================

-- Foreign key lookup indexes (Global hierarchy)
CREATE INDEX IF NOT EXISTS idx_topics_subject_id ON topics(subject_id);
CREATE INDEX IF NOT EXISTS idx_concepts_topic_id ON concepts(topic_id);
CREATE INDEX IF NOT EXISTS idx_questions_concept_id ON questions(concept_id);
CREATE INDEX IF NOT EXISTS idx_misconceptions_concept_id ON misconceptions(concept_id);
CREATE INDEX IF NOT EXISTS idx_interventions_misconception_id ON interventions(misconception_id);

-- Student attempts indexes
CREATE INDEX IF NOT EXISTS idx_student_attempts_student_id ON student_attempts(student_id);
CREATE INDEX IF NOT EXISTS idx_student_attempts_question_id ON student_attempts(question_id);
CREATE INDEX IF NOT EXISTS idx_student_attempts_parent_attempt_id ON student_attempts(parent_attempt_id);
CREATE INDEX IF NOT EXISTS idx_student_attempts_created_at ON student_attempts(created_at DESC);

-- Misconception tracking indexes
CREATE INDEX IF NOT EXISTS idx_student_misconceptions_student_id ON student_misconceptions(student_id);
CREATE INDEX IF NOT EXISTS idx_student_misconceptions_status ON student_misconceptions(status);

-- Intervention tracking indexes
CREATE INDEX IF NOT EXISTS idx_student_interventions_attempt_id ON student_interventions(attempt_id);
CREATE INDEX IF NOT EXISTS idx_student_interventions_student_id ON student_interventions(student_id);

-- Mastery indexes
CREATE INDEX IF NOT EXISTS idx_student_concept_mastery_student_id ON student_concept_mastery(student_id);
