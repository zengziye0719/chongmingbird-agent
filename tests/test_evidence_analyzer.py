from types import SimpleNamespace

from src.evidence_analyzer import EvidenceAnalyzer
from src.schemas import Claim, PageEvidence, EvidenceCard
from src.rubric import ReliabilityRubric


def test_olympics_direct_evidence_supports_claim():
    analyzer = EvidenceAnalyzer(demo_mode=True)
    card = analyzer.analyze(
        Claim(claim_id="C1", claim_text="2024年奥运会在法国巴黎举办。"),
        PageEvidence(
            title="新华网报道",
            url="https://news.cn/example",
            domain="news.cn",
            text_excerpt="国际奥委会最终确定巴黎为2024年夏季奥运会举办地。",
            full_text="国际奥委会最终确定巴黎为2024年夏季奥运会举办地。",
        ),
        1,
    )
    assert card.relation == "support"
    assert card.evidence_strength >= 85


def test_olympics_bid_only_is_not_strong_support():
    analyzer = EvidenceAnalyzer(demo_mode=True)
    card = analyzer.analyze(
        Claim(claim_id="C1", claim_text="2024年奥运会在法国巴黎举办。"),
        PageEvidence(
            title="申办报道",
            url="https://news.example/bid",
            domain="news.example",
            text_excerpt="巴黎正式申办2024年夏季奥运会。",
            full_text="巴黎正式申办2024年夏季奥运会。",
        ),
        1,
    )
    assert card.relation in {"partially_support", "unclear"}
    assert card.relation != "support"


def test_evidence_analyzer_malformed_llm_falls_back_to_rules(monkeypatch):
    analyzer = EvidenceAnalyzer(demo_mode=False)

    def fake_chat_json(messages, fallback):
        analyzer.llm.last_status = "success"
        analyzer.llm.last_error = None
        return {"relation": "bad", "evidence_strength": "nope"}

    analyzer.llm.chat_json = fake_chat_json
    card = analyzer.analyze(
        Claim(claim_id="C1", claim_text="2024年奥运会在法国巴黎举办。"),
        PageEvidence(
            title="新华网报道",
            url="https://news.cn/example",
            domain="news.cn",
            text_excerpt="国际奥委会最终确定巴黎为2024年夏季奥运会举办地。",
            full_text="国际奥委会最终确定巴黎为2024年夏季奥运会举办地。",
        ),
        1,
    )
    assert card.relation == "support"
    assert analyzer.last_status == "failed"


def test_rubric_support_without_refute_is_high_trust():
    cards = [
        EvidenceCard(evidence_id="E1", claim_id="C1", title="新华网", url="https://news.cn/a", domain="news.cn", source_type="mainstream_media", relation="support", evidence_strength=88),
        EvidenceCard(evidence_id="E2", claim_id="C1", title="IOC", url="https://olympics.com/a", domain="olympics.com", source_type="official", relation="support", evidence_strength=90),
    ]
    score = ReliabilityRubric().score_claim("C1", cards)
    assert score.reliability_level == "高可信"
    assert score.total_score >= 85


def test_rubric_all_unclear_is_not_untrustworthy():
    cards = [EvidenceCard(evidence_id="E1", claim_id="C1", title="背景", url="https://x.test", relation="unclear", evidence_strength=40)]
    score = ReliabilityRubric().score_claim("C1", cards)
    assert score.reliability_level in {"证据不足", "存疑"}


def test_rubric_low_quality_support_does_not_auto_high_trust():
    cards = [
        EvidenceCard(evidence_id="E1", claim_id="C1", title="博客", url="https://blog.test/a", domain="blog.test", source_type="other", relation="support", evidence_strength=86),
        EvidenceCard(evidence_id="E2", claim_id="C1", title="论坛", url="https://forum.test/a", domain="forum.test", source_type="other", relation="support", evidence_strength=86),
    ]
    score = ReliabilityRubric().score_claim("C1", cards)
    assert score.reliability_level != "高可信"
