# ChongmingBird Agent v0.3 演示原型 Test Log

## 测试环境

- 日期：2026-06-27
- 工作目录：`/workspace/chongmingbird-agent`
- Shell：`bash`
- Python：`Python 3.14.4`
- 目标：v0.4 演示前加固，保持 v0.3 演示原型稳定可运行。

## 测试结果汇总

| 检查项 | 命令 | 结果 |
| --- | --- | --- |
| 单元/集成测试 | `python -m pytest` | 通过：`21 passed, 2 skipped` |
| Demo 模式无 API Key 运行 | `env -u DEEPSEEK_API_KEY -u TAVILY_API_KEY DEMO_MODE=true python - <<'PY' ... PY` | 通过：生成 session、claims、evidence cards、scores |
| JSON 样例校验 | `python -m json.tool data/sample_cases.json >/tmp/sample_cases.pretty` | 通过 |
| 语法编译检查 | `python -m compileall -q src tests` | 通过 |
| Gradio 启动 | `python app.py` | 通过：本地监听 `http://127.0.0.1:7860`，HTTP 200 |
| FastAPI 启动 | `python -m uvicorn main:app --host 127.0.0.1 --port 8000` | 通过：应用启动完成 |
| FastAPI endpoints | `curl /health`、`POST /api/fact-check`、`GET /api/sessions`、`GET /api/export.csv` | 通过：均返回 200 或有效内容 |

## 详细输出摘录

### pytest

```text
21 passed, 2 skipped in 0.25s
```

### Demo 模式无 API Key

```text
{'session_id': '74e987a5-5593-4a64-8039-ed2e6ce1c2c1', 'claims': 2, 'evidence_cards': 6, 'score': '较不可信'}
```

含义：无需 DeepSeek/Tavily API Key，Agent 成功生成 session id、claims、evidence cards 和可靠性评分。

### Gradio 启动

```text
* Running on local URL:  http://127.0.0.1:7860
```

随后执行：

```bash
curl -s -I http://127.0.0.1:7860
```

返回：

```text
HTTP/1.1 200 OK
```

### FastAPI endpoints

启动：

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

检查结果摘录：

```text
GET /health -> {"status":"ok"}
POST /api/fact-check -> {'session_id': '...', 'claims': 2, 'evidence_cards': 6, 'scores': 2}
GET /api/sessions -> 返回 session 列表
GET /api/export.csv -> 返回 CSV，包含 session_id 表头
```

## v0.3 验收结论

- `DEMO_MODE=true` 的核心 Agent 流程已验证：不需要 DeepSeek/Tavily API Key。
- Gradio v0.3 演示原型可启动，并能加载页面。
- FastAPI 可启动，核心 endpoints 可用。
- SQLite session 保存、人工裁决保存、CSV 导出路径由测试覆盖。
- 网页读取失败不会导致整体流程崩溃，由测试覆盖。
- 本轮仅做 v0.4 演示前加固，没有引入 React、Docker、登录系统或复杂部署。

## 真实 API smoke test 步骤（v0.3 接入验收）

> 不要在文档、测试日志、截图或 Git 提交中写入真实 API Key。

1. 复制 `.env` 并填写真实 Key：

```bash
cp .env.example .env
```

```env
DEEPSEEK_API_KEY=你的 DeepSeek API Key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
TAVILY_API_KEY=你的 Tavily API Key
DEMO_MODE=false
```

2. 启动 Gradio 或 FastAPI：

```bash
python app.py
# 或
python -m uvicorn main:app --reload
```

3. 测试输入：

```text
2024年夏季奥运会在法国巴黎举办。
```

4. 预期结果：

- Evidence cards 中出现真实 URL。
- Source 不应是 `example.edu.gov.cn`、`news.example.com`、`factcheck.example.org`。
- Tavily 状态显示搜索成功。
- DeepSeek 若成功，应显示调用成功；若失败，应明确显示已回退到本地规则。
- 报告仍能正常生成。
- SQLite 能保存 session。
- CSV 能导出。

## 5 个 sample case 的 Demo/mock 验收

Demo 模式现在按输入内容选择对应 mock source，不再把所有案例都套用“中小学食堂食品安全”证据。

| 类别 | 示例主题 | 预期 mock source | 验收重点 |
| --- | --- | --- | --- |
| 真实 | 课后服务试点 | `https://example.edu.gov.cn/notice/after-school-pilot-2026`、`https://news.example.com/education/after-school-pilot` | 返回课后服务相关支持证据，不应出现食堂关闭 source |
| 虚假 | 所有中小学食堂关闭 | `https://example.edu.gov.cn/notice/canteen-safety`、`https://factcheck.example.org/school-canteen-rumor` | 返回食堂整改/并未关闭所有食堂的反驳证据 |
| 半真半假 | 三所学校暂停供餐被扩大为全县停餐 | `https://news.example.com/canteen-check`、`https://example.edu.gov.cn/notice/county-canteen-clarification` | 同时体现“三所学校整改属实”和“全县所有学校停餐不实” |
| 证据不足 | 缺少具体地点和时间的传言 | 空结果 | 输出“证据不足”或低置信，不硬套其他案例 source |
| 旧闻新炒 | 2019 年旧图被当作今日事件 | `https://factcheck.example.org/old-canteen-photo-2019`、`https://news.example.com/archive/2019-school-canteen-check` | 返回带旧日期/时间错位的 mock source |

自动化测试覆盖：课后服务案例不返回食堂 source、同一 claim 下 URL 不重复生成 evidence card、证据不足案例不硬判反驳。

## 真实 API evidence relation 修复记录

- 当前真实 API 已成功接通 Qwen/Tavily：LLM 状态可显示调用成功，Tavily 状态可显示搜索成功。
- 旧问题：真实搜索已找到新华网等 source，但 EvidenceAnalyzer 依赖 Demo 关键词规则，导致 evidence relation 全部为 `unclear`，可靠性被误判为“较不可信”。
- 修复目标：真实 API 模式下 EvidenceAnalyzer 优先调用 LLM 判断 evidence relation；LLM 失败或返回 malformed JSON 时回退本地规则；最终可靠性仍由 `rubric.py` 计算。
- 测试案例：`2024年奥运会在法国巴黎举办。`
- 预期：当证据写明“国际奥委会最终确定巴黎为2024年夏季奥运会举办地”时，EvidenceAnalyzer 输出 `support`，强度不低于 85；最终可靠性不应为“较不可信”。
- 界面区别：Demo 模式显示示例案例；真实 API 模式隐藏示例案例，用户应手动输入待核查消息。

## 人工裁决区默认值与保存校验

- 人工裁决不是系统默认生成的结论。
- “是否接受 AI 结论”初始不选中任何项。
- “人工最终可靠性等级”初始为 `--请选择--`。
- 未选择接受状态或最终等级时，保存按钮会提示：`请先选择是否接受 AI 结论，并选择人工最终可靠性等级。`
- 未提交人工裁决的 session 在数据库/CSV 中记录为 `未提交人工裁决`。
