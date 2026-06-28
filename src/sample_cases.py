"""Utilities for loading classroom sample fact-checking cases."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_SAMPLE_INPUT = "网传某地因为食品安全问题关闭了所有中小学食堂。"
SAMPLE_CASES_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_cases.json"


def load_sample_cases(path: str | Path = SAMPLE_CASES_PATH) -> list[dict[str, Any]]:
    """Load sample cases for the Gradio dropdown.

    Returns an empty list if the file is missing or malformed so the UI can still
    start with manual input and the default sample message.
    """
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(raw, list):
        return []
    cases: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, dict) and item.get("input_text"):
            cases.append(item)
    return cases


def sample_case_choices(cases: list[dict[str, Any]]) -> list[str]:
    """Return stable dropdown labels for sample cases."""
    return [f"{case.get('category', '案例')}｜{case.get('title', case.get('case_id', '未命名'))}" for case in cases]


def input_for_choice(choice: str | None, cases: list[dict[str, Any]]) -> str:
    """Map a dropdown label back to its input text, preserving manual fallback."""
    if not choice:
        return DEFAULT_SAMPLE_INPUT
    lookup = dict(zip(sample_case_choices(cases), cases, strict=False))
    case = lookup.get(choice)
    return str(case.get("input_text")) if case else DEFAULT_SAMPLE_INPUT
