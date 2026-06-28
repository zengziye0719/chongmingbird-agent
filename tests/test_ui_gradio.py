import pytest

pytest.importorskip("gradio")

from src.ui_gradio import run_check


def test_run_check_generator_demo_mode_does_not_raise(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'ui.db'}")

    outputs = list(run_check("网传某地因为食品安全问题关闭了所有中小学食堂。", True))

    assert outputs
    final_trace, final_cards, final_report, session_id = outputs[-1]
    assert session_id
    assert "正在计算可靠性评分" in final_trace
    assert "URL:" in final_cards
    assert "Source 列表" in final_report


def test_sample_case_visibility_toggle():
    from src.ui_gradio import toggle_sample_case_visibility

    assert toggle_sample_case_visibility(True)["visible"] is True
    assert toggle_sample_case_visibility(False)["visible"] is False


def test_human_override_initial_values_and_validation(tmp_path, monkeypatch):
    from src.ui_gradio import HUMAN_LEVEL_PLACEHOLDER, acceptance, level, save_override

    assert acceptance.value is None
    assert level.value == HUMAN_LEVEL_PLACEHOLDER
    assert save_override("session-id", None, HUMAN_LEVEL_PLACEHOLDER, "") == "请先选择是否接受 AI 结论，并选择人工最终可靠性等级。"
    assert save_override("session-id", "接受", HUMAN_LEVEL_PLACEHOLDER, "") == "请先选择是否接受 AI 结论，并选择人工最终可靠性等级。"


def test_human_override_success_after_required_choices(tmp_path, monkeypatch):
    from src.agent import FactCheckAgent
    from src.ui_gradio import save_override

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'human.db'}")
    result = FactCheckAgent(demo_mode=True).run("网传某地因为食品安全问题关闭了所有中小学食堂。")
    assert save_override(result.session_id, "接受", "较可信", "") == "已保存人工裁决。"
