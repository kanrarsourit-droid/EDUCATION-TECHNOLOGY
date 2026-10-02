-- ==============================================================================
-- Migration: 003_curriculum_and_learning_materials.sql
-- Description: Extends the Learning Debugger schema with Curriculum Hierarchy
--              (Curricula -> Curriculum Levels -> Curriculum Subjects) and
--              Learning Materials metadata & chunking support.
--
-- NOTE:
-- This migration is DDL-only. No seed data is added, and no existing tables or
-- data are modified or deleted.
--
-- Target: PostgreSQL / Supabase
-- Idempotent: Yes (uses IF NOT EXISTS guards)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Helper Function: update_updated_at_column
-- Reuses or ensures existence of the automated timestamp updater
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = timezone('utc'::text, now());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- SECTION 1: CURRICULUM HIERARCHY
-- ==============================================================================

-- 1. Curricula (e.g., CBSE, MAKAUT, JEE, NEET, Custom)
CREATE TABLE IF NOT EXISTS curricula (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 2. Curriculum Levels (e.g., Class 11, Class 12, B.Tech, Diploma)
CREATE TABLE IF NOT EXISTS curriculum_levels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    curriculum_id UUID NOT NULL REFERENCES curricula(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    description TEXT,
    order_index INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_curriculum_levels_slug UNIQUE (curriculum_id, slug)
);

-- 3. Curriculum Subjects (Associates a curriculum level to an existing global subject)
CREATE TABLE IF NOT EXISTS curriculum_subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    curriculum_level_id UUID NOT NULL REFERENCES curriculum_levels(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    code TEXT,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_curriculum_subjects UNIQUE (curriculum_level_id, subject_id)
);

-- ==============================================================================
-- SECTION 2: LEARNING MATERIALS & CHUNKS
-- ==============================================================================

-- 4. Learning Materials (Document and media metadata)
CREATE TABLE IF NOT EXISTS learning_materials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    topic_id UUID REFERENCES topics(id) ON DELETE SET NULL,
    concept_id UUID REFERENCES concepts(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    description TEXT,
    material_type TEXT NOT NULL
        CHECK (material_type IN ('pdf', 'text', 'video', 'link', 'document')),
    file_name TEXT,
    storage_path TEXT,
    source_url TEXT,
    mime_type TEXT,
    file_size_bytes BIGINT,
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 5. Learning Material Chunks (Prepares system for document retrieval & processing)
CREATE TABLE IF NOT EXISTS learning_material_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    learning_material_id UUID NOT NULL REFERENCES learning_materials(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    page_number INTEGER,
    section_title TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_learning_material_chunks UNIQUE (learning_material_id, chunk_index)
);

-- ==============================================================================
-- SECTION 3: TRIGGERS FOR UPDATED_AT
-- ==============================================================================

DROP TRIGGER IF EXISTS trigger_learning_materials_updated_at ON learning_materials;
CREATE TRIGGER trigger_learning_materials_updated_at
    BEFORE UPDATE ON learning_materials
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ==============================================================================
-- SECTION 4: PERFORMANCE INDEXES
-- ==============================================================================

-- Curriculum navigation indexes
CREATE INDEX IF NOT EXISTS idx_curriculum_levels_curriculum_id ON curriculum_levels(curriculum_id);
CREATE INDEX IF NOT EXISTS idx_curriculum_subjects_level_id ON curriculum_subjects(curriculum_level_id);
CREATE INDEX IF NOT EXISTS idx_curriculum_subjects_subject_id ON curriculum_subjects(subject_id);

-- Learning materials querying indexes
CREATE INDEX IF NOT EXISTS idx_learning_materials_subject_id ON learning_materials(subject_id);
CREATE INDEX IF NOT EXISTS idx_learning_materials_topic_id ON learning_materials(topic_id);
CREATE INDEX IF NOT EXISTS idx_learning_materials_concept_id ON learning_materials(concept_id);
CREATE INDEX IF NOT EXISTS idx_learning_materials_material_type ON learning_materials(material_type);

-- Chunk retrieval index
CREATE INDEX IF NOT EXISTS idx_learning_material_chunks_material_id ON learning_material_chunks(learning_material_id);
