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

## Docker

Run canvas-faker in a container — no local Python or venv required. The generated
`.db` is written to a mounted host directory.

### Build

```bash
docker build -t canvas-faker:latest .
```

### Run

Mount a host directory at `/data` and pass `--user` so the output file is owned by
you (not root):

```bash
# Default: small dataset, seed 42 -> ./out/cd2.db
mkdir -p out
docker run --rm --user $(id -u):$(id -g) -v "$PWD/out:/data" canvas-faker:latest

# Override any CLI flag
docker run --rm --user $(id -u):$(id -g) -v "$PWD/out:/data" \
  canvas-faker:latest --scale medium --seed 99 --out /data/medium.db

# Clean data (no messiness)
docker run --rm --user $(id -u):$(id -g) -v "$PWD/out:/data" \
  canvas-faker:latest --clean --out /data/clean.db
```

### Docker Compose

```bash
export UID="$(id -u)" GID="$(id -g)"      # so output is owned by you
docker compose run --rm gen                          # -> ./out/cd2.db
docker compose run --rm gen --scale medium --seed 99 # override flags
```

### Notes

- Multi-stage build: a wheel is built in a `builder` stage, then installed into a
  slim runtime — no build tooling ships in the final image.
- Runs as a non-root user; `/data` is the volume mount point.
- The image entrypoint is the `canvas-faker` CLI, so anything after the image name
  is passed straight through as CLI flags.

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

### Sample Dataset Overview

After running `/cd2-gen small 42 /tmp/demo.db`, you get ~11,000 rows across 121 tables:
- **84 canvas tables**: courses (8), users (76), enrollments, submissions (1,200), grades, discussions
- **3,215 web logs**: request logs with realistic HTTP status codes
- **28 catalog tables**: e-commerce data (~100 rows)
- **8 new_quizzes tables**: quiz data (~160 rows)

### Realistic Messiness Present
- **63 late submissions** (with seconds_late calculated)
- **51 missing submissions** (no grade, no submission)
- **Soft deletes**: some users/enrollments marked as deleted
- **Bounced emails**: a few communication_channels with bounce_count
- **Merged users**: rare duplicate-detection scenarios
- **Partial SIS linkage**: ~30-40% of rows lack sis_source_id

### First 10 Users
```
id  name               sortable_name       created_at            workflow_state
--  -----------------  ------------------  --------------------  --------------
1   Sharon James       James, Sharon       2023-04-02T16:55:25Z  registered    
2   Tricia Valencia    Valencia, Tricia    2022-08-24T17:46:20Z  registered    
3   Joseph Martinez    Martinez, Joseph    2022-12-09T08:22:04Z  registered    
4   Dr. Steven Martin  Martin, Dr. Steven  2022-08-20T01:51:52Z  registered    
5   Sherry Wood        Wood, Sherry        2022-11-05T20:57:43Z  registered    
6   Timothy Hancock    Hancock, Timothy    2023-12-20T02:28:20Z  registered    
7   Jeffrey Rush       Rush, Jeffrey       2023-11-22T09:15:00Z  registered    
8   Shannon Mcclure    Mcclure, Shannon    2023-09-12T05:02:41Z  registered    
9   Sarah Ashley       Ashley, Sarah       2023-03-16T12:15:19Z  registered    
10  Ashley Weiss       Weiss, Ashley       2023-12-14T08:38:57Z  registered
```

### All Courses (8 total)
```
id  name                                course_code  workflow_state
--  ----------------------------------  -----------  --------------
1   Seminar in Marketing                MKT-401-W    available     
2   History of English                  ENGL-499     available     
3   Applied Spanish                     SPAN-201-01  available     
4   Advanced Spanish                    SPAN-202     available     
5   History of Spanish                  SPAN-499     available     
6   Seminar in History                  HIST-202     available     
7   Theory and Practice of Mathematics  MATH-499-H   available     
8   Advanced Education                  EDUC-401-01  available
```

### Submissions with Grades (sample)
```
id  name            title               score  grade  late  missing
--  --------------  ------------------  -----  -----  ----  -------
1   Gregory Flores  Midterm Exam        8.9    B+     0     0      
2   Gregory Flores  Lab Report 2        19.9   C+     0     0      
3   Gregory Flores  Essay 3             6.5    D      0     0      
6   Gregory Flores  Lab Report 6        84.4   B      0     0      
7   Jesus Braun     Midterm Exam        9.7    A      0     0      
9   Jesus Braun     Essay 3             5.6    F      0     0      
10  Jesus Braun     Homework 4          4.3    F      0     0      
11  Jesus Braun     Reading Response 5  16.1   D      0     0
```

### Discussion Posts (sample)
```
id  name               title                          message                                           
--  -----------------  -----------------------------  --------------------------------------------------
1   Kyle Smith         Reflection on Core Vocabulary  Bill though indeed ability difference. Interview...
2   Jeffrey Rush       Reflection on Core Vocabulary  College body big what ground past brother.        
3   Gerald Chavez      Reflection on Core Vocabulary  Page concern most.                                
4   Scott Smith        Reflection on Core Vocabulary  Throw reach person expert. Even material hard ente
5   Keith Rodriguez    Reflection on Core Vocabulary  Technology within sing.                           
6   Raymond Thomas     Reflection on Core Vocabulary  Land someone with spring both into.
```

### Late Submissions (sample, showing seconds_late)
```
id   name             title               score  seconds_late
---  ---------------  ------------------  -----  ------------
29   Gerald Chavez    Reading Response 5  18.1   104610       (29 hours late)
47   Laura Berry      Reading Response 5  15.0   337386       (93+ hours late)
50   Scott Smith      Lab Report 2        19.8   47715        (13+ hours late)
63   Derek Thomas     Essay 3             9.7    140033       (38+ hours late)
147  Kyle Smith       Essay 3             7.8    26081        (7+ hours late)
```

### SQL Queries to Explore

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

-- Missing submissions
SELECT u.name, a.title
FROM canvas__submissions sub
JOIN canvas__assignments a ON a.id = sub.assignment_id
JOIN canvas__users u ON u.id = sub.user_id
WHERE sub.missing = 1;
```

### Quick Inspect with Skills

```bash
# Generate a dataset
/cd2-gen small 42 /tmp/demo.db

# Test integrity
/cd2-test /tmp/demo.db

# Get stats & sample rows
/cd2-inspect /tmp/demo.db

# Query directly
sqlite3 /tmp/demo.db "SELECT COUNT(*) FROM canvas__submissions WHERE late=1;"
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
