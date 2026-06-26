"""Gradio classroom demo UI for ChongmingBird Agent."""
from __future__ import annotations

import tempfile

import gradio as gr

from .agent import FactCheckAgent
from .database import export_csv_text, update_human
from .schemas import HumanOverride


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
    for event in FactCheckAgent(demo_mode).run_events(text):
        if event["type"] == "trace":
            trace_lines.append(event["data"]["message"])
            yield "\n".join(trace_lines), "正在收集和分析证据……", "等待最终报告……", ""
        elif event["type"] == "result":
            final_result = event["data"]

    if final_result is None:
        yield "\n".join(trace_lines + ["[错误] 未生成结果。"]), "", "核查失败。", ""
        return
    yield "\n".join(trace_lines), _cards_markdown(final_result), final_result.report, final_result.session_id


def save_override(session_id: str, acceptance: str, level: str, notes: str) -> str:
    if not session_id:
        return "请先完成一次核查。"
    update_human(session_id, HumanOverride(acceptance=acceptance, final_reliability_level=level, human_notes=notes))
    return "已保存人工裁决。"


def export_csv_file() -> str:
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="w", encoding="utf-8-sig")
    handle.write(export_csv_text())
    handle.close()
    return handle.name


with gr.Blocks(title="ChongmingBird Agent 重明鸟") as demo:
    gr.Markdown("# ChongmingBird Agent（重明鸟）事实核查 Demo")
    session_id = gr.Textbox(label="Session ID", visible=False)
    with gr.Row():
        text = gr.Textbox(label="输入待核查消息", lines=6, value="网传某地因为食品安全问题关闭了所有中小学食堂。")
        demo_mode = gr.Checkbox(label="Demo 模式（无 API Key 也可运行）", value=True)
    start_button = gr.Button("开始核查", variant="primary")
    trace = gr.Markdown(label="实时过程区")
    evidence = gr.Markdown(label="证据区")
    report = gr.Markdown(label="最终报告区")
    start_button.click(run_check, [text, demo_mode], [trace, evidence, report, session_id])

    gr.Markdown("## 人工裁决区")
    acceptance = gr.Radio(["接受", "部分接受", "不接受"], label="是否接受 AI 结论", value="部分接受")
    level = gr.Dropdown(["高可信", "较可信", "存疑", "较不可信", "不可信", "证据不足"], label="人工最终可靠性等级", value="存疑")
    notes = gr.Textbox(label="人工说明", lines=3)
    save_button = gr.Button("保存人工裁决")
    save_status = gr.Markdown()
    save_button.click(save_override, [session_id, acceptance, level, notes], save_status)

    gr.Markdown("## 数据导出区")
    csv_file = gr.File(label="课堂日志 CSV")
    gr.Button("导出课堂日志 CSV").click(export_csv_file, outputs=csv_file)
