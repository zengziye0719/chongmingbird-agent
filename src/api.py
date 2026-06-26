"""FastAPI backend for ChongmingBird Agent."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

from .agent import FactCheckAgent
from .database import export_csv_text, get_session, init_db, list_sessions, update_human
from .schemas import HumanOverride

app = FastAPI(title="ChongmingBird Agent API")


class FactCheckRequest(BaseModel):
    text: str
    demo_mode: bool = True


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/fact-check")
def fact_check(request: FactCheckRequest):
    return FactCheckAgent(request.demo_mode).run(request.text)


@app.get("/api/sessions")
def sessions():
    return list_sessions()


@app.get("/api/sessions/{session_id}")
def session(session_id: str):
    record = get_session(session_id)
    if not record:
        raise HTTPException(status_code=404, detail="session not found")
    return record


@app.post("/api/sessions/{session_id}/human-override")
def human(session_id: str, override: HumanOverride):
    if not update_human(session_id, override):
        raise HTTPException(status_code=404, detail="session not found")
    return {"ok": True}


@app.get("/api/export.csv")
def export():
    return Response(
        export_csv_text(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=chongmingbird_logs.csv"},
    )
