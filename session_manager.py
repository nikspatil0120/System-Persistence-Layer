import uuid
import sqlite3
from datetime import datetime
from database import get_db


def _now() -> str:
    return datetime.now().isoformat()


def _require_session(conn, session_id: str) -> sqlite3.Row:
    row = conn.execute(
        "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
    ).fetchone()
    if row is None:
        raise ValueError(f"Session '{session_id}' not found.")
    return row


def _require_nonempty(value: str, field: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"'{field}' cannot be empty.")
    return stripped


def create_session(candidate_id: str) -> str:
    candidate_id = _require_nonempty(candidate_id, "candidate_id")
    session_id = str(uuid.uuid4())

    with get_db() as conn:
        conn.execute(
            "INSERT INTO sessions (session_id, candidate_id, status, start_time) VALUES (?, ?, 'active', ?)",
            (session_id, candidate_id, _now()),
        )

    return session_id


def save_transcript(session_id: str, question: str, answer: str) -> None:
    session_id = _require_nonempty(session_id, "session_id")
    question   = _require_nonempty(question,   "question")
    answer     = _require_nonempty(answer,     "answer")

    with get_db() as conn:
        _require_session(conn, session_id)
        conn.execute(
            "INSERT INTO transcripts (session_id, question, answer, timestamp) VALUES (?, ?, ?, ?)",
            (session_id, question, answer, _now()),
        )


def save_evaluation(session_id: str, score: float, feedback: str) -> None:
    session_id = _require_nonempty(session_id, "session_id")
    feedback   = _require_nonempty(feedback,   "feedback")

    if not (0 <= score <= 10):
        raise ValueError(f"Score must be between 0 and 10, got {score}.")

    with get_db() as conn:
        _require_session(conn, session_id)
        conn.execute(
            "INSERT INTO evaluations (session_id, score, feedback, timestamp) VALUES (?, ?, ?, ?)",
            (session_id, score, feedback, _now()),
        )


def load_session(session_id: str) -> dict:
    with get_db() as conn:
        session_row = _require_session(conn, session_id)

        transcripts = [
            {"question": row["question"], "answer": row["answer"], "timestamp": row["timestamp"]}
            for row in conn.execute(
                "SELECT question, answer, timestamp FROM transcripts WHERE session_id = ? ORDER BY id ASC",
                (session_id,),
            ).fetchall()
        ]

        evaluations = [
            {"score": row["score"], "feedback": row["feedback"], "timestamp": row["timestamp"]}
            for row in conn.execute(
                "SELECT score, feedback, timestamp FROM evaluations WHERE session_id = ? ORDER BY id ASC",
                (session_id,),
            ).fetchall()
        ]

    return {
        "session_id":   session_row["session_id"],
        "candidate_id": session_row["candidate_id"],
        "status":       session_row["status"],
        "start_time":   session_row["start_time"],
        "end_time":     session_row["end_time"],
        "transcripts":  transcripts,
        "evaluations":  evaluations,
    }


def complete_session(session_id: str) -> None:
    with get_db() as conn:
        _require_session(conn, session_id)
        conn.execute(
            "UPDATE sessions SET status = 'completed', end_time = ? WHERE session_id = ?",
            (_now(), session_id),
        )


def interrupt_session(session_id: str) -> None:
    with get_db() as conn:
        _require_session(conn, session_id)
        conn.execute(
            "UPDATE sessions SET status = 'interrupted', end_time = ? WHERE session_id = ?",
            (_now(), session_id),
        )


def list_sessions(candidate_id: str) -> list[dict]:
    candidate_id = _require_nonempty(candidate_id, "candidate_id")

    with get_db() as conn:
        rows = conn.execute(
            "SELECT session_id, status, start_time, end_time FROM sessions WHERE candidate_id = ? ORDER BY start_time DESC",
            (candidate_id,),
        ).fetchall()

    return [
        {"session_id": row["session_id"], "status": row["status"], "start_time": row["start_time"], "end_time": row["end_time"]}
        for row in rows
    ]


def get_session_status(session_id: str) -> dict:
    with get_db() as conn:
        session_row = _require_session(conn, session_id)

        transcript_count = conn.execute(
            "SELECT COUNT(*) FROM transcripts WHERE session_id = ?", (session_id,)
        ).fetchone()[0]

        evaluation_count = conn.execute(
            "SELECT COUNT(*) FROM evaluations WHERE session_id = ?", (session_id,)
        ).fetchone()[0]

    return {
        "session_id":       session_row["session_id"],
        "status":           session_row["status"],
        "transcript_count": transcript_count,
        "evaluation_count": evaluation_count,
        "start_time":       session_row["start_time"],
        "end_time":         session_row["end_time"],
    }
