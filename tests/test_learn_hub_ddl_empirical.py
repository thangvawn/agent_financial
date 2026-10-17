"""Empirical verification test for Learn Hub SQLite DDL & Triggers.
Strict limit: <200 lines.
"""
import re
import sqlite3
from pathlib import Path
import pytest


def extract_architecture_ddl() -> str:
    doc_path = Path("docs/LEARN_HUB_ARCHITECTURE.md")
    assert doc_path.exists(), "LEARN_HUB_ARCHITECTURE.md must exist"
    text = doc_path.read_text(encoding="utf-8")
    sql_blocks = re.findall(r"```sql\s*\n(.*?)\n```", text, re.DOTALL)
    assert len(sql_blocks) >= 6, f"Expected >=6 SQL blocks, found {len(sql_blocks)}"
    return "\n\n".join(sql_blocks)


@pytest.fixture
def memory_db():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA recursive_triggers = ON;")
    ddl = extract_architecture_ddl()
    conn.executescript(ddl)
    yield conn
    conn.close()


def test_all_expected_tables_created(memory_db):
    cursor = memory_db.execute(
        "SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%';"
    )
    names = {row[0] for row in cursor.fetchall()}
    expected_tables = {
        "learning_courses_v2", "learning_course_modules", "learning_course_lessons",
        "learning_user_course_progress", "learning_book_metadata", "learning_book_annotations",
        "learning_book_bookmarks", "learning_book_reading_sessions", "learning_video_metadata",
        "learning_video_chapters", "learning_video_notes", "learning_video_transcripts",
        "learning_bctc_cases", "learning_bctc_case_steps", "learning_bctc_submissions",
        "learning_checkpoints", "learning_verified_events", "learning_progress_receipts",
        "learning_fts5_unified_index"
    }
    for tbl in expected_tables:
        assert tbl in names, f"Table {tbl} not found in database schema"


def test_fts5_triggers_sync_on_insert_update_delete(memory_db):
    memory_db.execute(
        """INSERT INTO learning_bctc_cases (
            case_id, title, slug, ticker, period, industry, difficulty,
            narrative_scenario, financial_cache_path
        ) VALUES (
            'case_01', 'HPG Capex Analysis', 'hpg-capex', 'HPG', '2024-Q3',
            'Thép', 'intermediate', 'Phân tích dòng tiền HPG Dung Quất 2',
            'data/financials/cache/HPG.json'
        )"""
    )
    res = memory_db.execute(
        "SELECT content_id, title FROM learning_fts5_unified_index WHERE learning_fts5_unified_index MATCH '\"Dung Quất\"';"
    ).fetchall()
    assert len(res) == 1
    assert res[0][0] == "case_01"

    memory_db.execute(
        "UPDATE learning_bctc_cases SET narrative_scenario = 'Phân tích dự án mới Hòa Phát' WHERE case_id = 'case_01';"
    )
    res_old = memory_db.execute(
        "SELECT content_id FROM learning_fts5_unified_index WHERE learning_fts5_unified_index MATCH '\"Dung Quất\"';"
    ).fetchall()
    assert len(res_old) == 0
    res_new = memory_db.execute(
        "SELECT content_id FROM learning_fts5_unified_index WHERE learning_fts5_unified_index MATCH '\"Hòa Phát\"';"
    ).fetchall()
    assert len(res_new) == 1

    memory_db.execute("DELETE FROM learning_bctc_cases WHERE case_id = 'case_01';")
    res_del = memory_db.execute(
        "SELECT content_id FROM learning_fts5_unified_index WHERE content_id = 'case_01';"
    ).fetchall()
    assert len(res_del) == 0


def test_courses_trigger_column_scoped_resolves_recursion(memory_db):
    memory_db.execute(
        """INSERT INTO learning_courses_v2 (
            course_id, title, slug, tier, category
        ) VALUES ('c_bug', 'CFA Level 1 CF', 'cfa-cf-bug', 'beginner', 'corporate_finance');"""
    )
    # Empirically verifies: column-scoped trigger executes cleanly without recursion
    memory_db.execute("UPDATE learning_courses_v2 SET title = 'CFA Level 1 CF New' WHERE course_id = 'c_bug';")
    row = memory_db.execute("SELECT title, updated_at FROM learning_courses_v2 WHERE course_id = 'c_bug';").fetchone()
    assert row[0] == "CFA Level 1 CF New"
    assert row[1] is not None


def test_courses_trigger_remediated_resolves_recursion():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA recursive_triggers = ON;")
    ddl = extract_architecture_ddl()
    # Replace recursive trigger with column-scoped trigger
    remediated_ddl = re.sub(
        r"CREATE TRIGGER IF NOT EXISTS trg_courses_v2_updated_at\s+AFTER UPDATE ON learning_courses_v2\s+FOR EACH ROW\s+WHEN OLD\.updated_at = NEW\.updated_at",
        "CREATE TRIGGER IF NOT EXISTS trg_courses_v2_updated_at AFTER UPDATE OF title, slug, description, instructor, tier, category, is_active ON learning_courses_v2 FOR EACH ROW",
        ddl
    )
    conn.executescript(remediated_ddl)
    conn.execute(
        """INSERT INTO learning_courses_v2 (course_id, title, slug) VALUES ('c_fixed', 'CFA Fixed', 'cfa-fixed');"""
    )
    conn.execute("UPDATE learning_courses_v2 SET title = 'CFA Fixed 2' WHERE course_id = 'c_fixed';")
    row = conn.execute("SELECT title, updated_at FROM learning_courses_v2 WHERE course_id = 'c_fixed';").fetchone()
    assert row[0] == "CFA Fixed 2"
    assert row[1] is not None
    conn.close()


def test_foreign_key_and_cascades(memory_db):
    memory_db.execute(
        """INSERT INTO learning_courses_v2 (course_id, title, slug) VALUES ('c_parent', 'Parent Course', 'parent-course');"""
    )
    memory_db.execute(
        """INSERT INTO learning_course_modules (module_id, course_id, sequence_order, title) VALUES ('m_child', 'c_parent', 1, 'Module 1');"""
    )
    with pytest.raises(sqlite3.IntegrityError):
        memory_db.execute(
            """INSERT INTO learning_course_modules (module_id, course_id, sequence_order, title) VALUES ('m_inv', 'nonexistent', 2, 'M2');"""
        )
    memory_db.execute("DELETE FROM learning_courses_v2 WHERE course_id = 'c_parent';")
    count = memory_db.execute("SELECT COUNT(*) FROM learning_course_modules WHERE course_id = 'c_parent';").fetchone()[0]
    assert count == 0


def test_check_constraints(memory_db):
    with pytest.raises(sqlite3.IntegrityError):
        memory_db.execute(
            """INSERT INTO learning_courses_v2 (course_id, title, slug, tier) VALUES ('c_bad', 'Bad', 'bad', 'invalid_tier');"""
        )
    memory_db.execute(
        """INSERT INTO learning_video_metadata (video_id, title, slug, stream_url) VALUES ('v_01', 'Intro', 'intro', 'http://url');"""
    )
    with pytest.raises(sqlite3.IntegrityError):
        memory_db.execute(
            """INSERT INTO learning_video_chapters (chapter_id, video_id, sequence_order, start_seconds, end_seconds, title)
               VALUES ('ch_bad', 'v_01', 1, 100.0, 50.0, 'Inverted timestamps');"""
        )


def test_duplicate_foreign_key_in_progress_receipts(memory_db):
    # Verifies duplicate FK definition on verified_event_id has been removed
    fks = memory_db.execute("PRAGMA foreign_key_list(learning_progress_receipts);").fetchall()
    verified_event_fks = [fk for fk in fks if fk[2] == "learning_verified_events" and fk[3] == "verified_event_id"]
    # There is now exactly 1 foreign key declaration in the doc DDL
    assert len(verified_event_fks) == 1, "Doc DDL must have exactly one foreign key on verified_event_id"
