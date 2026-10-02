-- ==============================================================================
-- Migration: 004_auth_student_link.sql
-- Description: Adds auth_user_id to the students table to link Supabase Auth
--              users (Email/Password, Google OAuth) with student profiles.
--
-- NOTE:
-- - Uses a UUID link without a direct foreign key to auth.users for compatibility
--   across Supabase hosting environments and migration runners.
-- - Nullable initially so existing students without auth links remain valid.
-- - Enforces a UNIQUE constraint so each Auth user maps to at most one student.
-- - Idempotent and non-destructive.
--
-- Target: PostgreSQL / Supabase
-- Idempotent: Yes
-- ==============================================================================

-- 1. Add auth_user_id column if it does not exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'students' AND column_name = 'auth_user_id'
    ) THEN
        ALTER TABLE students ADD COLUMN auth_user_id UUID DEFAULT NULL;
    END IF;
END $$;

-- 2. Add Unique constraint on auth_user_id
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_students_auth_user_id'
    ) THEN
        ALTER TABLE students ADD CONSTRAINT uq_students_auth_user_id UNIQUE (auth_user_id);
    END IF;
END $$;

-- 3. Create index for fast lookups by auth_user_id
CREATE INDEX IF NOT EXISTS idx_students_auth_user_id ON students(auth_user_id);
