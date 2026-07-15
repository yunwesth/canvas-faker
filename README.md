# canvas-faker: Generate Realistic Canvas Data 2 (CD2) Datasets

`canvas-faker` is a Python library that generates fake, referentially-consistent Canvas Data 2 datasets with realistic real-world messiness. Perfect for testing, development, and learning about Canvas LMS data structures.

## Features

- **All 4 CD2 namespaces:** canvas (~84 tables), canvas_logs, new_quizzes, catalog (28 tables)
- **121 tables total** with full foreign-key integrity
- **Realistic messiness:** soft deletes, late/missing submissions, bounced emails, merged users, log noise, partial SIS linkage — all tunable
- **SQLite output:** write directly to `.db` file with proper types and indexes
- **Deterministic generation:** same seed = same data, every time
- **Configurable scale:** small (~200 rows), medium (~4k), large (~40k+)

## Installation

```bash
pip install -e /path/to/01-canvas-faker
```

## Usage

### CLI

```bash
# Generate a small dataset
python -m canvas_faker --out cd2.db --seed 42 --scale small

# Generate with messiness
python -m canvas_faker --out cd2.db --scale medium --messiness 0.5

# Generate clean data (no messiness)
python -m canvas_faker --out cd2.db --scale small --clean
```

### Python API

```python
from canvas_faker import GenerationConfig, generate_dataset

cfg = GenerationConfig(seed=42, scale="small")
conn = generate_dataset(cfg, "cd2.db")
conn.close()
```

Configure messiness:

```python
from canvas_faker import GenerationConfig, MessinessConfig, generate_dataset

cfg = GenerationConfig(
    seed=42,
    scale="small",
    messiness=MessinessConfig(
        intensity=0.3,
        soft_delete=True,
        late_missing=True,
        bounced_email=True,
        merged_users=True,
        # ... per-behavior toggles
    ),
)
conn = generate_dataset(cfg, "cd2.db")
```

## Schema Coverage

### Story Tables (correlated, deep)

**canvas namespace (core student flow):**
- accounts, roles, enrollment_terms, courses, course_sections
- users, pseudonyms, communication_channels
- enrollments, enrollment_states
- assignment_groups, assignments, submissions, submission_comments
- quizzes, quiz_questions, quiz_submissions
- discussion_topics, discussion_entries
- context_modules, context_module_progressions
- scores, grading_periods, grading_standards
- learning_outcomes, learning_outcome_results
- rubrics, rubric_associations, rubric_assessments
- ... and 40+ more

**canvas_logs namespace:**
- web_logs (request logs with masquerading, 4xx/5xx noise)

**new_quizzes namespace:**
- quizzes, quiz_submissions, assignments, assignment_overrides

**catalog namespace:**
- products, orders, order_items, enrollments, payments
- certificates, promotions, carts

### Peripheral Tables (schema-valid, lightly linked)

All remaining 40+ canvas tables populated with realistic values but simpler correlation logic.

## Messiness Engine

Every messiness behavior scales with `intensity` (0.0–1.0, default 0.3). When `enabled=False`, all messiness is disabled regardless of intensity.

**Behaviors (all tunable):**

- **soft_delete** — set `workflow_state='deleted'` on a fraction of rows
- **nulls** — drop optional fields (e.g., `users.avatar_image_url`, `pseudonyms.sis_user_id`)
- **late_missing** — submissions with `late/missing/excused` flags, `late_policy_status`, `seconds_late`
- **bounced_email** — communication_channels with `bounce_count`/`last_bounce_at`, state variants
- **merged_users** — a few users with `merged_into_user_id`, name typos/casing variants
- **dropped_enrollments** — concluded/rejected/deleted enrollments with matching enrollment_states
- **timestamp_mess** — tz spread, `updated_at < created_at`, out-of-order logs
- **log_noise** — 4xx/5xx status codes, masquerading (`real_user_id`), truncated user agents
- **missing_sis** — partial SIS linkage (subset of rows lacking `sis_source_id`/`integration_id`)

## Volume Configuration

Presets for scale (all tunable):

```python
SCALE_PRESETS = {
    "small": dict(
        n_root_accounts=1, n_sub_accounts=3, n_terms=2, n_courses=8,
        students_per_course=25, teachers_per_course=1, sections_per_course=2,
        assignments_per_course=6, quizzes_per_course=2, discussions_per_course=2,
        modules_per_course=3, web_log_days=14, logs_per_student_day=3),
    "medium": dict(...),
    "large": dict(...),
}
```

## Testing

```bash
pytest tests/
```

Verifies:
- **FK integrity:** every FK value resolves to an existing PK
- **Join sanity:** canonical `enrollments ⋈ scores ⋈ users ⋈ courses` works
- **Messiness presence:** soft deletes, late submissions, bounced emails present when enabled
- **Row counts:** tracking config (e.g., students_per_course × n_courses ≈ enrollments)

## Architecture

```
canvas_faker/
  schema.py           # CD2 table→column DSL + SQLite type map
  config.py           # GenerationConfig + MessinessConfig + scale presets
  ids.py              # IdAllocator + Registry (FK tracking)
  providers.py        # Custom Faker providers (course_code, sis_id, letter_grade, etc.)
  messiness.py        # MessinessEngine: all mess transforms
  generate.py         # Orchestrator: dependency-ordered generation
  cli.py              # CLI: python -m canvas_faker
  generators/
    canvas.py         # Canvas namespace (84 tables)
    canvas_logs.py    # Web logs
    catalog.py        # E-commerce (28 tables)
    new_quizzes.py    # New Quizzes (8 tables)
  writers/
    sqlite_writer.py  # CREATE TABLE, bulk INSERT, indexes
```

## Key Design Decisions

1. **SQLite output:** indexed for joins, typed columns, FK foreign_keys=ON for testing
2. **Story tables first:** generate deep, correlated data (enrollments → submissions → scores), then peripheral tables
3. **Messiness at generation time:** avoid post-processing; cleaner, faster
4. **Deterministic + seeded:** reproducible datasets for tests
5. **All namespaces, ~121 tables:** complete schema coverage, even edge tables

## Example: Querying the Generated Data

```sql
-- Student grades (canonical CD2 join)
SELECT u.name, c.course_code, s.current_score, s.final_grade
FROM canvas__enrollments e
JOIN canvas__scores s ON s.enrollment_id = e.id AND s.course_score = 1
JOIN canvas__users u ON u.id = e.user_id
JOIN canvas__courses c ON c.id = e.course_id
WHERE e.type = 'StudentEnrollment'
  AND e.workflow_state = 'active'
ORDER BY u.name;

-- Late submissions
SELECT u.name, a.title, sub.seconds_late
FROM canvas__submissions sub
JOIN canvas__assignments a ON a.id = sub.assignment_id
JOIN canvas__users u ON u.id = sub.user_id
WHERE sub.late = 1
ORDER BY sub.seconds_late DESC;

-- Bounced emails
SELECT u.name, cc.path, cc.bounce_count
FROM canvas__communication_channels cc
JOIN canvas__users u ON u.id = cc.user_id
WHERE cc.workflow_state = 'bounced'
ORDER BY cc.bounce_count DESC;
```

## Future Work (not in v0.1)

- JSONL/CSV/Parquet exporters
- Cloud deployment option (remote data generation)
- Advanced time-series simulation (true course lifecycle)
- Custom data profiles (e.g., "struggling student", "engaged teacher")

## License

MIT

## References

- [Canvas Data 2 Documentation](https://developerdocs.instructure.com/services/dap)
- [Faker Documentation](https://faker.readthedocs.io/)
