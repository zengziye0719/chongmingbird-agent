from types import SimpleNamespace

from src.llm_client import LLMClient


def test_deepseek_unconfigured_falls_back_with_status(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    client = LLMClient(demo_mode=False)
    fallback = {"claims": []}

    assert client.chat_json([], fallback) == fallback
    assert client.last_status == "unconfigured"
    assert "未配置" in client.last_error


def test_deepseek_failure_records_error(monkeypatch):
    def fake_post(*args, **kwargs):
        raise RuntimeError("deepseek down")

    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setattr("src.llm_client.requests", SimpleNamespace(post=fake_post))

    client = LLMClient(demo_mode=False)
    fallback = {"claims": []}

    assert client.chat_json([], fallback) == fallback
    assert client.last_status == "failed"
    assert "deepseek down" in client.last_error
