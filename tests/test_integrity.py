"""Test suite: FK integrity, join sanity, messiness stats."""
import sqlite3
import tempfile
from pathlib import Path

import pytest

from canvas_faker import GenerationConfig, MessinessConfig, generate_dataset
from canvas_faker.schema import all_tables, parsed_table, sqlite_table_name


@pytest.fixture
def db():
    """Generate a small test dataset and yield the connection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test.db"
        cfg = GenerationConfig(seed=42, scale="small")
        conn = generate_dataset(cfg, path)
        yield conn
        conn.close()


class TestFKIntegrity:
    """Every FK value exists in its referenced table."""

    def test_all_fk_targets_exist(self, db: sqlite3.Connection):
        db.row_factory = sqlite3.Row
        for ns, tbl in all_tables():
            columns = parsed_table(ns, tbl)
            tbl_name = sqlite_table_name(ns, tbl)
            for col in columns:
                if not col.fk:
                    continue
                fns, ftbl = col.fk.split(".")
                ftbl_name = sqlite_table_name(fns, ftbl)
                # Check that every non-null FK value exists
                cursor = db.execute(
                    f'SELECT DISTINCT "{col.name}" FROM "{tbl_name}" '
                    f'WHERE "{col.name}" IS NOT NULL'
                )
                fk_values = set(r[0] for r in cursor)
                if fk_values:
                    cursor = db.execute(f'SELECT id FROM "{ftbl_name}"')
                    pk_values = set(r[0] for r in cursor)
                    missing = fk_values - pk_values
                    assert not missing, (
                        f"{ns}.{tbl}.{col.name} references {ftbl} but found "
                        f"missing PK values: {missing}"
                    )

    def test_all_tables_present(self, db: sqlite3.Connection):
        cursor = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        existing_tables = {r[0] for r in cursor}
        expected = {sqlite_table_name(ns, tbl) for ns, tbl in all_tables()}
        missing = expected - existing_tables
        assert not missing, f"Missing tables: {missing}"
        extra = existing_tables - expected
        assert not extra, f"Unexpected tables: {extra}"


class TestJoinSanity:
    """The canonical CD2 join should return rows."""

    def test_student_grades_join(self, db: sqlite3.Connection):
        db.row_factory = sqlite3.Row
        cursor = db.execute("""
            SELECT u.name, c.name, s.current_score, s.final_grade
            FROM canvas__enrollments e
            JOIN canvas__scores s ON s.enrollment_id = e.id AND s.course_score = 1
            JOIN canvas__users u ON u.id = e.user_id
            JOIN canvas__courses c ON c.id = e.course_id
            WHERE e.type = 'StudentEnrollment'
              AND e.workflow_state = 'active'
            LIMIT 10
        """)
        rows = cursor.fetchall()
        assert len(rows) > 0, "Student grades join returned no rows"


class TestMessiness:
    """Messiness should be present or absent based on config."""

    def test_soft_deletes_present(self, db: sqlite3.Connection):
        cursor = db.execute("SELECT COUNT(*) FROM canvas__users WHERE workflow_state = 'deleted'")
        deleted_count = cursor.fetchone()[0]
        # With intensity 0.3, expect some soft deletes
        assert deleted_count > 0, "No soft deletes found in users (messiness not applied?)"

    def test_clean_mode(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "clean.db"
            cfg = GenerationConfig(
                seed=42, scale="small",
                messiness=MessinessConfig(intensity=0.0, enabled=False),
            )
            conn = generate_dataset(cfg, path)
            cursor = conn.execute("SELECT COUNT(*) FROM canvas__users WHERE workflow_state = 'deleted'")
            deleted_count = cursor.fetchone()[0]
            assert deleted_count == 0, "Clean mode should have no soft deletes"
            conn.close()

    def test_late_submissions_present(self, db: sqlite3.Connection):
        cursor = db.execute("SELECT COUNT(*) FROM canvas__submissions WHERE late = 1")
        late_count = cursor.fetchone()[0]
        assert late_count > 0, "No late submissions found"

    def test_missing_submissions_present(self, db: sqlite3.Connection):
        cursor = db.execute("SELECT COUNT(*) FROM canvas__submissions WHERE missing = 1")
        missing_count = cursor.fetchone()[0]
        assert missing_count > 0, "No missing submissions found"


class TestRowCounts:
    """Row counts should roughly track config."""

    def test_course_count(self, db: sqlite3.Connection):
        cursor = db.execute("SELECT COUNT(*) FROM canvas__courses WHERE workflow_state != 'deleted'")
        count = cursor.fetchone()[0]
        # scale=small has n_courses=8
        assert count >= 8, f"Expected at least 8 courses, got {count}"

    def test_enrollment_count(self, db: sqlite3.Connection):
        cursor = db.execute(
            "SELECT COUNT(*) FROM canvas__enrollments "
            "WHERE type = 'StudentEnrollment' AND workflow_state != 'deleted'"
        )
        count = cursor.fetchone()[0]
        # scale=small: ~8 courses × 25 students = ~200 students
        assert count >= 100, f"Expected at least 100 student enrollments, got {count}"

    def test_submission_count(self, db: sqlite3.Connection):
        cursor = db.execute(
            "SELECT COUNT(*) FROM canvas__submissions WHERE workflow_state != 'deleted'"
        )
        count = cursor.fetchone()[0]
        # ~8 courses × 25 students × 6 assignments = ~1200 submissions (with some missing)
        assert count >= 100, f"Expected at least 100 submissions, got {count}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
