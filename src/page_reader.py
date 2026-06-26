from urllib.parse import urlparse
try:
    import requests
except Exception:
    requests = None
try:
    import trafilatura
except Exception:
    trafilatura = None
try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None
from .schemas import SearchResult, PageEvidence
from .mock_data import MOCK_PAGE_TEXT
class PageReader:
    def __init__(self,demo_mode=True): self.demo_mode=demo_mode
    def read(self,result:SearchResult)->PageEvidence:
        if self.demo_mode or result.url.startswith("https://example") or requests is None:
            return PageEvidence(title=result.title,url=result.url,domain=result.source_domain,published_date=result.published_date,text_excerpt=MOCK_PAGE_TEXT[:500],full_text=MOCK_PAGE_TEXT)
        try:
            html=requests.get(result.url,timeout=15,headers={"User-Agent":"ChongmingBirdAgent/0.1"}).text
            text=(trafilatura.extract(html) if trafilatura else None) or (BeautifulSoup(html,"html.parser").get_text(" ",strip=True) if BeautifulSoup else html)
            return PageEvidence(title=result.title,url=result.url,domain=urlparse(result.url).netloc,published_date=result.published_date,text_excerpt=(text or result.snippet)[:800],full_text=(text or result.snippet)[:6000])
        except Exception as e:
            return PageEvidence(title=result.title,url=result.url,domain=result.source_domain,published_date=result.published_date,fetch_status="failed",error=str(e),text_excerpt=result.snippet,full_text=result.snippet)
