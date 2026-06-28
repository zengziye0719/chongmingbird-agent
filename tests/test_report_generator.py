from src.report_generator import ReportGenerator
from src.schemas import Claim, EvidenceCard, ReliabilityScore

def test_report_contains_source():
    c=Claim(claim_id="C1",claim_text="测试主张")
    e=EvidenceCard(evidence_id="E1",claim_id="C1",title="来源",url="https://example.com",relation="support",evidence_strength=80)
    s=ReliabilityScore(claim_id="C1",total_score=75,reliability_level="较可信",dimension_scores={},explanation="ok")
    r=ReportGenerator().generate("原文",[c],[e],[s])
    assert "https://example.com" in r and "人工最终裁决区" in r
