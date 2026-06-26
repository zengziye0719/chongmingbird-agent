import re
from .schemas import Claim
from .llm_client import LLMClient

class ClaimExtractor:
    def __init__(self, demo_mode: bool=True): self.llm=LLMClient(demo_mode)
    def extract(self, text: str) -> list[Claim]:
        fallback=self._heuristic(text)
        data=self.llm.chat_json([{"role":"user","content":"将文本拆解为可核查事实主张，JSON: {claims:[{claim_id,claim_text,checkability,reason,suggested_search_angles}]}\n"+text}], {"claims":[c.model_dump() for c in fallback]})
        return [Claim(**c) for c in data.get("claims", [])] or fallback
    def _heuristic(self,text):
        parts=[p.strip() for p in re.split(r"[。！？；;\n]+", text) if p.strip()]
        if not parts: parts=[text.strip() or "空输入"]
        claims=[]
        for i,p in enumerate(parts,1):
            claims.append(Claim(claim_id=f"C{i}",claim_text=p,checkability="中",reason="包含可通过公开来源交叉验证的事实性表述。",suggested_search_angles=["官方通报", "主流媒体报道", "反证与辟谣", "时间线", "原始出处"]))
        if len(claims)==1 and ("因为" in text or "导致" in text):
            claims.append(Claim(claim_id="C2",claim_text="该事件的原因链条是否成立："+text,checkability="中",reason="因果关系需要独立证据支持。",suggested_search_angles=["原因说明", "官方调查", "媒体追踪"]))
        return claims
