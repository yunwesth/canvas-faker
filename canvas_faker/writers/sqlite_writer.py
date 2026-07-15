"""Write generated rows to SQLite."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ..schema import Column, all_tables, parsed_table, sqlite_table_name


_CREATE_TMPL = "CREATE TABLE IF NOT EXISTS {name} ({cols});"
_INDEX_TMPL = "CREATE INDEX IF NOT EXISTS idx_{tbl}_{col} ON {tbl} ({col});"


def _col_ddl(col: Column) -> str:
    parts = [f'"{col.name}" {col.sqlite_type}']
    if col.is_pk and col.code == "pk":
        parts.append("PRIMARY KEY")
    return " ".join(parts)


def create_tables(conn: sqlite3.Connection) -> None:
    """Create all CD2 tables in the SQLite database."""
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=OFF;")

    for ns, tbl in all_tables():
        columns = parsed_table(ns, tbl)
        tbl_name = sqlite_table_name(ns, tbl)
        col_ddl = ", ".join(_col_ddl(c) for c in columns)
        conn.execute(_CREATE_TMPL.format(name=f'"{tbl_name}"', cols=col_ddl))

    conn.commit()


def create_indexes(conn: sqlite3.Connection) -> None:
    """Create indexes on FK columns for join performance."""
    for ns, tbl in all_tables():
        columns = parsed_table(ns, tbl)
        tbl_name = sqlite_table_name(ns, tbl)
        for col in columns:
            if col.fk or col.name in ("user_id", "course_id", "enrollment_id"):
                idx_col_safe = col.name.replace("-", "_")
                tbl_safe = tbl_name.replace(".", "_")
                conn.execute(
                    _INDEX_TMPL.format(
                        tbl=f'"{tbl_name}"',
                        col=f'"{col.name}"',
                        idx=f"idx_{tbl_safe}_{idx_col_safe}",
                    ).replace(
                        "CREATE INDEX IF NOT EXISTS idx_",
                        f"CREATE INDEX IF NOT EXISTS idx_{tbl_safe}_{idx_col_safe} ON \"{tbl_name}\" (\"{col.name}\"); --",
                    )
                )
    conn.commit()


def insert_rows(
    conn: sqlite3.Connection,
    namespace: str,
    table: str,
    rows: list[dict],
) -> None:
    """Bulk-insert rows into a table. list[str] values are JSON-encoded."""
    if not rows:
        return
    tbl_name = sqlite_table_name(namespace, table)
    columns = parsed_table(namespace, table)
    col_names = [c.name for c in columns]

    def _coerce(col: Column, val):
        if val is None:
            return None
        if col.code == "bool":
            return 1 if val else 0
        if col.code == "json" and isinstance(val, list):
            return json.dumps(val)
        return val

    placeholders = ", ".join("?" for _ in col_names)
    col_list = ", ".join(f'"{n}"' for n in col_names)
    sql = f'INSERT OR IGNORE INTO "{tbl_name}" ({col_list}) VALUES ({placeholders})'

    data = [
        tuple(_coerce(c, row.get(c.name)) for c in columns)
        for row in rows
    ]
    conn.executemany(sql, data)


def open_db(path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=OFF;")
    return conn
