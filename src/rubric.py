from pathlib import Path
try:
    import yaml
except Exception:
    yaml = None
from .schemas import EvidenceCard, ReliabilityScore
AUTH={"official":90,"academic":85,"mainstream_media":75,"other":55,"unknown":45,"social_media":30}
MOJIBAKE_MARKERS=("ã","å","æ","�","Â","¤","µ")
def quality_factor(card: EvidenceCard) -> float:
    text = card.excerpt or ""
    if not text:
        return 0.85
    marker_count=sum(text.count(marker) for marker in MOJIBAKE_MARKERS)
    if marker_count / max(1, len(text)) > 0.03:
        return 0.55
    if card.source_type in ("official","mainstream_media"):
        return 1.0
    if card.source_type == "other" and card.evidence_strength < 90:
        return 0.85
    return 0.9
class ReliabilityRubric:
    def __init__(self, path="config/rubric.yaml"):
        cfg=yaml.safe_load(Path(path).read_text(encoding="utf-8")) if (yaml and Path(path).exists()) else {}
        self.weights=cfg.get("weights",{"source_authority":.2,"evidence_directness":.2,"multi_source_consistency":.2,"temporal_context_consistency":.15,"counter_evidence_strength":.15,"traceability":.1})
    def score_claim(self, claim_id:str, cards:list[EvidenceCard])->ReliabilityScore:
        cs=[c for c in cards if c.claim_id==claim_id and c.relation!="irrelevant"]
        if not cs:
            return ReliabilityScore(claim_id=claim_id,reliability_level="证据不足",dimension_scores={},explanation="未获得可用证据，不能强行判断。",key_uncertainties=["缺少可追溯来源"],recommended_human_checks=["补充官方或原始来源检索"])
        authority=round(sum(AUTH.get(c.source_type,45) for c in cs)/len(cs))
        direct_support_cards=[c for c in cs if c.relation=="support"]
        partial_support_cards=[c for c in cs if c.relation=="partially_support"]
        refute_cards=[c for c in cs if c.relation=="refute"]
        support=sum(round(c.evidence_strength * quality_factor(c)) for c in [*direct_support_cards,*partial_support_cards])
        refute=sum(round(c.evidence_strength * quality_factor(c)) for c in refute_cards)
        if support == 0 and refute == 0:
            return ReliabilityScore(claim_id=claim_id,total_score=None,reliability_level="证据不足",dimension_scores={},explanation=f"找到 {len(cs)} 条相关或不明确证据，但没有支持或反驳主张的有效证据，不能据此判为不可信。",key_uncertainties=["现有证据均为 unclear 或无直接证明力"],recommended_human_checks=["补充直接来源或权威报道"])
        direct=round(min(100,max(support,refute)/max(1,len(cs))))
        domains={c.domain for c in cs}; consistency=80 if len(domains)>=2 and (support==0 or refute==0) else (55 if support and refute else 65)
        temporal=70 if any(c.published_date for c in cs) else 55
        counter= max(0,100-round(refute/max(1,support+refute)*100)) if support else max(0,40-round(refute/len(cs)))
        trace=80 if any(c.source_type in ("official","academic") for c in cs) else 55
        dims={"source_authority":authority,"evidence_directness":direct,"multi_source_consistency":consistency,"temporal_context_consistency":temporal,"counter_evidence_strength":counter,"traceability":trace}
        total=round(sum(dims[k]*self.weights[k] for k in self.weights))
        high_quality_supports=[c for c in direct_support_cards if c.source_type in ("official","mainstream_media") and c.evidence_strength >= 85 and quality_factor(c) >= 0.85]
        if len(direct_support_cards) >= 2 and high_quality_supports and refute == 0:
            total=max(total,85)
        elif direct_support_cards and max(c.evidence_strength for c in direct_support_cards) >= 80 and refute == 0:
            total=max(total,70)
        if len(direct_support_cards) >= 2 and refute == 0 and any(c.source_type in ("official","mainstream_media") for c in direct_support_cards):
            total=max(total,78)
        if refute>support*1.2: total=min(total,54)
        level="高可信" if total>=85 else "较可信" if total>=70 else "存疑" if total>=55 else "较不可信" if total>=40 else "不可信"
        return ReliabilityScore(claim_id=claim_id,total_score=total,reliability_level=level,dimension_scores=dims,explanation=f"基于 {len(cs)} 条证据计算；质量调整后支持强度 {support}，反驳强度 {refute}。",key_uncertainties=["需确认来源是否为最新上下文", "需核对是否存在未检索到的原始材料"],recommended_human_checks=["查看 source 原文", "补充当地官方渠道和原始出处"])
