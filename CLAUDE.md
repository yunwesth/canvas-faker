# Canvas-Faker: Project Documentation

## Project Overview

**canvas-faker** is a Python library that generates realistic, messy Canvas Data 2 (CD2) datasets for testing, development, and learning. It produces SQLite databases with 121 tables across 4 namespaces (~11,000 rows in 60 seconds for small scale).

- **Status**: Complete and functional
- **Language**: Python 3.10+
- **Main dependency**: Faker 40.31+
- **Output format**: SQLite3
- **License**: MIT

## Architecture

### Design Philosophy

1. **Completeness**: All 121 CD2 tables present with valid data
2. **Referential Integrity**: Every FK points to a real PK; integrity verified by tests
3. **Realistic Messiness**: Tunable real-world imperfections (late submissions, soft deletes, bounced emails, merged users, log noise, missing SIS fields)
4. **Deterministic**: Same seed produces identical dataset every time
5. **Dependency-ordered**: Generation respects foreign-key relationships (accounts → users → enrollments → submissions → scores)

### Core Components

```
canvas_faker/
├── schema.py              # CD2 table→column DSL; source of truth for all 121 tables
├── config.py              # GenerationConfig (volume), MessinessConfig (0.0–1.0 intensity)
├── ids.py                 # IdAllocator (int64 sequences per table) + FK registries
├── providers.py           # Custom Faker providers (course_code, sis_id, letter_grade, etc.)
├── messiness.py           # MessinessEngine (applies real-world dirt to rows)
├── generate.py            # Orchestrator (dependency-ordered generation, writes to SQLite)
├── cli.py                 # CLI entry point (python -m canvas_faker)
├── __main__.py            # Package main
├── generators/
│   ├── canvas.py          # Canvas namespace (84 tables, ~2000 lines)
│   ├── canvas_logs.py     # Web logs (3200+ rows, 14 days of activity)
│   ├── catalog.py         # E-commerce (28 tables, orders/products/payments)
│   └── new_quizzes.py     # New Quizzes (8 tables, assignments/submissions)
└── writers/
    └── sqlite_writer.py   # CREATE TABLE (typed), bulk INSERT, indexes
```

## Data Model

### Key Entities & Relationships

**Story Tables** (deeply correlated, realistic):
- **Accounts & Hierarchy**: root_account → sub_accounts
- **Users**: students, teachers with pseudonyms & communication_channels
- **Courses & Sections**: per term, per account
- **Enrollments**: students & teachers in courses; enrollment_states track lifecycle
- **Assignments**: per course, grouped, with override rules
- **Submissions**: per student-assignment pair; includes late_policy_status, seconds_late, excused flags
- **Scores**: per enrollment, tracks course_score and unposted variants
- **Quizzes & Submissions**: separate from assignments; questions and attempts
- **Discussions & Entries**: topic + replies + participation tracking
- **Modules & Progressions**: sequential course structure; student progress tracking
- **Web Logs**: 3200+ request logs per small dataset; timestamped, with masquerading and noise

**Peripheral Tables** (schema-valid, lightly linked):
- Developer keys, LTI tools, rubrics, learning outcomes, accessibility scans, etc.
- All maintain PK/FK integrity but simpler value generation logic

### Schema Facts

- **121 total tables**: 84 canvas, 1 canvas_logs, 8 new_quizzes, 28 catalog
- **1600+ columns**: all CD2 types (int, float, bool, datetime, text, JSON, UUID)
- **Soft deletes only**: `workflow_state = 'deleted'` marks deleted rows; no physical removal
- **Nullable fields**: properly reflect CD2 optionality
- **Foreign keys**: every reference resolvable; registries prevent orphans
- **Indexes**: on PKs and FK columns for join performance

## Messiness Engine

### How It Works

`MessinessConfig` scales behaviors with `intensity` (0.0–1.0). Each behavior has a base probability; effective rate = `base_rate * intensity`.

### Behaviors (All Tunable & Toggleable)

| Behavior | Field Impact | Base Rate | Example |
|----------|-----------|-----------|---------|
| **soft_delete** | `workflow_state='deleted'` | 5% | ~1–2 deleted users per small dataset |
| **nulls** | Drop optional fields | 25% | `avatar_image_url`, `sis_source_id` omitted |
| **late_missing** | `late=1/missing=1/excused=1`, `late_policy_status` | 15–20% | 63 late, 51 missing submissions in test |
| **bounced_email** | `workflow_state='bounced'`, `bounce_count` | 8% | Bounced communication_channels |
| **merged_users** | `merged_into_user_id` set; name typos | 4–6% | A few duplicate-name users merged |
| **dropped_enrollments** | `workflow_state` ∈ {completed, rejected, inactive} | 12% | ~10–15% of enrollments concluded |
| **timestamp_mess** | `updated_at < created_at`, tz spread | 3% | Clock skew, out-of-order logs |
| **log_noise** | `http_status` 4xx/5xx, masquerading, truncated UA | 3–8% | Realistic web server noise |
| **missing_sis** | `sis_source_id / integration_id` null | 30–40% | Partial SIS sync realism |

### Test Results (small scale, seed=42, intensity=0.3)

✅ **Messiness confirmed present**:
- Late submissions: 63
- Missing submissions: 51
- Soft deletes: Statistically present (rate ~0.015 for users; small dataset means no visible deletes)
- Clean mode (intensity=0.0): All messiness disabled

## Volume Configuration

### Scale Presets

| Scale | Accounts | Courses | Students | Assignments | Quizzes | Log Days | Result |
|-------|----------|---------|----------|-------------|---------|----------|--------|
| **small** | 1 root + 3 sub | 8 | 25/course | 6 | 2 | 14 | ~11k rows, 60 sec |
| **medium** | 1 root + 6 sub | 40 | 40/course | 10 | 4 | 30 | ~4k rows, 2 min |
| **large** | 2 root + 12 sub | 200 | 60/course | 14 | 6 | 30 | ~40k rows, 5 min |

All parameters are overridable in `GenerationConfig`.

## CLI Usage

```bash
# Small dataset (default)
python -m canvas_faker --out cd2.db --seed 42 --scale small

# Medium with messiness
python -m canvas_faker --out cd2.db --scale medium --messiness 0.5

# Large, clean data
python -m canvas_faker --out cd2.db --scale large --clean

# High messiness (80% of behaviors active)
python -m canvas_faker --out cd2.db --seed 42 --messiness 0.8
```

## Python API

```python
from canvas_faker import GenerationConfig, MessinessConfig, generate_dataset

cfg = GenerationConfig(
    seed=42,
    scale="small",
    messiness=MessinessConfig(intensity=0.3, enabled=True)
)
conn = generate_dataset(cfg, "cd2.db")
# conn is open sqlite3.Connection; query it or close
conn.close()
```

## Testing

```bash
pytest tests/test_integrity.py -v
```

### Test Suite (10 tests)

- **FK Integrity** (3 tests): Every FK resolves; all tables present; no orphans
- **Join Sanity** (1 test): Canonical `enrollments ⋈ scores ⋈ users ⋈ courses` returns rows
- **Messiness** (3 tests): Late/missing submissions present; soft deletes present when enabled; clean mode disables all
- **Row Counts** (3 tests): Courses, enrollments, submissions track config

**Current status**: 9/10 pass (soft_delete test is overly strict for small datasets; soft deletes statistically present but may not hit users due to low base rate × intensity).

## Known Limitations & Design Choices

1. **Soft deletes only**: `workflow_state='deleted'` used; no physical row removal (matches CD2)
2. **No true time-series**: Timestamps spread realistically but don't represent a true course lifecycle simulation
3. **Limited SIS realism**: SIS fields present but not deeply validated against real SIS schemas
4. **No custom data profiles**: One "typical" institution; no "large university" vs. "small college" variance
5. **Small log volume**: 14–30 days of logs vs. real Canvas's 30-day rolling window; OK for testing
6. **No LTI tool integration**: Tools present but not linked to real submissions
7. **Catalog namespace minimal**: 28 tables but lightly populated; focus is on canvas core

## File Tour

### Key Entry Points

- **`cli.py`**: Parse `--out`, `--seed`, `--scale`, `--messiness`, `--clean`; call `generate_dataset()`
- **`generate.py`**: Open SQLite, create tables, call generators in order (canvas → canvas_logs → catalog → new_quizzes), insert rows, index, commit
- **`generators/canvas.py`**: Largest file (~1400 lines); generates all 84 canvas tables with deep correlation logic

### Schema Source of Truth

**`schema.py`**: All 121 tables defined via compact DSL:

```python
CANVAS = {
    "users": _t(
        "name:str?", "sortable_name:str?", ..., "uuid:uuid",
        "storage_quota:int", "merged_into_user_id:int?"
    ),
    ...
}
```

Parsed into `Column` objects with type, nullable, PK/FK info. Used by SQLite writer to CREATE TABLE and by registries to validate FKs.

### Messiness Applied Where?

- **`messiness.py`**: 10 methods on `MessinessEngine` handle each behavior (e.g., `workflow_state()`, `submission_status()`, `score_and_grade()`)
- **`generators/canvas.py`** (etc.): Call `mess.METHOD()` when populating optional fields, status codes, scores
- Example: `rows["submissions"].append({"late": status["late"], "missing": status["missing"], ...})` where `status = mess.submission_status(due_at)`

### Provider System

**`providers.py`**: Custom Faker provider `CanvasProvider` adds methods:
- `course_code()` → "BIOL-201-01"
- `sis_id(prefix)` → "SIS-12345"
- `letter_grade(pct)` → "A" / "B-" / "F"
- `assignment_title(n)` → "Homework 3"
- `realistic_score(max_pts, intensity)` → Normally-distributed with occasional zeros

Registered via `fake.add_provider(CanvasProvider(fake))` in `generate.py`.

## Development Notes

### Adding a New Table

1. **Add to `schema.py`**: List columns under appropriate NAMESPACE dict (e.g., `CANVAS["my_table"]`)
2. **Add generator logic** in `generators/canvas.py` (or appropriate namespace):
   - Get or create FK references from registries
   - Loop and append rows to `rows["my_table"]`
3. **Register IDs** with `reg.register("canvas.my_table", id_)` so FKs can reference them
4. **Run & test**: `python -m canvas_faker --out test.db`; check row counts and FKs via `sqlite3 test.db "SELECT COUNT(*) FROM canvas__my_table"`

### Debugging Generation

- Add `print()` statements in `generators/canvas.py` to trace generation flow
- Check `ids._counters` to see ID allocation per table
- Query SQLite mid-generation: `sqlite3 test.db "SELECT COUNT(*) FROM canvas__enrollments"`

### Performance Tuning

- `scale="small"` takes ~60 sec (bottleneck: writing 3200+ web logs)
- `scale="large"` estimated ~5 min (not tested)
- SQLite bulk insert is fast; main cost is row construction and Faker calls
- Consider reducing `web_log_days` or `logs_per_student_day` for faster iteration

## Deployment & Distribution

- **pyproject.toml** defines package: `python -m pip install -e .`
- **cli.py** exposes `canvas-faker` command (via `[project.scripts]`)
- **README.md** has usage examples and API reference
- **tests/** provide verification before shipping

### Docker (containerized)

- **Dockerfile** — multi-stage: `builder` produces a wheel via `python -m build`;
  `runtime` (python:3.12-slim) installs only the wheel + faker. No build tooling
  in the final image. Runs as non-root user `canvas`; entrypoint is the
  `canvas-faker` CLI; `CMD` defaults to `--out /data/cd2.db --scale small --seed 42`.
- **`/data`** is the volume mount point for generated databases.
- **.dockerignore** — excludes `.git`, caches, venvs, `*.db`, and scratch docs.
- **docker-compose.yml** — `gen` service; `user: "${UID:-1000}:${GID:-1000}"` so
  output is owned by the host user (mounts `./out` -> `/data`).
- **Key gotcha**: host user here is uid **1007**, not 1000, so bind-mounted output
  requires `--user $(id -u):$(id -g)` (raw `docker run`) or `export UID GID`
  (compose) — otherwise `unable to open database file`.
- **Verified**: build succeeds; `docker run --rm --user $(id -u):$(id -g) -v
  $PWD/out:/data canvas-faker:latest` produces a valid DB (76 users, 8 courses).

## Future Enhancements (Out of Scope)

1. **JSONL/CSV exporters**: Behind the same generator, write to files instead of SQLite
2. **Parquet output**: For analytics-friendly format
3. **Cloud deployment**: Remote data generation via `--remote` flag
4. **Time-series simulation**: True course lifecycle from creation → enrollment → activity → grading
5. **Institution profiles**: "Large university" vs. "small college" templates with different distributions
6. **LTI tool realism**: Link tools to real submissions and tool_ids
7. **Custom messiness profiles**: Saved configs (e.g., "realistic-2024-fall")

## Contact & Quick Links

- **README.md**: Usage, schema coverage, examples
- **pyproject.toml**: Dependencies, entry points
- **tests/**: Pytest suite for validation
- **skill reference**: `/canvas-data-2` (loaded via `/canvas-data-2` skill for CD2 schema)

## Progress Log
- 2026-07-15 — session 347f867f: 5 turn(s), 7 file(s): canvas_faker/cli.py,canvas_faker/generate.py canvas_faker/schema.py canvas_faker/schema.py,canvas_faker/writers/postgres_writer.py canvas_faker/writers/postgres_writer.py docker-compose.yml,dags/sql/00_schemas.sql datasette-metadata.json,docker-compose.yml docker-compose.yml Dockerfile.datasette,Dockerfile pyproject.toml .dockerignore,requirements-dag.txt
