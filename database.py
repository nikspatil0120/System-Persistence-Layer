import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "interview_sessions.db")


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id   TEXT PRIMARY KEY,
                candidate_id TEXT NOT NULL,
                status       TEXT NOT NULL DEFAULT 'active'
                             CHECK(status IN ('active', 'completed', 'interrupted')),
                start_time   TEXT NOT NULL,
                end_time     TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS transcripts (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT    NOT NULL,
                question   TEXT    NOT NULL,
                answer     TEXT    NOT NULL,
                timestamp  TEXT    NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS evaluations (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT    NOT NULL,
                score      REAL    NOT NULL
                           CHECK(score >= 0 AND score <= 10),
                feedback   TEXT    NOT NULL,
                timestamp  TEXT    NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

    print("[database] Tables initialized successfully.")


init_db()
