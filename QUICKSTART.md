# DeepTutor 快速开始指南

## 🚀 3分钟快速上手

### 1. 复制配置文件

```bash
cp .env.example .env
```

### 2. 配置您的 API Key

编辑 `.env` 文件，填入您的 LLM API Key：

```env
# LLM 配置
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
LLM_API_KEY=your-api-key-here  # 换成您的 API Key
```

### 3. 启用您想使用的通道

```env
# 选择您要启用的通道（设置为 true）
TELEGRAM_ENABLED=false
DISCORD_ENABLED=false
WEBSOCKET_ENABLED=true  # WebSocket 默认启用
```

### 4. 启动 DeepTutor

```bash
python run.py
```

---

## 📱 通道配置详解

### Telegram

```env
TELEGRAM_ENABLED=true
TELEGRAM_TOKEN=your-telegram-bot-token
```

获取 Token: [@BotFather](https://t.me/BotFather)

### Discord

```env
DISCORD_ENABLED=true
DISCORD_TOKEN=your-discord-bot-token
DISCORD_PREFIX=!
```

### WebSocket（推荐用于快速测试）

```env
WEBSOCKET_ENABLED=true
WEBSOCKET_HOST=localhost
WEBSOCKET_PORT=8765
```

连接后可以通过 WebSocket 发送消息测试。

### Slack

```env
SLACK_ENABLED=true
SLACK_BOT_TOKEN=xoxb-xxx
SLACK_APP_TOKEN=xapp-xxx
```

---

## 🐳 Docker 部署

### 使用 Compose 一键启动

```bash
docker-compose up -d
```

### 查看日志

```bash
docker-compose logs -f deeptutor
```

### 停止服务

```bash
docker-compose down
```

---

## 💻 CLI 命令行使用

### 交互式聊天

```bash
python -m deeptutor chat
```

### 配置检查

```bash
python -m deeptutor config
```

### 启动通道

```bash
python -m deeptutor channels
```

---

## 📚 更多资料

- 完整文档: [DEVELOPMENT.md](./DEVELOPMENT.md)
- 原项目文档: [README.md](./README.md)
- 配置示例: [.env.example](./.env.example)

---

## 🔧 故障排查

### 常见问题

**Q: 配置验证失败？**

A: 确保 `LLM_API_KEY` 已正确配置。

**Q: 通道连接不上？**

A: 检查对应平台的 Token 是否正确，确认端口没有被占用。

**Q: 如何只启用一个通道测试？**

A: 在 `.env` 中将其他通道设为 `false`，只保留一个通道为 `true`。

### 获取帮助

- 提交 Issue: [GitHub Issues](https://github.com/17625398/opendeepbot/issues)
