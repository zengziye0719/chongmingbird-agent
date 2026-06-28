from src.claim_extractor import ClaimExtractor, normalize_claim


def test_extract_claims_demo():
    claims = ClaimExtractor(True).extract("网传某地因为食品安全问题关闭了所有中小学食堂。")
    assert len(claims) >= 1
    assert claims[0].claim_id.startswith("C")


def test_normalize_claim_numeric_id_and_checkability():
    normalized = normalize_claim({"claim_id": 1, "claim_text": "测试主张", "checkability": "可核查"}, 1)
    assert normalized["claim_id"] == "C1"
    assert normalized["checkability"] == "中"


def test_extract_cleans_qwen_style_claim(monkeypatch):
    extractor = ClaimExtractor(demo_mode=False)

    def fake_chat_json(messages, fallback):
        return {
            "claims": [
                {
                    "claim_id": 1,
                    "claim_text": "2024年夏季奥运会在法国巴黎举办。",
                    "checkability": "可核查",
                    "reason": "可以查询官方来源",
                }
            ]
        }

    extractor.llm.chat_json = fake_chat_json
    claims = extractor.extract("2024年夏季奥运会在法国巴黎举办。")

    assert claims[0].claim_id == "C1"
    assert claims[0].checkability == "中"
    assert claims[0].suggested_search_angles
    assert extractor.last_warning == "LLM 输出格式异常，已清洗。"


def test_extract_skips_malformed_claim_without_crashing(monkeypatch):
    extractor = ClaimExtractor(demo_mode=False)

    def fake_chat_json(messages, fallback):
        return {"claims": [{"claim_id": 1, "checkability": "high"}, {"text": "有效主张", "checkability": "high"}]}

    extractor.llm.chat_json = fake_chat_json
    claims = extractor.extract("有效主张。")

    assert len(claims) == 1
    assert claims[0].claim_id == "C1"
    assert claims[0].claim_text == "有效主张"
    assert claims[0].checkability == "高"


def test_extract_empty_claims_uses_fallback(monkeypatch):
    extractor = ClaimExtractor(demo_mode=False)

    def fake_chat_json(messages, fallback):
        return {"claims": []}

    extractor.llm.chat_json = fake_chat_json
    claims = extractor.extract(" fallback 主张。")

    assert claims
    assert claims[0].claim_text == "fallback 主张"
    assert extractor.last_warning == "LLM 输出格式异常，已回退到本地规则。"


def test_extract_non_list_claims_uses_fallback(monkeypatch):
    extractor = ClaimExtractor(demo_mode=False)

    def fake_chat_json(messages, fallback):
        return {"claims": {"claim_text": "不是数组"}}

    extractor.llm.chat_json = fake_chat_json
    claims = extractor.extract("备用主张。")

    assert claims[0].claim_text == "备用主张"
    assert extractor.last_warning == "LLM 输出格式异常，已回退到本地规则。"
