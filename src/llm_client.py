from __future__ import annotations

import json

try:
    import requests
except Exception:
    requests = None

from .prompts import SYSTEM_PRINCIPLES
from .settings import get_settings


class LLMClient:
    """DeepSeek OpenAI-compatible chat completions client with fallback state."""

    def __init__(self, demo_mode: bool | None = None):
        self.settings = get_settings()
        self.demo_mode = self.settings.demo_mode if demo_mode is None else demo_mode
        self.last_error: str | None = None
        self.last_status: str = "not_called"

    @property
    def enabled(self) -> bool:
        return bool(self.settings.deepseek_api_key) and not self.demo_mode and requests is not None

    def chat_json(self, messages: list[dict], fallback):
        self.last_error = None
        if self.demo_mode:
            self.last_status = "demo"
            return fallback
        if not self.settings.deepseek_api_key:
            self.last_status = "unconfigured"
            self.last_error = "未配置 DeepSeek API Key"
            return fallback
        if requests is None:
            self.last_status = "failed"
            self.last_error = "requests 依赖不可用"
            return fallback

        try:
            response = requests.post(
                f"{self.settings.deepseek_base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {self.settings.deepseek_api_key}", "Content-Type": "application/json"},
                json={
                    "model": self.settings.deepseek_model,
                    "messages": [{"role": "system", "content": SYSTEM_PRINCIPLES}, *messages],
                    "response_format": {"type": "json_object"},
                },
                timeout=30,
            )
            response.raise_for_status()
            self.last_status = "success"
            return json.loads(response.json()["choices"][0]["message"]["content"])
        except Exception as exc:
            self.last_status = "failed"
            self.last_error = str(exc)
            return fallback
