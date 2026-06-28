from types import SimpleNamespace

from src.schemas import SearchTask
from src.web_search import TAVILY_SEARCH_URL, WebSearchTool


def _task():
    return SearchTask(
        claim_id="C1",
        query="2024年夏季奥运会 法国 巴黎",
        purpose="官方来源搜索",
        preferred_source_type="official",
        expected_evidence_type="官方来源",
    )


def test_demo_mode_returns_mock_without_tavily_key(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    tool = WebSearchTool(demo_mode=True)
    task = SearchTask(
        claim_id="C1",
        query="网传某地因为食品安全问题关闭了所有中小学食堂。",
        purpose="官方来源搜索",
        preferred_source_type="official",
        expected_evidence_type="官方来源",
    )

    results = tool.search(task, max_results=2)

    assert len(results) == 2
    assert tool.last_error is None
    assert all(result.url.startswith("https://") for result in results)


def test_tavily_request_uses_bearer_header_not_body_api_key(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "results": [
                    {
                        "title": "Paris 2024",
                        "url": "https://olympics.com/en/paris-2024",
                        "content": "Paris hosted the 2024 Summer Olympics.",
                        "published_date": "2024-07-26",
                    }
                ]
            }

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    monkeypatch.setattr("src.web_search.requests", SimpleNamespace(post=fake_post))

    results = WebSearchTool(demo_mode=False).search(_task(), max_results=1)

    assert captured["url"] == TAVILY_SEARCH_URL
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["headers"]["Content-Type"] == "application/json"
    assert "api_key" not in captured["json"]
    assert captured["json"] == {
        "query": "2024年夏季奥运会 法国 巴黎",
        "max_results": 1,
        "include_answer": False,
        "search_depth": "basic",
        "topic": "general",
    }
    assert results[0].url == "https://olympics.com/en/paris-2024"


def test_tavily_failure_returns_no_fake_source(monkeypatch):
    def fake_post(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    monkeypatch.setattr("src.web_search.requests", SimpleNamespace(post=fake_post))

    tool = WebSearchTool(demo_mode=False)
    results = tool.search(_task(), max_results=1)

    assert results == []
    assert "boom" in tool.last_error


def test_agent_trace_reports_search_failure_without_fake_evidence(tmp_path, monkeypatch):
    from src.agent import FactCheckAgent

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'failed-search.db'}")
    agent = FactCheckAgent(demo_mode=False)

    def fail_search(task, max_results=2):
        agent.searcher.last_error = "Tavily 401 Unauthorized"
        return []

    agent.searcher.search = fail_search
    events = list(agent.run_events("2024年夏季奥运会在法国巴黎举办。"))
    trace_messages = [event["data"]["message"] for event in events if event["type"] == "trace"]
    result = events[-1]["data"]

    assert any("搜索失败" in message and "Tavily 401" in message for message in trace_messages)
    assert result.evidence_cards == []
    assert all("example.invalid/search-error" not in message for message in trace_messages)


def test_real_mode_without_tavily_key_returns_no_mock_results(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    tool = WebSearchTool(demo_mode=False)

    results = tool.search(_task(), max_results=2)

    assert results == []
    assert "未配置 Tavily API Key" in tool.last_error
