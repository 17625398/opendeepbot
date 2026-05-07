# DeepTutor — Agent-Native Architecture
# DeepTutor — Agent-Native 架构

## Overview / 概述

DeepTutor is an **agent-native** intelligent learning companion built around
a two-layer plugin model (Tools + Capabilities) with three entry points:
CLI, WebSocket API, and Python SDK.
# DeepTutor 是一个**面向 Agent 原生**的智能学习助手，构建在双层插件模型（工具 + 能力）之上，提供三个入口：CLI、WebSocket API 和 Python SDK。

## Architecture / 架构

```
Entry Points:  CLI (Typer)  |  WebSocket /api/v1/ws  |  Python SDK
                    ↓                   ↓                   ↓
              ┌─────────────────────────────────────────────────┐
              │              ChatOrchestrator                    │
              │   routes to ChatCapability (default)             │
              │   or a selected deep Capability                  │
              └──────────┬──────────────┬───────────────────────┘
                         │              │
              ┌──────────▼──┐  ┌────────▼──────────┐
              │ ToolRegistry │  │ CapabilityRegistry │
              │  (Level 1)   │  │   (Level 2)        │
              └──────────────┘  └────────────────────┘
```

### Level 1 — Tools / 第一层 — 工具

Lightweight single-function tools the LLM calls on demand:
# LLM 按需调用的轻量级单功能工具：

| Tool / 工具              | Description / 描述                                    |
| ----------------------- | ---------------------------------------------------- |
| `rag`                   | Knowledge base retrieval (RAG) / 知识库检索 (RAG)              |
| `web_search`            | Web search with citations / 带引用的网络搜索                    |
| `code_execution`        | Sandboxed Python execution / 沙箱 Python 执行                 |
| `reason`                | Dedicated deep-reasoning LLM call / 专用深度推理 LLM 调用       |
| `brainstorm`            | Breadth-first idea exploration with rationale / 带推理的广度优先创意探索 |
| `paper_search`          | arXiv academic paper search / arXiv 学术论文搜索            |
| `geogebra_analysis`     | Image → GeoGebra commands (4-stage vision pipeline) / 图片 → GeoGebra 命令（四阶段视觉流水线） |
| `deepseek_code_edit`    | Apply code patches in diff format (DeepSeek V4) / 以 diff 格式应用代码补丁（DeepSeek V4） |
| `lsp_diagnostic`        | Post-edit LSP diagnostics (pyright/rust-analyzer) / 编辑后 LSP 诊断（pyright/rust-analyzer） |

### Level 2 — Capabilities / 第二层 — 能力

Multi-step agent pipelines that take over the conversation:
# 接管对话的多步骤 Agent 流水线：

| Capability / 能力       | Stages / 阶段                                       |
| ---------------------- | -------------------------------------------------- |
| `chat`                 | responding (default, tool-augmented) / 响应（默认，工具增强） |
| `deep_solve`          | planning → reasoning → writing / 规划 → 推理 → 写作     |
| `deep_question`        | ideation → evaluation → generation → validation / 创意 → 评估 → 生成 → 验证 |
| `deep_coding`          | plan → code → review → test (DeepSeek V4) / 规划 → 编码 → 审查 → 测试（DeepSeek V4） |

### Playground Plugins / Playground 插件

Extended features in `deeptutor/plugins/`:
# `deeptutor/plugins/` 中的扩展功能：

| Plugin / 插件           | Type / 类型      | Description / 描述                          |
| ---------------------- | --------------- | ------------------------------------------ |
| `deep_research`        | playground      | Multi-agent research + reporting / 多 Agent 研究与报告 |

## CLI Usage / CLI 使用方法

```bash
# Install CLI / 安装 CLI
pip install -r requirements/cli.txt && pip install -e .

# Run any capability (agent-first entry point) / 运行任何能力（Agent 优先入口）
deeptutor run chat "Explain Fourier transform"
deeptutor run deep_solve "Solve x^2=4" -t rag --kb my-kb
deeptutor run deep_question "Linear algebra" --config num_questions=5

# Interactive REPL / 交互式 REPL
deeptutor chat
# (inside the REPL: /regenerate or /retry re-runs the last user message)
# (REPL 内：/regenerate 或 /retry 重新运行上一条用户消息)

# Knowledge bases / 知识库
deeptutor kb list
deeptutor kb create my-kb --doc textbook.pdf

# Plugins & memory / 插件与记忆
deeptutor plugin list
deeptutor memory show

# API server (requires server.txt) / API 服务器（需要 server.txt）
deeptutor serve --port 8001
```

## Key Files / 关键文件

| Path / 路径                            | Purpose / 用途                                    |
| ------------------------------------- | ------------------------------------------------ |
| `deeptutor/runtime/orchestrator.py`       | ChatOrchestrator — unified entry / 统一入口            |
| `deeptutor/core/stream.py`                | StreamEvent protocol (+ REASONING_CONTENT, COST_UPDATE) / 流事件协议（+ REASONING_CONTENT, COST_UPDATE） |
| `deeptutor/core/stream_bus.py`             | Async event fan-out / 异步事件分发                        |
| `deeptutor/core/tool_protocol.py`          | BaseTool abstract class / BaseTool 抽象类              |
| `deeptutor/core/capability_protocol.py`    | BaseCapability abstract class / BaseCapability 抽象类   |
| `deeptutor/core/context.py`               | UnifiedContext dataclass / UnifiedContext 数据类          |
| `deeptutor/runtime/registry/tool_registry.py`      | Tool discovery & registration / 工具发现与注册         |
| `deeptutor/runtime/registry/capability_registry.py`| Capability discovery & registration / 能力发现与注册    |
| `deeptutor/runtime/mode.py`                | RunMode (CLI vs SERVER) / RunMode（CLI vs SERVER）    |
| `deeptutor/capabilities/`                  | Built-in capability wrappers / 内置能力封装             |
| `deeptutor/tools/builtin/`                 | Built-in tool wrappers / 内置工具封装                  |
| `deeptutor/plugins/`                       | Playground plugins / Playground 插件                  |
| `deeptutor/plugins/loader.py`              | Plugin discovery from manifest.yaml / 从 manifest.yaml 发现插件 |
| `deeptutor_cli/main.py`                    | Typer CLI entry point / Typer CLI 入口                |
| `deeptutor/api/routers/unified_ws.py`     | Unified WebSocket endpoint / 统一 WebSocket 端点         |
| `deeptutor/services/llm/auto_mode.py`     | Auto mode (model+reasoning router) / 自动模式（模型+推理路由） |
| `deeptutor/tools/builtin/code_edit_tool.py`| DeepSeek code edit tool / DeepSeek 代码编辑工具            |
| `deeptutor/tools/builtin/lsp_tool.py`      | LSP diagnostic tool / LSP 诊断工具                     |
| `deeptutor/capabilities/deep_coding.py`    | DeepCoding capability (plan→code→review→test) / DeepCoding 能力（规划→编码→审查→测试） |

## Plugin Development / 插件开发

Create a directory under `deeptutor/plugins/<name>/` with:
# 在 `deeptutor/plugins/<name>/` 下创建目录，包含：

```
manifest.yaml     # name, version, type, description, stages
capability.py     # class extending BaseCapability
```

Minimal `manifest.yaml`:
# 最小 `manifest.yaml`：

```yaml
name: my_plugin
version: 0.1.0
type: playground
description: "My custom plugin"
stages: [step1, step2]
```

Minimal `capability.py`:
# 最小 `capability.py`：

```python
from deeptutor.core.capability_protocol import BaseCapability, CapabilityManifest
from deeptutor.core.context import UnifiedContext
from deeptutor.core.stream_bus import StreamBus

class MyPlugin(BaseCapability):
    manifest = CapabilityManifest(
        name="my_plugin",
        description="My custom plugin",
        stages=["step1", "step2"],
    )

    async def run(self, context: UnifiedContext, stream: StreamBus) -> None:
        async with stream.stage("step1", source=self.name):
            await stream.content("Working on step 1...", source=self.name)
        await stream.result({"response": "Done!"}, source=self.name)
```

## Dependency Layers / 依赖层级

```
requirements/cli.txt            — CLI full (LLM + RAG + providers + tools)
# CLI 完整版（LLM + RAG + providers + tools）
requirements/server.txt         — CLI + FastAPI/uvicorn (for Web/API)
# CLI + FastAPI/uvicorn（用于 Web/API）
requirements/math-animator.txt  — Manim addon (for `deeptutor animate`)
# Manim 插件（用于 `deeptutor animate`）
requirements/dev.txt            — Server + test/lint tools
# 服务器 + 测试/lint 工具
```
