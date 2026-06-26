# 重明鸟 Chongmingniao Agent

面向新闻事实核查教学场景的联网事实核查智能体 Demo。

## 项目简介

“重明鸟”是一个用于新闻学院《事实与事实核查》课程的实验型智能体系统。它的目标不是训练一个新的大语言模型，而是基于现有大模型 API 搭建一个可解释、可追踪、可用于课堂实验的人机协同事实核查 Agent。

用户输入一段待核查消息后，系统会自动完成以下流程：

1. 拆解消息中的可核查事实主张；
2. 为每条主张生成搜索计划；
3. 联网检索相关网页和来源；
4. 读取网页正文并提取证据；
5. 判断证据与主张之间的关系；
6. 按新闻事实可靠性评价尺度进行评分；
7. 输出带有 source 的可解释核查报告；
8. 允许学生或教师进行人工裁决与修改；
9. 保存课堂实验过程数据，供后续研究分析。

本项目强调：AI 不直接取代事实核查员，而是辅助学生完成证据收集、信息比对和可靠性评估。最终判断权仍保留给人类。

## 项目目标

第一版 Demo 需要实现一个类似 Codex 工作方式的事实核查 Agent：

```text
用户输入待核查消息
        ↓
智能体拆解事实主张
        ↓
智能体规划搜索任务
        ↓
后端调用联网搜索工具
        ↓
读取网页并生成证据卡片
        ↓
根据可靠性评价尺度评分
        ↓
输出核查报告和 source
        ↓
学生进行人工裁决
        ↓
保存课堂实验日志
```

## 核心功能

### 1. 事实主张拆解

将用户输入的一段消息拆分为多个可核查事实主张。

例如：

```text
网传某地因为食品安全问题关闭了所有中小学食堂。
```

可拆解为：

```text
1. 某地发生食品安全问题。
2. 当地关闭了所有中小学食堂。
3. 食堂关闭是因为食品安全问题导致。
```

### 2. 搜索规划

针对每个事实主张，自动生成多角度搜索任务，包括：

* 官方来源搜索；
* 主流媒体搜索；
* 反证搜索；
* 时间线搜索；
* 原始出处搜索。

### 3. 联网搜索

通过搜索 API 获取真实网页来源，并记录：

* 标题；
* URL；
* 摘要；
* 发布时间；
* 来源域名；
* 搜索关键词；
* 搜索目的。

第一版 Demo 默认支持 mock/offline 模式，方便在没有 API Key 的情况下演示。

### 4. 网页读取

读取搜索结果网页正文，提取与事实核查相关的信息，包括：

* 网页标题；
* 正文片段；
* 发布时间；
* 来源机构；
* 关键摘录；
* 读取状态。

### 5. 证据卡片

每个来源会被转化为 Evidence Card，包含：

* 来源标题；
* URL；
* 来源类型；
* 发布时间；
* 证据摘录；
* 与主张关系；
* 证据强度；
* 判断理由。

证据关系包括：

```text
support              支持
refute               反驳
partially_support    部分支持
unclear              不明确
irrelevant           无关
```

### 6. 可靠性评分

第一版采用 V1 可靠性评价尺度：

| 维度       |  权重 | 含义                       |
| -------- | --: | ------------------------ |
| 信源权威性    | 20% | 官方机构、权威媒体、学术来源、当事人原始材料优先 |
| 证据直接性    | 20% | 证据是直接证明，还是间接推测           |
| 多源一致性    | 20% | 是否有多个独立来源相互印证            |
| 时间与语境一致性 | 15% | 是否存在旧闻新炒、断章取义、时间错位       |
| 反证强度     | 15% | 是否存在高质量反证                |
| 可追溯性     | 10% | 是否能追到原始文件、原始讲话、原始数据      |

最终可靠性等级：

|     分数 | 等级   | 说明                  |
| -----: | ---- | ------------------- |
| 85-100 | 高可信  | 多个高质量来源直接支持，几乎无有效反证 |
|  70-84 | 较可信  | 有较强证据支持，但仍有局部不确定    |
|  55-69 | 存疑   | 支持和反驳证据并存，或证据质量一般   |
|  40-54 | 较不可信 | 证据薄弱，存在明显矛盾或语境问题    |
|   0-39 | 不可信  | 高质量来源反驳，或关键事实错误     |
|    不计分 | 证据不足 | 找不到足够可靠来源，不能强行判断    |

评分模块应尽量由独立规则完成，而不是完全交给大模型自由打分。

### 7. 核查报告

最终生成 Markdown 格式核查报告，包含：

* 原始输入；
* 拆解出的事实主张；
* 每条主张的可靠性等级和评分；
* 支持证据；
* 反驳证据；
* 不确定证据；
* 判断理由；
* 仍需人工确认的问题；
* source 列表；
* AI 建议结论；
* 人工最终裁决区域。

### 8. 人工裁决

系统应允许学生或教师对 AI 结论进行修改：

* 接受 AI 结论；
* 部分接受 AI 结论；
* 不接受 AI 结论；
* 修改最终可靠性等级；
* 补充人工说明。

人工裁决结果需要写入数据库。

### 9. 课堂实验日志

每次核查应保存为一次 session，用于后续课堂研究。

至少记录：

* session_id；
* created_at；
* user_input；
* extracted_claims_json；
* search_trace_json；
* evidence_cards_json；
* ai_result_json；
* human_override_json；
* elapsed_seconds；
* demo_mode。

系统应支持导出 CSV。

## 推荐技术栈

第一版 Demo 计划使用：

```text
Python 3.10+
FastAPI
Gradio
DeepSeek API
Tavily API
SQLite
requests
trafilatura / BeautifulSoup
pydantic
pytest
```

其中：

* DeepSeek API 作为 Agent 大脑；
* Tavily API 作为联网搜索工具；
* FastAPI 作为后端；
* Gradio 作为演示前端；
* SQLite 保存课堂实验日志；
* mock 模式保证无 API Key 也能演示。

## 计划目录结构

```text
chongmingniao-agent/
  README.md
  requirements.txt
  .env.example
  app.py
  main.py
  config/
    rubric.yaml
  data/
    .gitkeep
  src/
    __init__.py
    settings.py
    schemas.py
    llm_client.py
    claim_extractor.py
    search_planner.py
    web_search.py
    page_reader.py
    evidence_analyzer.py
    rubric.py
    report_generator.py
    agent.py
    database.py
    api.py
    ui_gradio.py
    mock_data.py
  tests/
    test_rubric.py
    test_claim_extractor.py
    test_report_generator.py
  docs/
    ARCHITECTURE.md
    RUBRIC_V1.md
    SAMPLE_REPORT.md
```

## 环境变量

项目应使用 `.env` 管理配置。

示例：

```env
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

TAVILY_API_KEY=

DATABASE_URL=sqlite:///./data/chongmingniao.db

DEMO_MODE=true
```

当 `DEMO_MODE=true` 时，系统应使用 mock 数据，保证无 API Key 也能完整跑通。

## 启动方式

后续开发完成后，预计使用以下方式启动。

### 1. 创建虚拟环境

```bash
python -m venv .venv
```

Windows：

```bash
.venv\Scripts\activate
```

macOS / Linux：

```bash
source .venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
```

Windows 可以手动复制 `.env.example` 并重命名为 `.env`。

### 4. 启动 Gradio Demo

```bash
python app.py
```

### 5. 启动 FastAPI

```bash
uvicorn main:app --reload
```

### 6. 运行测试

```bash
pytest
```

## API 设计草案

### 健康检查

```http
GET /health
```

### 发起事实核查

```http
POST /api/fact-check
```

请求示例：

```json
{
  "text": "网传某地因为食品安全问题关闭了所有中小学食堂。",
  "demo_mode": true
}
```

### 查看历史记录

```http
GET /api/sessions
```

### 查看单次核查详情

```http
GET /api/sessions/{session_id}
```

### 保存人工裁决

```http
POST /api/sessions/{session_id}/human-override
```

### 导出课堂日志

```http
GET /api/export.csv
```

## Agent 行为原则

1. 不直接相信用户输入。
2. 不把搜索结果数量等同于真实性。
3. 优先寻找原始来源、官方通报、权威媒体、学术资料。
4. 必须同时寻找支持证据和反驳证据。
5. 不能在证据不足时强行判断真/假。
6. 必须保留 source。
7. 必须区分：

   * 已被证据支持的事实；
   * 被证据反驳的事实；
   * 尚不能确认的事实；
   * 推测性解释。
8. 最终结论应是可靠性评估，而不是绝对真理。
9. AI 只提供辅助判断，人类保留最终裁决权。
10. 所有流程都要可解释、可复盘、可教学使用。

## 第一版 Demo 验收标准

第一版 Demo 至少需要跑通以下流程：

1. 用户启动应用；
2. 打开 Gradio 页面；
3. 输入一段待核查消息；
4. 点击“开始核查”；
5. 页面实时显示 Agent 正在拆解、搜索、读取、分析、评分；
6. 系统展示证据卡片，每张卡片有 source URL；
7. 系统输出可靠性等级和评分；
8. 系统输出 Markdown 核查报告；
9. 用户可以人工修改结论并保存；
10. 数据写入 SQLite；
11. 用户可以导出 CSV；
12. pytest 测试通过。

## 当前状态

项目处于第一版 Demo 开发阶段。

当前重点不是部署正式系统，也不是训练新模型，而是先搭建一个可运行、可演示、可扩展的事实核查 Agent 原型。

## 后续计划

1. 完成第一版可运行 Demo；
2. 接入真实 DeepSeek API；
3. 接入真实 Tavily / Exa / Bing 搜索 API；
4. 优化新闻事实可靠性评价尺度；
5. 增加课堂实验数据分析面板；
6. 支持学生人工反诘与修改记录；
7. 后续根据 Wisepen 平台接口情况决定是否接入 Wisepen。
