from __future__ import annotations
from typing import Any, Literal
try:
    from pydantic import BaseModel, Field
except Exception:  # lightweight fallback for offline test environments
    def Field(default=None, default_factory=None, **_):
        return default_factory() if default_factory else default
    class BaseModel:
        def __init__(self, **kwargs):
            anns=getattr(self,'__annotations__',{})
            for k,v in anns.items():
                if k not in kwargs and hasattr(self.__class__, k):
                    dv=getattr(self.__class__, k); setattr(self,k,dv.copy() if isinstance(dv,(list,dict)) else dv)
            for k,v in kwargs.items(): setattr(self,k,v)
        def model_dump(self): return dict(self.__dict__)

Checkability = Literal["高", "中", "低"]
Relation = Literal["support", "refute", "partially_support", "unclear", "irrelevant"]
SourceType = Literal["official", "mainstream_media", "academic", "social_media", "unknown", "other"]
class Claim(BaseModel):
    claim_id: str; claim_text: str; checkability: Checkability = "中"; reason: str = ""; suggested_search_angles: list[str] = Field(default_factory=list)
class SearchTask(BaseModel):
    claim_id: str; query: str; purpose: str; preferred_source_type: str; expected_evidence_type: str
class SearchResult(BaseModel):
    title: str; url: str; snippet: str = ""; published_date: str | None = None; source_domain: str = ""; raw_rank: int = 0
class PageEvidence(BaseModel):
    title: str; url: str; domain: str = ""; published_date: str | None = None; text_excerpt: str = ""; full_text: str = ""; fetch_status: str = "ok"; error: str | None = None
class EvidenceCard(BaseModel):
    evidence_id: str; claim_id: str; title: str; url: str; domain: str = ""; source_type: SourceType = "unknown"; published_date: str | None = None; excerpt: str = ""; relation: Relation = "unclear"; evidence_strength: int = Field(default=0, ge=0, le=100); reasoning: str = ""
class ReliabilityScore(BaseModel):
    claim_id: str; total_score: int | None = None; reliability_level: str; dimension_scores: dict[str, int]; explanation: str; key_uncertainties: list[str] = Field(default_factory=list); recommended_human_checks: list[str] = Field(default_factory=list)
class FactCheckResult(BaseModel):
    session_id: str; claims: list[Claim]; search_trace: list[dict[str, Any]]; evidence_cards: list[EvidenceCard]; scores: list[ReliabilityScore]; report: str; elapsed_seconds: float; demo_mode: bool
class HumanOverride(BaseModel):
    acceptance: str; final_reliability_level: str | None = None; human_notes: str = ""
