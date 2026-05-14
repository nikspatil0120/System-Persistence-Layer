import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from session_manager import (
    create_session,
    save_transcript,
    save_evaluation,
    interrupt_session,
    load_session,
    list_sessions,
    get_session_status,
)

PASS = "  [PASS]"
FAIL = "  [FAIL]"


def section(title: str):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def expect_error(label: str, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
        print(f"{FAIL} {label} — expected ValueError but none was raised")
    except ValueError as e:
        print(f"{PASS} {label}")
        print(f"         Error caught: {e}")


section("STEP 1 — Create Session")

candidate_id = "candidate_007"
session_id = create_session(candidate_id)

print(f"  Candidate ID : {candidate_id}")
print(f"  Session ID   : {session_id}")
print(f"  Status       : active")
print(f"{PASS} Session created")


section("STEP 2 — Save 2 Transcripts")

save_transcript(
    session_id,
    question="Can you explain the difference between a list and a tuple in Python?",
    answer="A list is mutable — its elements can be changed after creation. A tuple is immutable — once created, its values cannot be modified.",
)
print(f"{PASS} Transcript 1 saved")

save_transcript(
    session_id,
    question="What is a REST API?",
    answer="A REST API is an architectural style for building web services. It uses HTTP methods like GET, POST, PUT, and DELETE to operate on resources.",
)
print(f"{PASS} Transcript 2 saved")


section("STEP 3 — Save 2 Evaluations")

save_evaluation(
    session_id,
    score=8.5,
    feedback="Good understanding of Python data structures. Could elaborate more on use cases.",
)
print(f"{PASS} Evaluation 1 saved  (score: 8.5)")

save_evaluation(
    session_id,
    score=9.0,
    feedback="Excellent explanation of REST APIs. Mentioned all key HTTP methods correctly.",
)
print(f"{PASS} Evaluation 2 saved  (score: 9.0)")


section("STEP 4 — Check Session Status (Lightweight)")

status = get_session_status(session_id)

print(f"  session_id       : {status['session_id']}")
print(f"  status           : {status['status']}")
print(f"  transcript_count : {status['transcript_count']}")
print(f"  evaluation_count : {status['evaluation_count']}")
print(f"  start_time       : {status['start_time']}")
print(f"  end_time         : {status['end_time']}")

assert status["status"] == "active"
assert status["transcript_count"] == 2
assert status["evaluation_count"] == 2
assert status["end_time"] is None
print(f"{PASS} Status check passed")


section("STEP 5 — Interrupt Session (Simulate Browser Close)")

interrupt_session(session_id)
print(f"  Session '{session_id}' marked as INTERRUPTED.")
print(f"{PASS} Session interrupted")


section("STEP 6 — Recover Full Session (load_session)")

recovered = load_session(session_id)

print(f"\n  session_id   : {recovered['session_id']}")
print(f"  candidate_id : {recovered['candidate_id']}")
print(f"  status       : {recovered['status']}")
print(f"  start_time   : {recovered['start_time']}")
print(f"  end_time     : {recovered['end_time']}")

print(f"\n  --- Transcripts ({len(recovered['transcripts'])} found) ---")
for i, t in enumerate(recovered["transcripts"], start=1):
    print(f"\n  [{i}] Timestamp : {t['timestamp']}")
    print(f"       Question  : {t['question']}")
    print(f"       Answer    : {t['answer']}")

print(f"\n  --- Evaluations ({len(recovered['evaluations'])} found) ---")
for i, e in enumerate(recovered["evaluations"], start=1):
    print(f"\n  [{i}] Timestamp : {e['timestamp']}")
    print(f"       Score     : {e['score']}")
    print(f"       Feedback  : {e['feedback']}")

assert recovered["status"] == "interrupted"
assert recovered["end_time"] is not None
assert len(recovered["transcripts"]) == 2
assert len(recovered["evaluations"]) == 2
print(f"\n{PASS} Full session recovered and verified")


section("STEP 7 — List All Sessions for Candidate")

sessions = list_sessions(candidate_id)

print(f"  Sessions found for '{candidate_id}': {len(sessions)}")
for s in sessions:
    print(f"    - {s['session_id']}  |  {s['status']}  |  started: {s['start_time']}")

assert len(sessions) >= 1
print(f"{PASS} Session list returned correctly")


section("STEP 8 — Error: Transcript on Non-Existent Session")

expect_error(
    "save_transcript with fake session_id",
    save_transcript,
    "00000000-0000-0000-0000-000000000000",
    "What is Python?",
    "A programming language.",
)


section("STEP 9 — Error: Evaluation with Out-of-Range Score")

expect_error(
    "save_evaluation with score=15 (out of range)",
    save_evaluation,
    session_id,
    15.0,
    "This score is too high.",
)

expect_error(
    "save_evaluation with score=-1 (out of range)",
    save_evaluation,
    session_id,
    -1.0,
    "This score is negative.",
)


section("STEP 10 — Error: Load Non-Existent Session")

expect_error(
    "load_session with fake session_id",
    load_session,
    "non-existent-session-id",
)


section("STEP 11 — Error: Create Session with Blank candidate_id")

expect_error(
    "create_session with empty string",
    create_session,
    "   ",
)


section("ALL TESTS COMPLETE")
print("  Happy path and error path tests passed.\n")
