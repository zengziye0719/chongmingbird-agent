from .schemas import Claim, EvidenceCard, ReliabilityScore
class ReportGenerator:
    def generate(self, original_text:str, claims:list[Claim], cards:list[EvidenceCard], scores:list[ReliabilityScore])->str:
        smap={s.claim_id:s for s in scores}; lines=["# ChongmingBird 事实核查报告","","## 原始输入",original_text,"","## 拆解出的事实主张"]
        for c in claims: lines += [f"- **{c.claim_id}** {c.claim_text}（可核查程度：{c.checkability}）- {c.reason}"]
        lines += ["","## 分项结论"]
        for c in claims:
            s=smap.get(c.claim_id); lines += [f"### {c.claim_id}: {c.claim_text}", f"- 可靠性等级：**{s.reliability_level if s else '证据不足'}**", f"- 分数：{s.total_score if s and s.total_score is not None else '不计分'}", f"- 判断理由：{s.explanation if s else '无'}", "#### 支持证据"]
            rel=[e for e in cards if e.claim_id==c.claim_id and e.relation in ("support","partially_support")]
            lines += [f"- [{e.title}]({e.url})（{e.relation}, {e.evidence_strength}）：{e.excerpt}" for e in rel] or ["- 暂无"]
            lines += ["#### 反驳证据"] + ([f"- [{e.title}]({e.url})（{e.evidence_strength}）：{e.excerpt}" for e in cards if e.claim_id==c.claim_id and e.relation=="refute"] or ["- 暂无"])
            lines += ["#### 不确定证据"] + ([f"- [{e.title}]({e.url})：{e.reasoning}" for e in cards if e.claim_id==c.claim_id and e.relation=="unclear"] or ["- 暂无"])
            lines += ["#### 仍需人工确认", *[f"- {x}" for x in (s.recommended_human_checks if s else ["补充证据"] )]]
        lines += ["","## Source 列表", *[f"- {e.title}: {e.url}" for e in cards], "","## AI 建议结论","以上为基于当前可获得证据的可靠性评估，不是绝对真理；人类保留最终裁决权。", "","## 人工最终裁决区","- 是否接受 AI 结论：","- 人工最终可靠性等级：","- 人工说明："]
        return "\n".join(lines)
