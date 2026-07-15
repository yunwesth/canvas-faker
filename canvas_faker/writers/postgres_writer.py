"""Write generated rows to PostgreSQL."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import psycopg2

from ..schema import Column, all_tables, parsed_table, sqlite_table_name


def _col_ddl(col: Column) -> str:
    parts = [f'"{col.name}" {col.pg_type}']
    if col.is_pk and col.code == "pk":
        parts.append("PRIMARY KEY")
    if not col.nullable and not col.is_pk:
        # Only enforce NOT NULL on non-pk non-nullable cols to match SQLite behaviour.
        pass
    return " ".join(parts)


def open_db(dsn: str):
    """Return an open psycopg2 connection."""
    try:
        import psycopg2
    except ImportError as exc:
        raise SystemExit(
            "psycopg2 is required for Postgres output.\n"
            "Install it with: pip install psycopg2-binary"
        ) from exc
    conn = psycopg2.connect(dsn)
    conn.autocommit = False
    return conn


def create_tables(conn) -> None:
    """Create all CD2 tables in the Postgres database (DROP + CREATE for idempotency)."""
    cur = conn.cursor()
    # Collect table names first so we can drop in reverse order (FK safety).
    tbl_names = [sqlite_table_name(ns, tbl) for ns, tbl in all_tables()]
    for tbl_name in reversed(tbl_names):
        cur.execute(f'DROP TABLE IF EXISTS "{tbl_name}" CASCADE;')

    for ns, tbl in all_tables():
        columns = parsed_table(ns, tbl)
        tbl_name = sqlite_table_name(ns, tbl)
        col_ddl = ", ".join(_col_ddl(c) for c in columns)
        cur.execute(f'CREATE TABLE "{tbl_name}" ({col_ddl});')

    conn.commit()
    cur.close()


def create_indexes(conn) -> None:
    """Create indexes on FK columns for join performance."""
    cur = conn.cursor()
    for ns, tbl in all_tables():
        columns = parsed_table(ns, tbl)
        tbl_name = sqlite_table_name(ns, tbl)
        tbl_safe = tbl_name.replace(".", "_")
        for col in columns:
            if col.fk or col.name in ("user_id", "course_id", "enrollment_id"):
                col_safe = col.name.replace("-", "_")
                idx_name = f"idx_{tbl_safe}_{col_safe}"
                cur.execute(
                    f'CREATE INDEX IF NOT EXISTS "{idx_name}" ON "{tbl_name}" ("{col.name}");'
                )
    conn.commit()
    cur.close()


def insert_rows(conn, namespace: str, table: str, rows: list[dict]) -> None:
    """Bulk-insert rows using psycopg2 executemany."""
    if not rows:
        return

    import psycopg2.extras

    tbl_name = sqlite_table_name(namespace, table)
    columns = parsed_table(namespace, table)
    col_names = [c.name for c in columns]

    def _coerce(col: Column, val):
        if val is None:
            return None
        if col.code == "bool":
            return bool(val)
        if col.code == "json" and isinstance(val, list):
            return json.dumps(val)
        if val == "":
            return None
        return val

    col_list = ", ".join(f'"{n}"' for n in col_names)
    placeholders = ", ".join(f"%s" for _ in col_names)
    sql = f'INSERT INTO "{tbl_name}" ({col_list}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'

    data = [
        tuple(_coerce(c, row.get(c.name)) for c in columns)
        for row in rows
    ]
    cur = conn.cursor()
    psycopg2.extras.execute_batch(cur, sql, data, page_size=500)
    conn.commit()
    cur.close()
