from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from session_manager import (
    create_session,
    save_transcript,
    save_evaluation,
    complete_session,
    interrupt_session,
    load_session,
    list_sessions,
    get_session_status,
)

app = FastAPI(
    title="AI Interview Session Persistence API",
    description="Stores and retrieves interview session data using SQLite. Supports full session recovery after interruption.",
    version="1.0.0",
)


class CreateSessionRequest(BaseModel):
    candidate_id: str = Field(..., min_length=1)


class TranscriptRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    question:   str = Field(..., min_length=1)
    answer:     str = Field(..., min_length=1)


class EvaluationRequest(BaseModel):
    session_id: str   = Field(..., min_length=1)
    score:      float = Field(..., ge=0, le=10)
    feedback:   str   = Field(..., min_length=1)


class SessionActionRequest(BaseModel):
    session_id: str = Field(..., min_length=1)


class TranscriptItem(BaseModel):
    question:  str
    answer:    str
    timestamp: str


class EvaluationItem(BaseModel):
    score:     float
    feedback:  str
    timestamp: str


class SessionResponse(BaseModel):
    session_id:   str
    candidate_id: str
    status:       str
    start_time:   str
    end_time:     Optional[str]
    transcripts:  list[TranscriptItem]
    evaluations:  list[EvaluationItem]


class SessionStatusResponse(BaseModel):
    session_id:       str
    status:           str
    transcript_count: int
    evaluation_count: int
    start_time:       str
    end_time:         Optional[str]


class SessionSummary(BaseModel):
    session_id: str
    status:     str
    start_time: str
    end_time:   Optional[str]


@app.get("/health", tags=["Utility"])
def health_check():
    return {"status": "ok", "version": app.version}


@app.post("/session/create", tags=["Session"])
def api_create_session(body: CreateSessionRequest):
    try:
        session_id = create_session(body.candidate_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"session_id": session_id}


@app.post("/session/transcript", tags=["Session"])
def api_save_transcript(body: TranscriptRequest):
    try:
        save_transcript(body.session_id, body.question, body.answer)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": "saved"}


@app.post("/session/evaluation", tags=["Session"])
def api_save_evaluation(body: EvaluationRequest):
    try:
        save_evaluation(body.session_id, body.score, body.feedback)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": "saved"}


@app.post("/session/complete", tags=["Session"])
def api_complete_session(body: SessionActionRequest):
    try:
        complete_session(body.session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": "session completed"}


@app.post("/session/interrupt", tags=["Session"])
def api_interrupt_session(body: SessionActionRequest):
    try:
        interrupt_session(body.session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": "session interrupted"}


@app.get("/session/{session_id}", response_model=SessionResponse, tags=["Session"])
def api_load_session(session_id: str):
    try:
        return load_session(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/session/{session_id}/status", response_model=SessionStatusResponse, tags=["Session"])
def api_session_status(session_id: str):
    try:
        return get_session_status(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/sessions/{candidate_id}", response_model=list[SessionSummary], tags=["Candidate"])
def api_list_sessions(candidate_id: str):
    try:
        return list_sessions(candidate_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
