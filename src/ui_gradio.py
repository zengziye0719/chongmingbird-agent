"""Gradio classroom demo UI for ChongmingBird Agent."""
from __future__ import annotations

import tempfile

import gradio as gr

from .agent import FactCheckAgent
from .database import export_csv_text, update_human
from .sample_cases import DEFAULT_SAMPLE_INPUT, input_for_choice, load_sample_cases, sample_case_choices
from .schemas import HUMAN_LEVEL_PLACEHOLDER, HumanOverride, validate_human_override_payload


def _cards_markdown(result) -> str:
    if not result or not result.evidence_cards:
        return "暂无证据卡片。"
    return "\n\n".join(
        [
            (
                f"### {card.evidence_id}: {card.title}\n"
                f"- URL: {card.url}\n"
                f"- 来源类型: {card.source_type}\n"
                f"- 与主张关系: {card.relation}\n"
                f"- 证据强度: {card.evidence_strength}\n"
                f"- 摘录: {card.excerpt}\n"
                f"- 理由: {card.reasoning}"
            )
            for card in result.evidence_cards
        ]
    )


def run_check(text: str, demo_mode: bool):
    """Gradio generator: yields visible progress while the agent works."""
    trace_lines: list[str] = []
    yield "[准备] 已收到输入，准备启动核查流程……", "等待证据卡片……", "等待最终报告……", ""

    final_result = None
    try:
        for event in FactCheckAgent(demo_mode).run_events(text):
            if event["type"] == "trace":
                trace_lines.append(event["data"]["message"])
                yield "\n".join(trace_lines), "正在收集和分析证据……", "等待最终报告……", ""
            elif event["type"] == "result":
                final_result = event["data"]
    except Exception as exc:
        error_message = f"[错误] {type(exc).__name__}: {exc}"
        yield "\n".join(trace_lines + [error_message]), "", "核查失败，请检查配置或稍后重试。", ""
        return

    if final_result is None:
        yield "\n".join(trace_lines + ["[错误] 未生成结果。"]), "", "核查失败。", ""
        return
    yield "\n".join(trace_lines), _cards_markdown(final_result), final_result.report, final_result.session_id


def save_override(session_id: str, acceptance: str | None, level: str, notes: str) -> str:
    if not session_id:
        return "请先完成一次核查。"
    override = HumanOverride(acceptance=acceptance or "", final_reliability_level=level, human_notes=notes)
    validation_error = validate_human_override_payload(override)
    if validation_error:
        return validation_error
    update_human(session_id, override)
    return "已保存人工裁决。"


def export_csv_file() -> str:
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="w", encoding="utf-8-sig")
    handle.write(export_csv_text())
    handle.close()
    return handle.name


SAMPLE_CASES = load_sample_cases()
SAMPLE_CHOICES = sample_case_choices(SAMPLE_CASES)


def toggle_sample_case_visibility(demo_mode: bool):
    return gr.update(visible=bool(demo_mode), interactive=bool(demo_mode))


with gr.Blocks(title="ChongmingBird Agent 重明鸟") as demo:
    gr.Markdown("# ChongmingBird Agent（重明鸟）v0.3 演示原型")
    session_id = gr.Textbox(label="Session ID", visible=False)
    sample_case = gr.Dropdown(
        choices=SAMPLE_CHOICES,
        label="示例案例（仅 Demo 模式）",
        info="示例案例仅用于 Demo 模式；真实 API 模式请手动输入待核查消息。",
        value=SAMPLE_CHOICES[1] if len(SAMPLE_CHOICES) > 1 else (SAMPLE_CHOICES[0] if SAMPLE_CHOICES else None),
    )
    with gr.Row():
        text = gr.Textbox(label="输入待核查消息", lines=6, value=input_for_choice(SAMPLE_CHOICES[1] if len(SAMPLE_CHOICES) > 1 else None, SAMPLE_CASES) if SAMPLE_CHOICES else DEFAULT_SAMPLE_INPUT)
        demo_mode = gr.Checkbox(label="Demo 模式（无 API Key 也可运行）", value=True)
    start_button = gr.Button("开始核查", variant="primary")
    trace = gr.Markdown(label="实时过程区")
    evidence = gr.Markdown(label="证据区")
    report = gr.Markdown(label="最终报告区")
    demo_mode.change(toggle_sample_case_visibility, demo_mode, sample_case)
    sample_case.change(lambda choice: input_for_choice(choice, SAMPLE_CASES), sample_case, text)
    start_button.click(run_check, [text, demo_mode], [trace, evidence, report, session_id])

    gr.Markdown("## 人工裁决区")
    acceptance = gr.Radio(["接受", "部分接受", "不接受"], label="是否接受 AI 结论", value=None)
    level = gr.Dropdown([HUMAN_LEVEL_PLACEHOLDER, "高可信", "较可信", "存疑", "较不可信", "不可信", "证据不足"], label="人工最终可靠性等级", value=HUMAN_LEVEL_PLACEHOLDER)
    notes = gr.Textbox(label="人工说明", lines=3)
    save_button = gr.Button("保存人工裁决")
    save_status = gr.Markdown()
    save_button.click(save_override, [session_id, acceptance, level, notes], save_status)

    gr.Markdown("## 数据导出区")
    csv_file = gr.File(label="课堂日志 CSV")
    gr.Button("导出课堂日志 CSV").click(export_csv_file, outputs=csv_file)
