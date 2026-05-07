# DeepTutor 快速开始指南

## 📋 目录

- [前置要求](#前置要求)
- [快速安装](#快速安装)
- [配置说明](#配置说明)
- [本地使用](#本地使用)
- [多平台使用](#多平台使用)
- [高级功能](#高级功能)
- [常见问题](#常见问题)

## 🚀 前置要求

- Python 3.9+
- 支持的 LLM（本地或云端）
- 根据需要安装相应的依赖

## 💻 快速安装

### 1. 克隆项目

```bash
git clone https://github.com/17625398/opendeepbot.git
cd opendeepbot
```

### 2. 安装依赖

```bash
# 基础依赖
pip install -e .

# 或者使用 Conda
conda env create -f environment.yml
conda activate deeptutor
```

### 3. 配置环境

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的配置
```

## ⚙️ 配置说明

### 最小配置（使用 DeepSeek）

在 `.env` 文件中设置：

```env
LLM_PROVIDER=deepseek
LLM_API_KEY=sk-xxxxxxxxxxxxxxx
LLM_MODEL=deepseek-chat
```

### 使用本地 Ollama

```bash
# 1. 安装并启动 Ollama
# https://ollama.ai

# 2. 拉取模型
ollama pull llama3

# 3. 配置环境变量
OLLAMA_ENABLED=true
LLM_PROVIDER=ollama
LLM_MODEL=llama3
```

## 🎯 本地使用

### 启动 WebUI

```bash
# 方式 1：使用脚本
python scripts/start_webui.py

# 方式 2：进入 web 目录
cd web
npm install
npm run dev
```

访问 `http://localhost:3000`

### 使用命令行

```bash
# 聊天模式
deeptutor chat

# 执行任务
deeptutor task "分析这个代码库"
```

## 🌐 多平台使用

### 启动通道网关

```bash
python scripts/start_channels.py
```

### 配置 Telegram Bot

1. 在 `.env` 中设置：
   ```env
   TELEGRAM_ENABLED=true
   TELEGRAM_TOKEN=your-bot-token
   ```

2. 在 [@BotFather](https://t.me/BotFather) 创建 bot

3. 启动后在 Telegram 中与 bot 对话

### 配置 Discord Bot

1. 在 `.env` 中设置：
   ```env
   DISCORD_ENABLED=true
   DISCORD_TOKEN=your-bot-token
   ```

2. 在 [Discord Developer Portal](https://discord.com/developers/applications) 创建应用

3. 邀请 bot 到你的服务器

4. 使用 `!` 前缀发送消息

### 使用 WebSocket 网关

WebSocket 已默认启用，用于与 WebUI 通信：

```env
WEBSOCKET_ENABLED=true
WEBSOCKET_HOST=localhost
WEBSOCKET_PORT=8765
```

## 🔧 高级功能

### YOLO 模式

自动批准所有工具调用，无需人工干预：

```python
from deeptutor.integrations.nanobot.agent import AgentLoop

agent = AgentLoop(llm_client, yolo_mode=True)
result = await agent.run("自动完成这个任务")
```

### 成本跟踪

实时跟踪 LLM 调用成本：

```python
cost_summary = agent.get_cost_summary()
print(f"总消耗: ${cost_summary['total_cost_usd']:.6f}")
print(f"总 tokens: {cost_summary['total_tokens']}")
```

### 工作区快照和回滚

```python
# 创建快照
snapshot_id = agent._create_snapshot("before_action")

# 稍后回滚
agent._rollback_to_snapshot(snapshot_id)

# 或者回滚几步
agent._rollback_steps(3)
```

### 思考模式可视化

```python
# 设置显示模式
agent.set_thinking_style("chain")  # 或 "tree", "mindmap"

# 打印思考过程
agent.print_thinking()
```

### 多模型并行推理

```python
from deeptutor.integrations.nanobot.agent import AgentLoop

result = await agent.run_parallel_models(
    user_input="分析这个问题",
    llm_clients=[client1, client2, client3],
    aggregate_method="vote"  # "vote", "ensemble", "best"
)
```

## 📊 本地模型管理

### 列出可用模型

```bash
deeptutor model list
```

### 列出本地 Ollama 模型

```bash
deeptutor model ollama-list
```

### 切换模型

```bash
# 切换到 Ollama 的 llama3
deeptutor model ollama-switch llama3

# 切换到 SGLang
deeptutor model sglang-switch deepseek-v4-flash
```

### 查看当前配置

```bash
deeptutor model current
```

## 📝 常见问题

### 1. 如何添加新的 LLM 提供商？

编辑 `deeptutor/services/llm/__init__.py` 和相应的适配器文件。

### 2. 如何创建自定义工具？

参考 `deeptutor/integrations/nanobot/agent/tools/` 目录下的现有工具，继承 `BaseTool` 类。

### 3. 如何添加新的聊天通道？

参考 `deeptutor/channels/` 目录，继承 `BaseChannel` 类。

### 4. 如何启用 MCP？

在 `.env` 中设置：

```env
MCP_ENABLED=true
MCP_SERVERS={"servers":[{"name":"filesystem","command":"npx","args":["-y","@modelcontextprotocol/server-filesystem","/path/to/dir"]}]}
```

## 🤝 支持与反馈

- 提交 Issue：https://github.com/17625398/opendeepbot/issues
- 查看文档：https://github.com/17625398/opendeepbot/wiki

## 📄 许可证

本项目采用 MIT 许可证 - 查看 LICENSE 文件了解详情。