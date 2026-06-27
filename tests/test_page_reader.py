from types import SimpleNamespace

from src.page_reader import PageReader
from src.schemas import SearchResult


def test_page_reader_failure_does_not_raise(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("network blocked")

    monkeypatch.setattr("src.page_reader.requests", SimpleNamespace(get=boom))
    result = SearchResult(title="bad", url="https://bad.example/page", snippet="fallback", source_domain="bad.example")
    page = PageReader(demo_mode=False).read(result)

    assert page.fetch_status == "failed"
    assert page.text_excerpt == "fallback"
    assert "network blocked" in page.error
