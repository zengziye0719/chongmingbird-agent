from .schemas import Claim, SearchTask
class SearchPlanner:
    def plan(self, claims: list[Claim]) -> list[SearchTask]:
        kinds=[("官方来源搜索","official","官方通报/公告"),("主流媒体搜索","mainstream_media","新闻报道"),("反证搜索","fact_check","辟谣或相反证据"),("时间线搜索","timeline","日期与背景"),("原始出处搜索","primary","原始文件/源头")]
        tasks=[]
        for c in claims:
            for purpose,stype,etype in kinds:
                q=f"{c.claim_text} {purpose.replace('搜索','')}"
                tasks.append(SearchTask(claim_id=c.claim_id,query=q,purpose=purpose,preferred_source_type=stype,expected_evidence_type=etype))
        return tasks
