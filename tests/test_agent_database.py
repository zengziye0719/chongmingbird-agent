import json
from pathlib import Path

from src.agent import FactCheckAgent
from src.database import export_csv_text, get_session, update_human
from src.schemas import HumanOverride


def test_demo_agent_persists_session_and_sources(tmp_path, monkeypatch):
    db_path = tmp_path / "classroom.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    result = FactCheckAgent(demo_mode=True).run("网传某地因为食品安全问题关闭了所有中小学食堂。")

    assert result.session_id
    assert result.evidence_cards
    assert all(card.url.startswith("https://") for card in result.evidence_cards)
    assert "## Source 列表" in result.report

    saved = get_session(result.session_id)
    assert saved is not None
    assert saved["session_id"] == result.session_id
    assert "session_id" in export_csv_text()

    ok = update_human(result.session_id, HumanOverride(acceptance="部分接受", final_reliability_level="存疑", human_notes="课堂测试"))
    assert ok is True
    updated = get_session(result.session_id)
    override = json.loads(updated["human_override_json"])
    assert override["human_notes"] == "课堂测试"


def test_agent_run_events_yields_trace_before_result(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'events.db'}")
    events = list(FactCheckAgent(demo_mode=True).run_events("测试消息。"))
    assert events[0]["type"] == "trace"
    assert events[-1]["type"] == "result"
    assert any("正在搜索" in event["data"]["message"] for event in events if event["type"] == "trace")
