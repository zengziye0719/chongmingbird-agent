from src.rubric import ReliabilityRubric
from src.schemas import EvidenceCard

def test_rubric_scores_with_evidence():
    cards=[EvidenceCard(evidence_id="E1",claim_id="C1",title="gov",url="https://x.gov/a",domain="x.gov",source_type="official",relation="support",evidence_strength=90)]
    s=ReliabilityRubric().score_claim("C1",cards)
    assert s.total_score is not None
    assert s.reliability_level in {"高可信","较可信","存疑","较不可信","不可信"}

def test_rubric_insufficient():
    s=ReliabilityRubric().score_claim("C1",[])
    assert s.reliability_level=="证据不足"
