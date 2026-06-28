"""Orchestration for the ChongmingBird fact-checking workflow."""
from __future__ import annotations

import time
import uuid
from collections.abc import Callable, Generator
from typing import Any

from .claim_extractor import ClaimExtractor
from .database import save_session
from .evidence_analyzer import EvidenceAnalyzer
from .page_reader import PageReader
from .report_generator import ReportGenerator
from .rubric import ReliabilityRubric
from .schemas import EvidenceCard, FactCheckResult
from .search_planner import SearchPlanner
from .web_search import WebSearchTool

TraceCallback = Callable[[dict[str, Any]], None]


class FactCheckAgent:
    """Runs a complete auditable fact-checking session.

    The final reliability score is computed by :mod:`src.rubric`; LLM output is only
    used upstream for extraction/analysis when API keys are available.
    """

    def __init__(self, demo_mode: bool = True):
        self.demo_mode = demo_mode
        self.extractor = ClaimExtractor(demo_mode)
        self.planner = SearchPlanner()
        self.searcher = WebSearchTool(demo_mode)
        self.reader = PageReader(demo_mode)
        self.analyzer = EvidenceAnalyzer(demo_mode)
        self.rubric = ReliabilityRubric()
        self.reporter = ReportGenerator()

    def _build_result(
        self,
        text: str,
        trace: list[dict[str, Any]],
        claims,
        cards: list[EvidenceCard],
        started_at: float,
    ) -> FactCheckResult:
        scores = [self.rubric.score_claim(claim.claim_id, cards) for claim in claims]
        report = self.reporter.generate(text, claims, cards, scores)
        result = FactCheckResult(
            session_id=str(uuid.uuid4()),
            claims=claims,
            search_trace=trace,
            evidence_cards=cards,
            scores=scores,
            report=report,
            elapsed_seconds=round(time.time() - started_at, 2),
            demo_mode=self.demo_mode,
        )
        save_session(result, text)
        return result

    def run(self, text: str, trace_cb: TraceCallback | None = None) -> FactCheckResult:
        """Run the workflow and return the final structured result."""
        final_result: FactCheckResult | None = None
        for event in self.run_events(text):
            if event["type"] == "trace" and trace_cb:
                trace_cb(event["data"])
            elif event["type"] == "result":
                final_result = event["data"]
        if final_result is None:  # defensive guard; should never happen.
            raise RuntimeError("Fact-check workflow ended without a result")
        return final_result

    def run_events(self, text: str) -> Generator[dict[str, Any], None, None]:
        """Yield trace events as work happens, then yield the final result.

        This generator powers the Gradio demo and leaves room for future SSE or
        WebSocket streaming in FastAPI.
        """
        started_at = time.time()
        trace: list[dict[str, Any]] = []

        def log(message: str, **metadata: Any) -> dict[str, Any]:
            item = {"message": message, **metadata}
            trace.append(item)
            return {"type": "trace", "data": item}

        yield log(f"[状态] 当前模式：{'Demo 模式' if self.demo_mode else '真实 API 模式'}")
        if self.demo_mode:
            yield log("[状态] Source 类型：mock source（示例来源，不代表真实联网结果）")
        yield log("[步骤 1] 正在拆解事实主张……")
        claims = self.extractor.extract(text)
        if self.extractor.last_warning:
            yield log(f"[警告] {self.extractor.last_warning}")
        llm_status = self.extractor.llm.last_status
        if llm_status == "success":
            yield log("[状态] DeepSeek 状态：调用成功")
        elif llm_status == "failed":
            yield log(f"[警告] DeepSeek 调用失败，已回退到本地规则。原因：{self.extractor.llm.last_error}")
        elif llm_status == "unconfigured":
            yield log("[状态] DeepSeek 状态：未配置，已回退到本地规则。")
        else:
            yield log("[状态] DeepSeek 状态：未配置（Demo 模式使用本地规则）")
        yield log(f"[步骤 2] 发现 {len(claims)} 个可核查主张……")

        yield log("[步骤 3] 正在生成搜索词……")
        tasks = self.planner.plan(claims)

        cards: list[EvidenceCard] = []
        seen_urls_by_claim: set[tuple[str, str]] = set()
        evidence_index = 1
        task_limit = max(5, len(claims) * 3)
        for task in tasks[:task_limit]:
            yield log(f"[步骤 4] 正在搜索：{task.query}", claim_id=task.claim_id)
            results = self.searcher.search(task, max_results=2)
            if not results:
                if self.searcher.last_error:
                    prefix = "[警告]" if "未配置 Tavily" in self.searcher.last_error else "[搜索失败]"
                    yield log(f"{prefix} {self.searcher.last_error}", claim_id=task.claim_id)
                else:
                    yield log("[步骤 5] 未找到可用来源，继续下一个搜索任务。", claim_id=task.claim_id)
                continue

            if self.demo_mode:
                yield log("[状态] Tavily 状态：Demo 模式使用 mock 搜索结果")
            else:
                yield log("[状态] Tavily 状态：搜索成功")
            for result in results[:2]:
                dedupe_key = (task.claim_id, result.url)
                if dedupe_key in seen_urls_by_claim:
                    yield log(f"[去重] 已跳过重复来源：{result.url}", claim_id=task.claim_id, url=result.url)
                    continue
                seen_urls_by_claim.add(dedupe_key)
                source_kind = "mock source" if self.demo_mode else "real source"
                yield log(f"[步骤 5] 找到来源：{result.title} {result.url}（Source 类型：{source_kind}）", url=result.url)
                yield log("[步骤 6] 正在读取网页正文……", url=result.url)
                page = self.reader.read(result)
                if page.fetch_status != "ok":
                    yield log(f"[警告] 网页读取失败但流程继续：{page.error}", url=result.url)

                claim = next(claim for claim in claims if claim.claim_id == task.claim_id)
                card = self.analyzer.analyze(claim, page, evidence_index)
                if self.analyzer.last_status == "success":
                    yield log("[状态] EvidenceAnalyzer：LLM 分析成功", evidence_id=card.evidence_id)
                elif self.analyzer.last_status in {"failed", "unconfigured"}:
                    yield log("[警告] EvidenceAnalyzer：LLM 分析失败，已回退本地规则", evidence_id=card.evidence_id, error=self.analyzer.last_error)
                evidence_index += 1
                cards.append(card)
                yield log("[步骤 7] 正在分析证据关系……", evidence_id=card.evidence_id, relation=card.relation)

        yield log("[步骤 8] 正在计算可靠性评分……")
        result = self._build_result(text, trace, claims, cards, started_at)
        yield {"type": "result", "data": result}
