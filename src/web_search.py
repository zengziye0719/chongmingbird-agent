from urllib.parse import urlparse
try:
    import requests
except Exception:
    requests = None
from .settings import get_settings
from .schemas import SearchResult, SearchTask
from .mock_data import MOCK_SEARCH_RESULTS
class WebSearchTool:
    def __init__(self,demo_mode=True): self.settings=get_settings(); self.demo_mode=demo_mode
    def search(self, task: SearchTask, max_results:int=3)->list[SearchResult]:
        if self.demo_mode or not self.settings.tavily_api_key or requests is None:
            return [SearchResult(**{**r,"raw_rank":i+1}) for i,r in enumerate(MOCK_SEARCH_RESULTS[:max_results])]
        try:
            resp=requests.post("https://api.tavily.com/search",json={"api_key":self.settings.tavily_api_key,"query":task.query,"max_results":max_results,"include_answer":False},timeout=20); resp.raise_for_status()
            out=[]
            for i,r in enumerate(resp.json().get("results",[]),1):
                url=r.get("url",""); out.append(SearchResult(title=r.get("title",url),url=url,snippet=r.get("content",""),published_date=r.get("published_date"),source_domain=urlparse(url).netloc,raw_rank=i))
            return out
        except Exception as e:
            return [SearchResult(title="搜索失败",url="https://example.invalid/search-error",snippet=str(e),source_domain="example.invalid",raw_rank=0)]
