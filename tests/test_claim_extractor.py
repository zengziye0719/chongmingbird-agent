from src.claim_extractor import ClaimExtractor

def test_extract_claims_demo():
    claims=ClaimExtractor(True).extract("网传某地因为食品安全问题关闭了所有中小学食堂。")
    assert len(claims)>=1
    assert claims[0].claim_id.startswith("C")
