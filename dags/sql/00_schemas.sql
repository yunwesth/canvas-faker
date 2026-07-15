-- 00_schemas.sql — target contract DDL for the nv-live app.
--
-- Scope: DROP/CREATE only the two target schemas. Never touches `public`
-- (the canvas__* synthetic source) and never DROP DATABASE. The Prefect flow's
-- assert_safe_target() gate must pass before this runs.
--
-- Shapes follow nv-live/frontend/src/types.ts and the gap-plan §8 examples:
--   integer surrogate keys for identity/reference data,
--   uuid ids (deterministic md5-based) for run/assessment/result rows.

DROP SCHEMA IF EXISTS simulation CASCADE;
DROP SCHEMA IF EXISTS canvas_sync CASCADE;
CREATE SCHEMA canvas_sync;
CREATE SCHEMA simulation;

-- ============================================================================
-- canvas_sync.* — identity & reference (integer surrogate keys, sis_id kept)
-- ============================================================================

CREATE TABLE canvas_sync.schools (
    id      integer PRIMARY KEY,
    sis_id  text    NOT NULL,
    name    text    NOT NULL
);

CREATE TABLE canvas_sync.students (
    id          integer PRIMARY KEY,
    sis_id      text    NOT NULL,
    first_name  text    NOT NULL,
    last_name   text    NOT NULL,
    email       text    NOT NULL,
    grade_level integer NOT NULL,                 -- synthesized (see 10_identity.sql)
    school_id   integer NOT NULL REFERENCES canvas_sync.schools(id)
);

CREATE TABLE canvas_sync.staff (
    id          integer PRIMARY KEY,
    sis_id      text    NOT NULL,
    first_name  text    NOT NULL,
    last_name   text    NOT NULL,
    email       text    NOT NULL,
    school_id   integer NOT NULL REFERENCES canvas_sync.schools(id),
    title       text    NOT NULL
);

CREATE TABLE canvas_sync.courses (
    id         integer PRIMARY KEY,
    sis_id     text    NOT NULL,
    name       text    NOT NULL,
    subject    text    NOT NULL,                  -- canonical vocab; == standards.subject
    school_id  integer NOT NULL REFERENCES canvas_sync.schools(id)
);

CREATE TABLE canvas_sync.sections (
    id          integer PRIMARY KEY,
    sis_id      text    NOT NULL,
    name        text    NOT NULL,
    course_id   integer NOT NULL REFERENCES canvas_sync.courses(id),
    teacher_id  integer NOT NULL REFERENCES canvas_sync.staff(id)  -- = course's teacher
);

CREATE TABLE canvas_sync.enrollments (
    id          integer PRIMARY KEY,
    student_id  integer NOT NULL REFERENCES canvas_sync.students(id),
    section_id  integer NOT NULL REFERENCES canvas_sync.sections(id),
    UNIQUE (student_id, section_id)
);

-- helper: course -> canonical subject (one row per course)
CREATE TABLE canvas_sync.subject_map (
    course_id  integer PRIMARY KEY REFERENCES canvas_sync.courses(id),
    subject    text    NOT NULL
);

-- ============================================================================
-- simulation.* — runs, standards, assessments, results, mastery, questions
-- ============================================================================

CREATE TABLE simulation.simulation_runs (
    id              uuid PRIMARY KEY,
    school_year     text NOT NULL,                -- '2025-2026'
    simulation_date date NOT NULL,                -- fixed constant, never now()
    description     text NOT NULL                 -- 'End of Q2' (unique lookup key)
);

CREATE TABLE simulation.standards (
    id          integer PRIMARY KEY,
    code        text    NOT NULL UNIQUE,          -- '6.EE.A.1'
    description text    NOT NULL,
    subject     text    NOT NULL,                 -- canonical vocab; == courses.subject
    grade_level integer NOT NULL,
    domain      text    NOT NULL
);

CREATE TABLE simulation.assessments (
    id              uuid    PRIMARY KEY,
    name            text    NOT NULL,
    assessment_date date    NOT NULL,
    max_score       numeric NOT NULL CHECK (max_score > 0),
    section_id      integer NOT NULL REFERENCES canvas_sync.sections(id),
    standard_id     integer NOT NULL REFERENCES simulation.standards(id)  -- synthesized alignment
);

CREATE TABLE simulation.student_results (
    id            uuid    PRIMARY KEY,
    run_id        uuid    NOT NULL REFERENCES simulation.simulation_runs(id),
    assessment_id uuid    NOT NULL REFERENCES simulation.assessments(id),
    student_id    integer NOT NULL REFERENCES canvas_sync.students(id),
    score         numeric NOT NULL,               -- raw points (not pre-judged)
    responses     jsonb   NOT NULL,               -- {"0":"A","1":"C"} (fabricated)
    UNIQUE (run_id, assessment_id, student_id)
);

CREATE TABLE simulation.standard_mastery (
    id            uuid    PRIMARY KEY,
    run_id        uuid    NOT NULL REFERENCES simulation.simulation_runs(id),
    student_id    integer NOT NULL REFERENCES canvas_sync.students(id),
    standard_id   integer NOT NULL REFERENCES simulation.standards(id),
    mastery_score numeric NOT NULL CHECK (mastery_score >= 0 AND mastery_score <= 1),
    UNIQUE (run_id, student_id, standard_id)
);

CREATE TABLE simulation.assessment_questions (
    id                integer PRIMARY KEY,
    assessment_id     uuid    NOT NULL REFERENCES simulation.assessments(id),
    question_index    integer NOT NULL,           -- 0-based; matches responses keys
    standard_code     text    NOT NULL,
    correct_answer    char(1) NOT NULL,
    answer_ids        jsonb,
    question_text     text,
    answer_a_text     text,
    answer_b_text     text,
    answer_c_text     text,
    answer_d_text     text,
    -- provenance metadata (fabrication is never hidden)
    source_type       text    NOT NULL,           -- 'generated_fallback' here
    is_synthetic_filler boolean NOT NULL,
    source_table      text,
    source_record_id  text,
    UNIQUE (assessment_id, question_index)
);

-- indexes on FK columns for join performance
CREATE INDEX idx_students_school     ON canvas_sync.students(school_id);
CREATE INDEX idx_sections_course     ON canvas_sync.sections(course_id);
CREATE INDEX idx_sections_teacher    ON canvas_sync.sections(teacher_id);
CREATE INDEX idx_enroll_student      ON canvas_sync.enrollments(student_id);
CREATE INDEX idx_enroll_section      ON canvas_sync.enrollments(section_id);
CREATE INDEX idx_assess_section      ON simulation.assessments(section_id);
CREATE INDEX idx_assess_standard     ON simulation.assessments(standard_id);
CREATE INDEX idx_results_assessment  ON simulation.student_results(assessment_id);
CREATE INDEX idx_results_student     ON simulation.student_results(student_id);
CREATE INDEX idx_mastery_student     ON simulation.standard_mastery(student_id);
CREATE INDEX idx_mastery_standard    ON simulation.standard_mastery(standard_id);
CREATE INDEX idx_aq_assessment       ON simulation.assessment_questions(assessment_id);
