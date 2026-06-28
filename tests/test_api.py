import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from src.api import app


def test_api_health_and_fact_check(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'api.db'}")
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}

    response = client.post("/api/fact-check", json={"text": "测试消息。", "demo_mode": True})
    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"]
    assert payload["evidence_cards"]

    sessions = client.get("/api/sessions")
    assert sessions.status_code == 200
    assert len(sessions.json()) >= 1

    exported = client.get("/api/export.csv")
    assert exported.status_code == 200
    assert "session_id" in exported.text
