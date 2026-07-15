"""Orchestrator: dependency-ordered generation across all namespaces."""
from __future__ import annotations

import random
import sqlite3
from pathlib import Path

from faker import Faker

from .config import GenerationConfig
from .generators import canvas, canvas_logs, catalog, new_quizzes
from .ids import IdAllocator, Registry
from .messiness import MessinessEngine
from .providers import CanvasProvider
from .writers.sqlite_writer import create_indexes, create_tables, insert_rows, open_db


def generate_dataset(cfg: GenerationConfig, output_path: str | Path) -> sqlite3.Connection:
    """Generate a full CD2 dataset and write to SQLite.

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

    conn = open_db(output_path)
    create_tables(conn)

    print(f"[canvas] Generating {cfg.n_courses} courses, {cfg.students_per_course} students/course...")
    canvas_rows = canvas.generate(cfg, fake, ids, reg, mess)
    for table, rows in canvas_rows.items():
        insert_rows(conn, "canvas", table, rows)
        print(f"  canvas.{table}: {len(rows)} rows")

    print(f"[canvas_logs] Generating {cfg.web_log_days} days of logs...")
    logs_rows = canvas_logs.generate(cfg, fake, ids, reg, mess)
    for table, rows in logs_rows.items():
        insert_rows(conn, "canvas_logs", table, rows)
        print(f"  canvas_logs.{table}: {len(rows)} rows")

    print(f"[catalog] Generating e-commerce data...")
    catalog_rows = catalog.generate(cfg, fake, ids, reg, mess)
    for table, rows in catalog_rows.items():
        insert_rows(conn, "catalog", table, rows)
        print(f"  catalog.{table}: {len(rows)} rows")

    print(f"[new_quizzes] Generating New Quizzes data...")
    nq_rows = new_quizzes.generate(cfg, fake, ids, reg, mess)
    for table, rows in nq_rows.items():
        insert_rows(conn, "new_quizzes", table, rows)
        print(f"  new_quizzes.{table}: {len(rows)} rows")

    print("Creating indexes...")
    create_indexes(conn)
    conn.commit()
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn
