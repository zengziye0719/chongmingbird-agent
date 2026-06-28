from src.agent import FactCheckAgent
from src.sample_cases import load_sample_cases
from src.web_search import WebSearchTool
from src.schemas import SearchTask


def _search(query: str):
    task = SearchTask(claim_id="C1", query=query, purpose="demo", preferred_source_type="mock", expected_evidence_type="mock")
    return WebSearchTool(demo_mode=True).search(task, max_results=3)


def test_after_school_case_does_not_return_canteen_mock_sources():
    case = next(case for case in load_sample_cases() if case["category"] == "真实")
    results = _search(case["input_text"])

    assert results
    joined = " ".join(f"{result.title} {result.snippet} {result.url}" for result in results)
    assert "课后服务" in joined
    assert "食堂" not in joined


def test_agent_deduplicates_evidence_urls_per_claim(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'dedupe.db'}")
    result = FactCheckAgent(demo_mode=True).run("网传某地因为食品安全问题关闭了所有中小学食堂。")

    pairs = [(card.claim_id, card.url) for card in result.evidence_cards]
    assert len(pairs) == len(set(pairs))


def test_insufficient_case_stays_insufficient_or_low_confidence(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'insufficient.db'}")
    case = next(case for case in load_sample_cases() if case["category"] == "证据不足")
    result = FactCheckAgent(demo_mode=True).run(case["input_text"])

    assert result.evidence_cards == []
    assert all(score.reliability_level == "证据不足" or (score.total_score is not None and score.total_score < 55) for score in result.scores)
