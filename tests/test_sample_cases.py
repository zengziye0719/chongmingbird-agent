from src.sample_cases import DEFAULT_SAMPLE_INPUT, input_for_choice, load_sample_cases, sample_case_choices


def test_sample_cases_load_and_map_choice():
    cases = load_sample_cases()
    assert len(cases) == 5
    categories = {case["category"] for case in cases}
    assert {"真实", "虚假", "半真半假", "证据不足", "旧闻新炒"}.issubset(categories)
    choices = sample_case_choices(cases)
    assert choices
    assert input_for_choice(choices[0], cases) == cases[0]["input_text"]


def test_sample_cases_fallback_on_missing_file(tmp_path):
    cases = load_sample_cases(tmp_path / "missing.json")
    assert cases == []
    assert input_for_choice("不存在", cases) == DEFAULT_SAMPLE_INPUT


def test_env_example_does_not_pin_default_deepseek_provider():
    lines = [line.strip() for line in open(".env.example", encoding="utf-8") if line.strip() and not line.lstrip().startswith("#")]
    assert "DEEPSEEK_BASE_URL=https://api.deepseek.com" not in lines
    assert "DEEPSEEK_MODEL=deepseek-v4-flash" not in lines
    assert "DEEPSEEK_BASE_URL=" in lines
    assert "DEEPSEEK_MODEL=" in lines
