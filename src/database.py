"""SQLite storage for classroom fact-checking sessions."""
from __future__ import annotations

import csv
import io
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .settings import get_settings

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "chongmingbird.db"
SQLITE_PREFIX = "sqlite:///"


def _path() -> str:
    """Resolve the configured SQLite path.

    Relative SQLite URLs are resolved against the repository root, not the
    process current working directory. This keeps `python /path/to/app.py`
    safe when launched from another directory.
    """
    url = get_settings().database_url
    if not url:
        return str(DEFAULT_DB_PATH)
    if not url.startswith(SQLITE_PREFIX):
        return str(DEFAULT_DB_PATH)

    raw_path = url[len(SQLITE_PREFIX) :]
    if not raw_path:
        return str(DEFAULT_DB_PATH)

    db_path = Path(raw_path)
    if db_path.is_absolute():
        return str(db_path)
    return str(PROJECT_ROOT / db_path)


def init_db() -> None:
    path = Path(_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions(
                session_id TEXT PRIMARY KEY,
                created_at TEXT,
                user_input TEXT,
                extracted_claims_json TEXT,
                search_trace_json TEXT,
                evidence_cards_json TEXT,
                ai_result_json TEXT,
                human_override_json TEXT,
                elapsed_seconds REAL,
                demo_mode INTEGER
            )
            """
        )


def _to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def save_session(result, user_input: str) -> None:
    init_db()
    with sqlite3.connect(_path()) as con:
        con.execute(
            "INSERT OR REPLACE INTO sessions VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                result.session_id,
                datetime.now(UTC).isoformat(),
                user_input,
                _to_json([claim.model_dump() for claim in result.claims]),
                _to_json(result.search_trace),
                _to_json([card.model_dump() for card in result.evidence_cards]),
                _to_json({"scores": [score.model_dump() for score in result.scores], "report": result.report, "ai_conclusion": "AI 结论见报告，人工裁决需用户主动提交。"}),
                _to_json({"status": "未提交人工裁决"}),
                result.elapsed_seconds,
                int(result.demo_mode),
            ),
        )


def update_human(session_id: str, override) -> bool:
    init_db()
    with sqlite3.connect(_path()) as con:
        cursor = con.execute(
            "UPDATE sessions SET human_override_json=? WHERE session_id=?",
            (_to_json(override.model_dump()), session_id),
        )
        return cursor.rowcount > 0


def list_sessions() -> list[dict[str, Any]]:
    init_db()
    with sqlite3.connect(_path()) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT session_id,created_at,user_input,human_override_json,elapsed_seconds,demo_mode FROM sessions ORDER BY created_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_session(session_id: str) -> dict[str, Any] | None:
    init_db()
    with sqlite3.connect(_path()) as con:
        con.row_factory = sqlite3.Row
        row = con.execute("SELECT * FROM sessions WHERE session_id=?", (session_id,)).fetchone()
    return dict(row) if row else None


def export_csv_text() -> str:
    rows = list_sessions()
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["session_id", "created_at", "user_input", "human_override_json", "elapsed_seconds", "demo_mode"])
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()
