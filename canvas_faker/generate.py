"""Orchestrator: dependency-ordered generation across all namespaces."""
from __future__ import annotations

import random
from pathlib import Path

from faker import Faker

from .config import GenerationConfig
from .generators import canvas, canvas_logs, catalog, new_quizzes
from .ids import IdAllocator, Registry
from .messiness import MessinessEngine
from .providers import CanvasProvider


def _get_writer(output: str | Path | None, pg_url: str | None):
    """Return (writer_module, conn) for either SQLite or Postgres."""
    if pg_url:
        from .writers import postgres_writer as writer
        conn = writer.open_db(pg_url)
    else:
        import sqlite3
        from .writers import sqlite_writer as writer
        conn = writer.open_db(output or "cd2.db")
    return writer, conn


def generate_dataset(
    cfg: GenerationConfig,
    output_path: str | Path | None = None,
    *,
    pg_url: str | None = None,
):
    """Generate a full CD2 dataset.

    Writes to SQLite when *output_path* is given (default), or to Postgres
    when *pg_url* is given (a libpq connection string such as
    ``postgresql://user:pass@host:5432/dbname``).

    Returns the open connection.
    """
    cfg = cfg.resolved()
    random.seed(cfg.seed)
    fake = Faker()
    fake.add_provider(CanvasProvider(fake))
    fake.seed_instance(cfg.seed)

    ids = IdAllocator()
    reg = Registry()
    mess = MessinessEngine(cfg.messiness, random.Random(cfg.seed))

    writer, conn = _get_writer(output_path, pg_url)
    writer.create_tables(conn)

    print(f"[canvas] Generating {cfg.n_courses} courses, {cfg.students_per_course} students/course...")
    canvas_rows = canvas.generate(cfg, fake, ids, reg, mess)
    for table, rows in canvas_rows.items():
        writer.insert_rows(conn, "canvas", table, rows)
        print(f"  canvas.{table}: {len(rows)} rows")

    print(f"[canvas_logs] Generating {cfg.web_log_days} days of logs...")
    logs_rows = canvas_logs.generate(cfg, fake, ids, reg, mess)
    for table, rows in logs_rows.items():
        writer.insert_rows(conn, "canvas_logs", table, rows)
        print(f"  canvas_logs.{table}: {len(rows)} rows")

    print(f"[catalog] Generating e-commerce data...")
    catalog_rows = catalog.generate(cfg, fake, ids, reg, mess)
    for table, rows in catalog_rows.items():
        writer.insert_rows(conn, "catalog", table, rows)
        print(f"  catalog.{table}: {len(rows)} rows")

    print(f"[new_quizzes] Generating New Quizzes data...")
    nq_rows = new_quizzes.generate(cfg, fake, ids, reg, mess)
    for table, rows in nq_rows.items():
        writer.insert_rows(conn, "new_quizzes", table, rows)
        print(f"  new_quizzes.{table}: {len(rows)} rows")

    print("Creating indexes...")
    writer.create_indexes(conn)
    return conn
