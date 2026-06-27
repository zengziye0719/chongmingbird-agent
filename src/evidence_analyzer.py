from .schemas import Claim, PageEvidence, EvidenceCard
class EvidenceAnalyzer:
    def analyze(self, claim: Claim, page: PageEvidence, idx:int)->EvidenceCard:
        text=(page.full_text+" "+claim.claim_text).lower()
        relation="unclear"; strength=45; reason="证据仅提供背景，无法完全确认主张。"
        if any(w in page.full_text for w in ["未提及关闭所有", "不实", "并未关闭所有", "夸大"]):
            relation="refute"; strength=82; reason="来源明确指出传言范围被夸大或关键表述不成立。"
        elif any(w in page.full_text for w in ["暂停", "整改", "通报显示", "检查"]):
            relation="partially_support"; strength=66; reason="证据支持存在相关整改/暂停供餐事实，但不足以支持全部表述。"
        st="official" if ".gov" in page.domain or "edu.gov" in page.domain else ("mainstream_media" if "news" in page.domain else "other")
        return EvidenceCard(evidence_id=f"E{idx}",claim_id=claim.claim_id,title=page.title,url=page.url,domain=page.domain,source_type=st,published_date=page.published_date,excerpt=page.text_excerpt[:500],relation=relation,evidence_strength=strength,reasoning=reason)
