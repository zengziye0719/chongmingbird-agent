# ChongmingBird Agent v0.1 Demo Test Log

## 测试环境

- 日期：2026-06-27
- 工作目录：`/workspace/chongmingbird-agent`
- Shell：`bash`
- Python：`Python 3.14.4`
- 说明：当前容器可以运行项目内不依赖外部包的 mock/pytest 路径，但访问 PyPI 时被网络代理拒绝，导致无法在本容器内安装 FastAPI/Gradio/Uvicorn 等依赖。

## 测试结果汇总

| 检查项 | 命令 | 结果 |
| --- | --- | --- |
| 单元/集成测试 | `python -m pytest` | 通过：`7 passed, 1 skipped` |
| Demo 模式无 API Key 运行 | `env -u DEEPSEEK_API_KEY -u TAVILY_API_KEY DEMO_MODE=true python - <<'PY' ... PY` | 通过：生成 session、claims、evidence cards、scores |
| 语法编译检查 | `python -m compileall -q src tests` | 通过 |
| 安装依赖 | `python -m pip install -r requirements.txt` | 环境限制：PyPI 访问返回 `403 Forbidden` |
| Gradio 启动 | `timeout 5 python app.py` | 环境限制：当前容器未安装 `gradio`；安装依赖后用 `python app.py` 启动 |
| FastAPI 启动 | `timeout 5 python -m uvicorn main:app --reload` | 环境限制：当前容器未安装 `uvicorn`；安装依赖后用该命令启动 |

## 详细输出摘录

### pytest

```text
7 passed, 1 skipped in 0.13s
```

`tests/test_api.py` 使用 `pytest.importorskip("fastapi")`，因此在当前未安装 FastAPI 的容器中跳过；在完成 `pip install -r requirements.txt` 的正常环境中会运行 FastAPI endpoint 测试。

### Demo 模式无 API Key

```text
ed639ec4-8bac-4b1b-ad44-7c3c7e0e6af3 2 6 较不可信
```

含义：无需 DeepSeek/Tavily API Key，Agent 成功生成 session id、2 条 claims、6 张 evidence cards 和可靠性评分。

### PyPI 安装限制

```text
ERROR: Could not find a version that satisfies the requirement fastapi>=0.111 (from versions: none)
ERROR: No matching distribution found for fastapi>=0.111
```

该错误由当前执行环境的包索引访问限制触发，前置日志显示 `Tunnel connection failed: 403 Forbidden`。在可访问 PyPI 的本地/课堂电脑中，应先运行：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## v0.1 验收结论

- `DEMO_MODE=true` 的核心 Agent 流程已验证：不需要 DeepSeek/Tavily API Key。
- SQLite session 保存、人工裁决保存、CSV 导出路径由测试覆盖。
- 网页读取失败不会导致整体流程崩溃，由测试覆盖。
- Gradio/FastAPI 启动命令已在 README 中记录；当前容器因无法安装依赖未能实际启动服务。
