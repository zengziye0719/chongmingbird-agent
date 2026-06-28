"""Tavily-compatible web search tool with deterministic demo fallback."""
from __future__ import annotations

from urllib.parse import urlparse

try:
    import requests
except Exception:  # pragma: no cover - only used in dependency-limited envs
    requests = None

from .mock_data import mock_search_results_for
from .schemas import SearchResult, SearchTask
from .settings import get_settings

TAVILY_SEARCH_URL = "https://api.tavily.com/search"


class WebSearchTool:
    def __init__(self, demo_mode: bool = True):
        self.settings = get_settings()
        self.demo_mode = demo_mode
        self.last_error: str | None = None

    def search(self, task: SearchTask, max_results: int = 3) -> list[SearchResult]:
        """Search the web or return mock results in demo mode.

        On real Tavily failures, return no results and store `last_error` so the
        agent can surface a clear trace message without turning failures into
        fake evidence sources.
        """
        self.last_error = None
        if self.demo_mode:
            return [SearchResult(**{**result, "raw_rank": index + 1}) for index, result in enumerate(mock_search_results_for(task.query)[:max_results])]
        if not self.settings.tavily_api_key:
            self.last_error = "未配置 Tavily API Key，无法真实联网搜索。"
            return []
        if requests is None:
            self.last_error = "requests 依赖不可用，无法真实联网搜索。"
            return []

        payload = {
            "query": task.query,
            "max_results": max_results,
            "include_answer": False,
            "search_depth": "basic",
            "topic": "general",
        }
        headers = {
            "Authorization": f"Bearer {self.settings.tavily_api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(TAVILY_SEARCH_URL, headers=headers, json=payload, timeout=20)
            response.raise_for_status()
            output: list[SearchResult] = []
            for index, item in enumerate(response.json().get("results", []), 1):
                url = item.get("url", "")
                output.append(
                    SearchResult(
                        title=item.get("title", url),
                        url=url,
                        snippet=item.get("content", ""),
                        published_date=item.get("published_date"),
                        source_domain=urlparse(url).netloc,
                        raw_rank=index,
                    )
                )
            return output
        except Exception as exc:
            self.last_error = str(exc)
            return []
