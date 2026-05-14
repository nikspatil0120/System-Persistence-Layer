# Task 18 — Session Persistence Layer

## Overview

This module implements a **persistence layer** for an AI Interview System. It stores and retrieves interview session data using **SQLite** — no external databases, no Docker, no Redis required.

The system allows you to:
- Start a new interview session for a candidate
- Record question-answer transcripts during the interview
- Store evaluation scores and feedback
- Gracefully handle interruptions (e.g., browser close, network drop)
- **Recover a full session** — including all transcripts and evaluations — from the database
- List all sessions for a candidate (session history)
- Poll session status without loading full content

---

## File Structure

```
TASK_18/
├── database.py                     # SQLite connection (context manager) and table creation
├── session_manager.py              # All core session functions
├── main.py                         # FastAPI app and route definitions
├── test_session.py                 # End-to-end test script (happy + error paths)
└── TASK18_SESSION_PERSISTENCE.md   # This documentation file
```

---

## Database Schema

### Table 1: `sessions`

| Column        | Type   | Constraints                                      | Description                                      |
|---------------|--------|--------------------------------------------------|--------------------------------------------------|
| `session_id`  | TEXT   | PRIMARY KEY                                      | Unique session identifier (UUID v4)              |
| `candidate_id`| TEXT   | NOT NULL                                         | Identifier for the candidate                     |
| `status`      | TEXT   | NOT NULL, CHECK IN ('active','completed','interrupted') | Current session state                   |
| `start_time`  | TEXT   | NOT NULL                                         | ISO 8601 timestamp when session started          |
| `end_time`    | TEXT   | nullable                                         | ISO 8601 timestamp when session ended            |

---

### Table 2: `transcripts`

| Column       | Type    | Constraints                          | Description                          |
|--------------|---------|--------------------------------------|--------------------------------------|
| `id`         | INTEGER | PRIMARY KEY AUTOINCREMENT            | Auto-generated row ID                |
| `session_id` | TEXT    | NOT NULL, FOREIGN KEY → sessions     | Links transcript to a session        |
| `question`   | TEXT    | NOT NULL                             | Interview question asked             |
| `answer`     | TEXT    | NOT NULL                             | Candidate's answer                   |
| `timestamp`  | TEXT    | NOT NULL                             | ISO 8601 timestamp of the exchange   |

---

### Table 3: `evaluations`

| Column       | Type    | Constraints                          | Description                          |
|--------------|---------|--------------------------------------|--------------------------------------|
| `id`         | INTEGER | PRIMARY KEY AUTOINCREMENT            | Auto-generated row ID                |
| `session_id` | TEXT    | NOT NULL, FOREIGN KEY → sessions     | Links evaluation to a session        |
| `score`      | REAL    | NOT NULL, CHECK(score >= 0 AND score <= 10) | Numeric score 0–10            |
| `feedback`   | TEXT    | NOT NULL                             | Textual feedback from the evaluator  |
| `timestamp`  | TEXT    | NOT NULL                             | ISO 8601 timestamp of the evaluation |

---

## API Endpoints

### `GET /health`
Server health check.

**Response:**
```json
{ "status": "ok", "version": "1.0.0" }
```

---

### `POST /session/create`
Creates a new interview session.

**Request body:**
```json
{ "candidate_id": "candidate_007" }
```

**Response:**
```json
{ "session_id": "3f2a1b4c-..." }
```

**Errors:** `400` if `candidate_id` is blank.

---

### `POST /session/transcript`
Saves a question-answer pair to the session.

**Request body:**
```json
{
  "session_id": "3f2a1b4c-...",
  "question": "What is a REST API?",
  "answer": "A REST API uses HTTP methods to operate on resources..."
}
```

**Response:** `{ "message": "saved" }`  
**Errors:** `404` if session not found.

---

### `POST /session/evaluation`
Saves a score and feedback for the session.

**Request body:**
```json
{
  "session_id": "3f2a1b4c-...",
  "score": 8.5,
  "feedback": "Good explanation, could add more detail."
}
```

**Response:** `{ "message": "saved" }`  
**Errors:** `404` if session not found. `422` if score is outside 0–10.

---

### `POST /session/complete`
Marks the session as completed and records the end time.

**Request body:** `{ "session_id": "3f2a1b4c-..." }`  
**Response:** `{ "message": "session completed" }`  
**Errors:** `404` if session not found.

---

### `POST /session/interrupt`
Marks the session as interrupted (e.g., browser closed). Session data is preserved.

**Request body:** `{ "session_id": "3f2a1b4c-..." }`  
**Response:** `{ "message": "session interrupted" }`  
**Errors:** `404` if session not found.

---

### `GET /session/{session_id}`
Retrieves the full session including all transcripts and evaluations.  
This is the **primary recovery endpoint**.

**Response:**
```json
{
  "session_id": "3f2a1b4c-...",
  "candidate_id": "candidate_007",
  "status": "interrupted",
  "start_time": "2026-05-14T10:00:00.000000",
  "end_time": "2026-05-14T10:25:00.000000",
  "transcripts": [
    { "question": "...", "answer": "...", "timestamp": "..." }
  ],
  "evaluations": [
    { "score": 8.5, "feedback": "...", "timestamp": "..." }
  ]
}
```

**Errors:** `404` if session not found.

---

### `GET /session/{session_id}/status`
Returns a lightweight status summary without loading all content.  
Useful for polling or heartbeat checks.

**Response:**
```json
{
  "session_id": "3f2a1b4c-...",
  "status": "active",
  "transcript_count": 3,
  "evaluation_count": 2,
  "start_time": "2026-05-14T10:00:00.000000",
  "end_time": null
}
```

**Errors:** `404` if session not found.

---

### `GET /sessions/{candidate_id}`
Returns all sessions for a candidate, most recent first.

**Response:**
```json
[
  {
    "session_id": "3f2a1b4c-...",
    "status": "interrupted",
    "start_time": "2026-05-14T10:00:00.000000",
    "end_time": "2026-05-14T10:25:00.000000"
  }
]
```

Returns `[]` if no sessions exist for that candidate.

---

## Error Handling

| Scenario                          | HTTP Status | Detail                                  |
|-----------------------------------|-------------|-----------------------------------------|
| Session not found                 | `404`       | `"Session '<id>' not found."`           |
| Empty `candidate_id`              | `400`       | `"'candidate_id' cannot be empty."`     |
| Score outside 0–10                | `422`       | Pydantic validation error               |
| Missing required field in body    | `422`       | Pydantic validation error               |

---

## Recovery Flow

Step-by-step walkthrough of what happens when a session is interrupted and resumed:

```
1. Candidate starts interview
      → POST /session/create
      → session created, status = "active"

2. Interview proceeds
      → POST /session/transcript  (one call per Q&A exchange)
      → POST /session/evaluation  (one call per scored answer)
      → All data written to SQLite immediately — nothing is buffered

3. Browser closes unexpectedly
      → POST /session/interrupt
      → status = "interrupted", end_time recorded
      → (Can also be triggered by a server-side heartbeat timeout)

4. Candidate reconnects / admin reviews
      → GET /session/{session_id}
      → Returns full session dict with all saved transcripts and evaluations
      → Nothing is lost — all data was persisted at write time

5. Session continues or is reviewed
      → New transcripts/evaluations can be appended to the same session_id
      → When finished: POST /session/complete → status = "completed"

6. Candidate history
      → GET /sessions/{candidate_id}
      → Returns all sessions for that candidate, most recent first
```

---

## How to Run

### 1. Install dependencies

```bash
pip install fastapi uvicorn
```

### 2. Start the API server

Run from inside the `TASK_18/` directory:

```bash
uvicorn main:app --reload
```

Server starts at: `http://127.0.0.1:8000`  
Interactive API docs: `http://127.0.0.1:8000/docs`

---

### 3. Run the test script

Run from inside the `TASK_18/` directory (no server needed):

```bash
python test_session.py
```

Covers 11 test cases: 7 happy-path steps and 4 error-path checks.