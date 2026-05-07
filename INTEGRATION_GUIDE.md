# DeepTutor 前端集成指南

## 🎉 集成完成！

DeepTutor 已成功集成到前端系统中！

---

## 📁 新增文件

### 前端
- `web/app/deeptutor-chat/page.tsx` - DeepTutor 统一聊天页面
- `web/app/dashboard/page.tsx` - 添加了 DeepTutor 入口（已修改）

### 后端
- `deeptutor/` - 完整的 DeepTutor 模块
  - `agents/agent_loop.py` - Agent 核心循环
  - `channels/` - 多平台聊天通道
  - `config.py` - 配置管理
  - `cli/` - 命令行工具
- `run.py` - 统一聊天系统启动入口

### 文档
- `QUICKSTART.md` - 快速开始指南
- `DEVELOPMENT.md` - 开发指南
- `INTEGRATION_GUIDE.md` - 本文档

---

## 🚀 使用方式

### 方式 1: Web UI（推荐）

1. 启动前端（如已启动跳过）：
```bash
cd web
npm install
npm run dev
```

2. 访问 `http://localhost:3000`

3. 登录后，点击 dashboard 上的 **"DeepTutor Chat"** 卡片

### 方式 2: 独立启动

```bash
# 配置
cp .env.example .env
# 编辑 .env，填入 API 密钥

# 启动
python run.py
```

### 方式 3: 命令行

```bash
# 交互式聊天
python -m deeptutor chat

# 查看配置
python -m deeptutor config

# 启动通道网关
python -m deeptutor channels
```

---

## 🔧 配置说明

### 必需配置
```env
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
LLM_API_KEY=your-api-key-here
```

### 可选通道配置
```env
# Telegram
TELEGRAM_ENABLED=false
TELEGRAM_TOKEN=your-token

# Discord
DISCORD_ENABLED=false
DISCORD_TOKEN=your-token

# Slack
SLACK_ENABLED=false
SLACK_BOT_TOKEN=your-token
SLACK_APP_TOKEN=your-token

# Email
EMAIL_ENABLED=false
EMAIL_USERNAME=your@email.com
EMAIL_PASSWORD=your-password

# WebSocket
WEBSOCKET_ENABLED=true
WEBSOCKET_PORT=8765
```

---

## 📊 功能特性

### ✅ Agent 功能
- YOLO 模式（自动执行）
- 实时成本追踪
- 工作区快照与回滚
- 思考过程可视化
- 多模型并行推理

### ✅ 聊天通道
- 📱 Telegram
- 🎮 Discord
- 💬 WeChat
- 📌 Feishu
- 🟦 Slack
- 📧 Email
- 🔌 WebSocket

### ✅ MCP 协议
- MCP 客户端
- MCP 服务端
- MCP 管理器
- 工具适配器

### ✅ 部署方式
- 独立 Python 脚本
- Docker 容器化
- Docker Compose 编排

---

## 🧪 快速测试

### 1. 启动 Web UI
访问 `http://localhost:3000/dashboard` → 点击 "DeepTutor Chat"

### 2. 测试聊天
在聊天界面发送消息，查看 AI 回复

### 3. 尝试通道
在左侧面板启用通道，测试对应平台

---

## 📝 项目结构总览

```
DeepTutor/
├── deeptutor/              # 后端模块
│   ├── agents/            # Agent 逻辑
│   ├── channels/          # 聊天通道
│   ├── cli/               # 命令行工具
│   ├── config.py          # 配置管理
│   └── ...
├── web/                   # 前端模块
│   └── app/
│       ├── dashboard/     # 仪表盘（已更新）
│       └── deeptutor-chat/ # 新聊天页面
├── run.py                 # 统一启动入口
├── docker-compose.yml     # Docker 配置
├── pyproject.toml         # Python 包配置
└── docs/                  # 文档
    ├── QUICKSTART.md
    ├── DEVELOPMENT.md
    └── INTEGRATION_GUIDE.md
```

---

## 🎯 下一步

1. **配置 API 密钥** - 编辑 `.env` 填入真实的 API 密钥
2. **启动后端服务** - `python run.py` 或 `docker-compose up`
3. **测试通道** - 根据需要启用 Telegram/Discord 等
4. **自定义功能** - 查看 `DEVELOPMENT.md` 了解如何扩展

---

## ❓ 获取帮助

- 快速开始：`QUICKSTART.md`
- 开发指南：`DEVELOPMENT.md`
- 原项目文档：`README.md`
- GitHub Issues：https://github.com/17625398/opendeepbot/issues

---

## 📄 许可证

MIT License

---

**集成完成日期**：2026-05-08
**版本**：v0.1.0
