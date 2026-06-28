# ChongmingBird Agent API 配置说明

## 1. 创建 `.env`

从示例文件复制一份本地配置：

```bash
cp .env.example .env
```

然后按需编辑 `.env`。请不要把 `.env`、真实 API Key、真实课堂日志或包含敏感信息的调试日志提交到 GitHub；仓库只应提交 `.env.example`。

## 2. DEMO_MODE=true 与 DEMO_MODE=false

### `DEMO_MODE=true`

- 适合课堂演示、离线调试和没有 API Key 的环境。
- 不需要 `DEEPSEEK_API_KEY`。
- 不需要 `TAVILY_API_KEY`。
- 系统使用 mock LLM、mock 搜索结果和 mock 网页正文，保证完整流程可跑通。
- 如果 source 仍然是 `example.edu.gov.cn`、`news.example.com`、`factcheck.example.org`，说明你仍在 Demo/mock 模式或仍在使用 mock 数据。

### `DEMO_MODE=false`

- 适合真实联网事实核查测试。
- 需要配置 DeepSeek API Key，供 Agent 做主张拆解和证据分析。
- 需要配置 Tavily API Key，供系统执行真实网页搜索。
- 网页读取仍可能受目标站点反爬、网络、动态渲染、登录墙影响。
- Gradio trace 会显示“当前模式：真实 API 模式”、DeepSeek 状态、Tavily 状态和 source 类型，可用来判断是否真的联网。

## 3. LLM / DeepSeek-compatible 配置项

项目不默认绑定某一个 LLM 服务。你可以使用 DeepSeek 官方 API、Paratera LLM API，或其他 OpenAI-compatible Chat Completions API。

1. 向你的 API 提供方申请 Key。
2. 复制 `.env.example` 为 `.env`。
3. 将 Key、Base URL 和模型名填入本地 `.env`，不要写入代码或文档。

通用模板：

```env
DEEPSEEK_API_KEY=你的 LLM API Key
DEEPSEEK_BASE_URL=你的 OpenAI-compatible Base URL
DEEPSEEK_MODEL=你的模型名
```

如果使用 Paratera LLM API，可类似：

```env
DEEPSEEK_API_KEY=你的Key
DEEPSEEK_BASE_URL=https://llmapi.paratera.com/v1
DEEPSEEK_MODEL=Qwen3-235B-A22B-Instruct-2507
```

如果使用 DeepSeek 官方 API，请根据 DeepSeek 官方文档填写 base URL 和 model。`DEEPSEEK_MODEL` 完全由用户配置，仓库不会写死默认模型。

## 4. Tavily 配置项

1. 在 Tavily 控制台申请 API Key。
2. 将 Key 填入本地 `.env`。
3. 设置 `DEMO_MODE=false` 后，系统会调用真实 Tavily Search API。

```env
TAVILY_API_KEY=你的 Tavily API Key
```

说明：Tavily 用于真实联网搜索。没有 Key 或 `DEMO_MODE=true` 时，系统会自动走 mock 搜索。真实请求使用 `Authorization: Bearer ${TAVILY_API_KEY}` header，不会把 Key 放入 JSON body。

## 5. 数据库配置

```env
DATABASE_URL=sqlite:///./data/chongmingbird.db
```

默认使用本地 SQLite，适合课堂 Demo。相对 SQLite 路径会解析到项目根目录下的 `data/`，避免从其他目录启动时写到错误位置。`data/*.db` 已被 `.gitignore` 忽略，不应提交课堂日志数据库。

## 6. 如何判断是否真的联网

- Gradio trace 显示：`[状态] 当前模式：真实 API 模式`。
- Tavily 状态显示：`搜索成功`。
- Evidence Card 中的 source URL 不应是 `example.edu.gov.cn`、`news.example.com`、`factcheck.example.org`。
- Trace 中 source 类型应显示 `real source`，而不是 `mock source`。
- DeepSeek 若成功，会显示 `DeepSeek 状态：调用成功`；若失败，会显示已回退到本地规则。

## 7. 真实联网失败的常见原因

- DeepSeek 或 Tavily API Key 填写错误。
- API 额度不足、账号未开通或被限流。
- 当前网络无法访问 API 服务。
- 搜索 API 返回结果过少或与查询词不匹配。
- 目标网页读取失败，例如反爬、登录墙、动态渲染、超时、证书问题。
- 目标网页没有清晰正文，导致正文抽取质量较低。

遇到失败时，建议先切回 `DEMO_MODE=true` 验证本地流程，再逐项检查 Key、额度和网络。
