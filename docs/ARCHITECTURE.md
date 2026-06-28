# Architecture

ChongmingBird Agent uses FastAPI for APIs, Gradio for the classroom demo UI, DeepSeek-compatible chat completions for reasoning, Tavily for web search, and SQLite for classroom logs. In DEMO_MODE it uses deterministic mock LLM/search/page content so the full workflow runs offline.

Pipeline: input -> claim extraction -> search planning -> search -> page reading -> evidence analysis -> rubric scoring -> Markdown report -> human override -> SQLite log.
