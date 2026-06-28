import re
from typing import Any

from .llm_client import LLMClient
from .schemas import Claim

DEFAULT_SEARCH_ANGLES = ["官方通报", "主流媒体报道", "反证与辟谣", "时间线", "原始出处"]
DEFAULT_REASON = "包含可通过公开来源交叉验证的事实性表述。"


def normalize_checkability(value: Any) -> str:
    text = str(value).strip().lower()
    if value is True or text in {"可核查", "中等", "medium", "true", "yes", "可查", "一般"}:
        return "中"
    if text in {"高", "高可核查", "high", "highly_checkable", "strong"}:
        return "高"
    if value is False or text in {"低", "低可核查", "low", "不可核查", "false", "no", "weak"}:
        return "低"
    if text in {"中", "中可核查", "moderate"}:
        return "中"
    return "中"


def normalize_claim(raw_claim: Any, index: int) -> dict[str, Any] | None:
    """Normalize model-specific claim JSON into the strict Claim schema.

    Returns None for malformed items that do not contain usable claim text.
    """
    if not isinstance(raw_claim, dict):
        return None

    claim_text = (
        raw_claim.get("claim_text")
        or raw_claim.get("claim")
        or raw_claim.get("text")
        or raw_claim.get("content")
        or raw_claim.get("statement")
    )
    if claim_text is None:
        return None
    claim_text = str(claim_text).strip()
    if not claim_text:
        return None

    suggested = raw_claim.get("suggested_search_angles") or raw_claim.get("search_angles") or raw_claim.get("suggested_queries")
    if not isinstance(suggested, list):
        suggested = DEFAULT_SEARCH_ANGLES
    else:
        suggested = [str(item).strip() for item in suggested if str(item).strip()] or DEFAULT_SEARCH_ANGLES

    reason = raw_claim.get("reason") or raw_claim.get("rationale") or raw_claim.get("explanation") or DEFAULT_REASON

    return {
        "claim_id": f"C{index}",
        "claim_text": claim_text,
        "checkability": normalize_checkability(raw_claim.get("checkability", "中")),
        "reason": str(reason).strip() or DEFAULT_REASON,
        "suggested_search_angles": suggested,
    }


class ClaimExtractor:
    def __init__(self, demo_mode: bool = True):
        self.llm = LLMClient(demo_mode)
        self.last_warning: str | None = None

    def extract(self, text: str) -> list[Claim]:
        self.last_warning = None
        fallback = self._heuristic(text)
        prompt = (
            "请将文本拆解为可核查事实主张。必须输出 JSON object，格式为："
            '{"claims":[{"claim_id":"C1","claim_text":"...","checkability":"高|中|低",'
            '"reason":"...","suggested_search_angles":["..."]}]}。'
            '要求：claims 必须是 array；claim_id 必须是字符串，例如 "C1"；'
            'checkability 只能输出 "高"、"中"、"低"；不要输出 markdown。\n'
            f"待核查文本：{text}"
        )
        data = self.llm.chat_json([{"role": "user", "content": prompt}], {"claims": [claim.model_dump() for claim in fallback]})

        raw_claims = data.get("claims") if isinstance(data, dict) else None
        if not isinstance(raw_claims, list):
            self.last_warning = "LLM 输出格式异常，已回退到本地规则。"
            return fallback

        normalized = []
        dropped = 0
        for raw in raw_claims:
            normalized_claim = normalize_claim(raw, len(normalized) + 1)
            if normalized_claim is None:
                dropped += 1
                continue
            normalized.append(normalized_claim)

        if not normalized:
            self.last_warning = "LLM 输出格式异常，已回退到本地规则。"
            return fallback

        try:
            claims = [Claim(**claim) for claim in normalized]
        except Exception:
            self.last_warning = "LLM 输出格式异常，已回退到本地规则。"
            return fallback

        if dropped or normalized != raw_claims:
            self.last_warning = "LLM 输出格式异常，已清洗。"
        return claims

    def _heuristic(self, text):
        parts = [p.strip() for p in re.split(r"[。！？；;\n]+", text) if p.strip()]
        if not parts:
            parts = [text.strip() or "空输入"]
        claims = []
        for i, part in enumerate(parts, 1):
            claims.append(
                Claim(
                    claim_id=f"C{i}",
                    claim_text=part,
                    checkability="中",
                    reason=DEFAULT_REASON,
                    suggested_search_angles=DEFAULT_SEARCH_ANGLES,
                )
            )
        if len(claims) == 1 and ("因为" in text or "导致" in text):
            claims.append(
                Claim(
                    claim_id="C2",
                    claim_text="该事件的原因链条是否成立：" + text,
                    checkability="中",
                    reason="因果关系需要独立证据支持。",
                    suggested_search_angles=["原因说明", "官方调查", "媒体追踪"],
                )
            )
        return claims
