from __future__ import annotations
import json
try:
    import requests
except Exception:
    requests = None
from .settings import get_settings
from .prompts import SYSTEM_PRINCIPLES

class LLMClient:
    def __init__(self, demo_mode: bool | None = None):
        self.settings = get_settings(); self.demo_mode = self.settings.demo_mode if demo_mode is None else demo_mode
    @property
    def enabled(self) -> bool:
        return bool(self.settings.deepseek_api_key) and not self.demo_mode and requests is not None
    def chat_json(self, messages: list[dict], fallback):
        if not self.enabled: return fallback
        try:
            r=requests.post(f"{self.settings.deepseek_base_url.rstrip('/')}/chat/completions",headers={"Authorization":f"Bearer {self.settings.deepseek_api_key}"},json={"model":self.settings.deepseek_model,"messages":[{"role":"system","content":SYSTEM_PRINCIPLES},*messages],"response_format":{"type":"json_object"}},timeout=30)
            r.raise_for_status(); return json.loads(r.json()["choices"][0]["message"]["content"])
        except Exception:
            return fallback
