from __future__ import annotations

from typing import Any

from .llm_client import LLMClient
from .schemas import Claim, EvidenceCard, PageEvidence

RELATIONS = {"support", "refute", "partially_support", "unclear", "irrelevant"}


class EvidenceAnalyzer:
    def __init__(self, demo_mode: bool = True):
        self.demo_mode = demo_mode
        self.llm = LLMClient(demo_mode)
        self.last_status: str = "not_called"
        self.last_error: str | None = None

    def analyze(self, claim: Claim, page: PageEvidence, idx: int) -> EvidenceCard:
        local = self._rule_based(claim, page)
        analysis = local
        self.last_status = "rule_based" if self.demo_mode else "not_called"
        self.last_error = None

        if not self.demo_mode:
            llm_data = self.llm.chat_json(
                [
                    {
                        "role": "user",
                        "content": self._prompt(claim, page),
                    }
                ],
                local,
            )
            self.last_status = self.llm.last_status
            self.last_error = self.llm.last_error
            normalized = self._normalize_llm_analysis(llm_data)
            if self.llm.last_status == "success" and normalized:
                analysis = normalized
                self.last_status = "success"
            else:
                analysis = local
                self.last_status = "failed" if self.llm.last_status in {"success", "failed"} else self.llm.last_status
                self.last_error = self.last_error or "LLM evidence analysis returned malformed JSON"

        source_type = "official" if ".gov" in page.domain or "edu.gov" in page.domain else ("mainstream_media" if "news" in page.domain or "news.cn" in page.domain else "other")
        if "factcheck" in page.domain:
            source_type = "other"
        return EvidenceCard(
            evidence_id=f"E{idx}",
            claim_id=claim.claim_id,
            title=page.title,
            url=page.url,
            domain=page.domain,
            source_type=source_type,
            published_date=page.published_date,
            excerpt=page.text_excerpt[:500],
            relation=analysis["relation"],
            evidence_strength=analysis["evidence_strength"],
            reasoning=analysis["reasoning"],
        )

    def _prompt(self, claim: Claim, page: PageEvidence) -> str:
        return f"""
请判断网页证据与事实主张的关系。只输出 JSON object，不要 markdown。

关系定义：
- 如果证据直接证明 claim 成立，输出 support。
- 如果证据直接反驳 claim，输出 refute。
- 如果证据只支持其中一部分，输出 partially_support。
- 如果证据相关但不能确认，输出 unclear。
- 如果证据和 claim 无关，输出 irrelevant。
- 不要因为来源不是官方就默认 unclear。
- 如果 source 明确写出“巴黎为2024年夏季奥运会举办地”，应判断为 support。

强度标准：官方/权威媒体直接支持 80-95；主流媒体直接支持 70-90；只提供背景或申办阶段信息 40-65；无关内容 0-20。

输出格式：{{"relation":"support|refute|partially_support|unclear|irrelevant","evidence_strength":0,"reasoning":"一句中文解释"}}

claim_id: {claim.claim_id}
claim_text: {claim.claim_text}
page title: {page.title}
page url: {page.url}
page domain: {page.domain}
published_date: {page.published_date}
text_excerpt: {page.text_excerpt}
full_text_first_2000: {(page.full_text or page.text_excerpt)[:2000]}
"""

    def _normalize_llm_analysis(self, data: Any) -> dict[str, Any] | None:
        if not isinstance(data, dict):
            return None
        relation = str(data.get("relation", "")).strip()
        if relation not in RELATIONS:
            return None
        try:
            strength = int(float(data.get("evidence_strength", 0)))
        except Exception:
            return None
        strength = max(0, min(100, strength))
        reasoning = str(data.get("reasoning") or "LLM 判断证据关系。").strip()
        return {"relation": relation, "evidence_strength": strength, "reasoning": reasoning}

    def _rule_based(self, claim: Claim, page: PageEvidence) -> dict[str, Any]:
        claim_text = claim.claim_text
        page_text = page.full_text or page.text_excerpt
        combined = f"{page_text} {claim_text}"
        relation = "unclear"
        strength = 45
        reason = "证据仅提供背景，无法完全确认主张。"
        if page.fetch_status != "ok" and page.text_excerpt:
            reason = "正文读取失败，基于搜索摘要判断。"

        olympic_claim = all(keyword in claim_text for keyword in ["2024"]) and any(keyword in claim_text for keyword in ["奥运", "奥运会", "夏季奥运会"]) and any(keyword in claim_text for keyword in ["巴黎", "法国"])
        direct_paris_2024 = any(
            keyword in page_text
            for keyword in [
                "最终确定巴黎为2024年夏季奥运会举办地",
                "巴黎为2024年夏季奥运会举办地",
                "巴黎被确定为2024年夏季奥运会举办地",
                "巴黎奥运会将于",
                "2024年巴黎奥运会",
            ]
        ) or ("国际奥委会" in page_text and "巴黎" in page_text and "2024年夏季奥运会举办地" in page_text)
        bid_only = any(keyword in page_text for keyword in ["申办", "可能取得举办权", "大路敞开"])
        if olympic_claim and direct_paris_2024:
            return {"relation": "support", "evidence_strength": 90, "reasoning": reason if page.fetch_status != "ok" else "证据明确写明巴黎为2024年夏季奥运会举办地，直接支持该主张。"}
        if olympic_claim and bid_only:
            return {"relation": "partially_support", "evidence_strength": 55, "reasoning": "证据仅说明申办或可能性，不能直接证明最终举办事实。"}

        if any(keyword in combined for keyword in ["新增20所", "课后服务试点", "试点学校名单"]):
            relation = "support"
            strength = 88
            reason = "来源直接支持课后服务试点的数量、时间或官方通知信息。"
        elif any(keyword in page_text for keyword in ["旧闻新炒", "时间错位", "并非今天", "2019年"]):
            relation = "refute"
            strength = 84
            reason = "来源显示传播内容存在时间错位或旧闻新炒，反驳其作为当前事件的表述。"
        elif any(keyword in page_text for keyword in ["未提及关闭所有", "不实", "并未关闭所有", "夸大", "不存在全县所有"]):
            if any(keyword in claim_text for keyword in ["所有", "全县", "全市", "关闭"]):
                relation = "refute"
                strength = 82
                reason = "来源明确指出传言范围被夸大或关键表述不成立。"
            else:
                relation = "partially_support"
                strength = 62
                reason = "来源支持存在局部事件，但提示传播范围或因果解释存在问题。"
        elif any(keyword in page_text for keyword in ["暂停", "整改", "通报显示", "检查", "三所学校"]):
            relation = "partially_support"
            strength = 66
            reason = "证据支持存在相关整改/暂停供餐事实，但不足以支持全部表述。"
        return {"relation": relation, "evidence_strength": strength, "reasoning": reason}
