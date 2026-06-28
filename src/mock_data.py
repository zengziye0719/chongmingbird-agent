"""Deterministic mock sources for classroom demo scenarios."""
from __future__ import annotations

MOCK_CASE_RESULTS = {
    "true": [
        {
            "title": "市教育局关于新增20所课后服务试点学校的通知",
            "url": "https://example.edu.gov.cn/notice/after-school-pilot-2026",
            "snippet": "市教育局通知显示，2026年春季学期新增20所学校开展课后服务试点。",
            "published_date": "2026-02-18",
            "source_domain": "example.edu.gov.cn",
        },
        {
            "title": "本地日报：20所学校纳入课后服务试点",
            "url": "https://news.example.com/education/after-school-pilot",
            "snippet": "本地日报报道，教育局公布新增课后服务试点学校名单。",
            "published_date": "2026-02-19",
            "source_domain": "news.example.com",
        },
    ],
    "false": [
        {
            "title": "市教育局发布中小学食堂管理情况说明",
            "url": "https://example.edu.gov.cn/notice/canteen-safety",
            "snippet": "教育局称个别学校食堂暂停整改，并未关闭所有中小学食堂。",
            "published_date": "2026-03-12",
            "source_domain": "example.edu.gov.cn",
        },
        {
            "title": "网传全市学校食堂关闭不实",
            "url": "https://factcheck.example.org/school-canteen-rumor",
            "snippet": "核查发现传言夸大范围，关闭原因也被简化。",
            "published_date": "2026-03-14",
            "source_domain": "factcheck.example.org",
        },
    ],
    "mixed": [
        {
            "title": "本地媒体：三所学校食堂因检查不合格暂停供餐",
            "url": "https://news.example.com/canteen-check",
            "snippet": "市场监管部门检查后，三所学校食堂临时停业整改。",
            "published_date": "2026-03-13",
            "source_domain": "news.example.com",
        },
        {
            "title": "县教育局：不存在全县所有学校停止供餐",
            "url": "https://example.edu.gov.cn/notice/county-canteen-clarification",
            "snippet": "通报称三所学校食堂整改属实，但全县所有学校停止供餐不实。",
            "published_date": "2026-03-13",
            "source_domain": "example.edu.gov.cn",
        },
    ],
    "insufficient": [],
    "old_news": [
        {
            "title": "2019年学校食品安全检查报道被误传为今日事件",
            "url": "https://factcheck.example.org/old-canteen-photo-2019",
            "snippet": "核查显示，网传配图来自2019年报道，并非今日学校食堂大面积停餐。",
            "published_date": "2026-06-01",
            "source_domain": "factcheck.example.org",
        },
        {
            "title": "2019年某市学校食品安全专项检查新闻",
            "url": "https://news.example.com/archive/2019-school-canteen-check",
            "snippet": "2019年旧报道记录了一次学校食品安全专项检查。",
            "published_date": "2019-09-10",
            "source_domain": "news.example.com",
        },
    ],
}

MOCK_PAGE_TEXT_BY_URL = {
    "https://example.edu.gov.cn/notice/after-school-pilot-2026": "官方通知称，某市教育局决定在2026年春季学期新增20所学校开展课后服务试点，并公布了试点学校名单、服务时间和监督电话。",
    "https://news.example.com/education/after-school-pilot": "本地日报援引市教育局通知报道，2026年春季学期将新增20所学校课后服务试点，报道内容与教育局通知一致。",
    "https://example.edu.gov.cn/notice/canteen-safety": "官方通报显示，近期食品安全检查中发现个别学校食堂存在管理问题，相关食堂暂停供餐并整改。通报未提及关闭所有中小学食堂，也未说明全市范围停餐。",
    "https://factcheck.example.org/school-canteen-rumor": "事实核查发现，网传所有中小学食堂关闭不实。实际情况是个别食堂整改，传言夸大范围，且关闭原因被简化。",
    "https://news.example.com/canteen-check": "本地媒体报道，三所学校食堂因检查不合格临时暂停供餐并整改。报道没有支持全县所有学校停止供餐的说法。",
    "https://example.edu.gov.cn/notice/county-canteen-clarification": "县教育局通报称，三所学校食堂整改属实，但全县所有学校停止供餐不实，其他学校供餐正常。",
    "https://factcheck.example.org/old-canteen-photo-2019": "核查显示，网传图片来自2019年学校食品安全检查报道，并非今天发生的学校食堂大面积停餐。该传播属于旧闻新炒和时间错位。",
    "https://news.example.com/archive/2019-school-canteen-check": "这是一篇2019年9月的旧报道，内容为某市学校食品安全专项检查，不是当前日期发生的新事件。",
}

# Backward-compatible alias used by earlier tests/imports.
MOCK_SEARCH_RESULTS = MOCK_CASE_RESULTS["false"]
MOCK_PAGE_TEXT = MOCK_PAGE_TEXT_BY_URL["https://example.edu.gov.cn/notice/canteen-safety"]


def mock_case_key(text: str) -> str:
    haystack = text.lower()
    if any(keyword in haystack for keyword in ["课后服务", "试点", "新增20所"]):
        return "true"
    if any(keyword in haystack for keyword in ["三所学校", "全县所有", "检查不合格"]):
        return "mixed"
    if any(keyword in haystack for keyword in ["证据不足", "网上都被删", "有个学校", "听说"]):
        return "insufficient"
    if any(keyword in haystack for keyword in ["旧闻", "旧报道", "2019", "配图", "今天"]):
        return "old_news"
    if any(keyword in haystack for keyword in ["食堂", "食品安全", "关闭了所有", "关闭所有"]):
        return "false"
    return "insufficient"


def mock_search_results_for(text: str) -> list[dict]:
    return MOCK_CASE_RESULTS[mock_case_key(text)]


def mock_page_text_for_url(url: str) -> str:
    return MOCK_PAGE_TEXT_BY_URL.get(url, "该 mock source 仅用于流程演示，未提供更多正文。")
