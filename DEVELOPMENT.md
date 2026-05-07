# DeepTutor 开发指南

本文档为 DeepTutor 项目的开发者提供完整的开发指南。

## 📋 目录

- [项目架构](#项目架构)
- [开发环境设置](#开发环境设置)
- [代码规范](#代码规范)
- [测试指南](#测试指南)
- [如何贡献](#如何贡献)

---

## 🏗️ 项目架构

### 目录结构

```
DeepTutor/
├── deeptutor/                  # 主源码目录
│   ├── agents/                # Agent 相关代码
│   │   └── agent_loop.py      # 核心 Agent 循环
│   ├── channels/              # 聊天通道
│   │   ├── __init__.py
│   │   ├── base.py            # 通道基类
│   │   ├── telegram.py        # Telegram 通道
│   │   ├── discord.py         # Discord 通道
│   │   ├── wechat.py          # WeChat 通道
│   │   ├── feishu.py          # Feishu 通道
│   │   ├── slack.py           # Slack 通道
│   │   ├── email.py           # Email 通道
│   │   └── websocket.py       # WebSocket 通道
│   ├── cli/                   # CLI 工具
│   │   ├── __init__.py
│   │   └── main.py            # CLI 主程序
│   ├── llm/                   # LLM 提供商
│   │   └── providers.py       # LLM 提供商接口
│   ├── mcp/                   # MCP 协议
│   │   ├── __init__.py
│   │   ├── client.py          # MCP 客户端
│   │   ├── server.py          # MCP 服务端
│   │   ├── manager.py         # MCP 管理器
│   │   └── adapter.py         # MCP 工具适配器
│   ├── memory/                # 记忆系统
│   └── __main__.py            # 模块入口
├── examples/                  # 示例代码
│   └── full_example.py        # 完整功能示例
├── scripts/                   # 脚本文件
│   └── start_channels.py      # 通道启动脚本
├── tests/                     # 测试文件
├── web/                       # 前端代码（原项目）
├── docker-compose.yml         # Docker Compose 配置
├── Dockerfile                 # Docker 镜像配置
├── pyproject.toml             # Python 包配置
└── requirements.txt           # 依赖文件
```

### 核心模块说明

#### 1. Agent 模块 (`deeptutor/agents/`)

`AgentLoop` 是核心执行引擎，负责：

- **推理循环**：思考 → 行动 → 观察 → 响应
- **工具调用**：执行注册的工具
- **成本跟踪**：实时统计 token 使用和费用
- **YOLO 模式**：自动批准工具调用

关键类：
```python
from deeptutor.agents.agent_loop import AgentLoop

agent = AgentLoop(
    llm_client=llm_client,
    max_iterations=10,
    yolo_mode=False,
    track_cost=True
)
```

#### 2. 聊天通道 (`deeptutor/channels/`)

所有通道都继承自 `BaseChannel` 基类：

```python
from deeptutor.channels.base import BaseChannel

class MyChannel(BaseChannel):
    async def initialize(self) -> bool:
        """初始化通道"""
        pass
    
    async def send_message(self, user_id: str, message: str) -> bool:
        """发送消息"""
        pass
    
    async def send_typing(self, user_id: str):
        """发送输入状态"""
        pass
    
    async def start(self):
        """启动通道"""
        pass
    
    async def shutdown(self):
        """关闭通道"""
        pass
```

`ChannelManager` 负责统一管理所有通道：

```python
from deeptutor.channels import ChannelManager, TelegramChannel, DiscordChannel

manager = ChannelManager(config)
manager.register_channel(TelegramChannel(config_telegram))
manager.register_channel(DiscordChannel(config_discord))
await manager.start()
```

#### 3. MCP 模块 (`deeptutor/mcp/`)

MCP (Model Context Protocol) 提供了工具注册和调用接口：

```python
from deeptutor.mcp import MCPManager

mcp = MCPManager(config)
await mcp.start()
```

---

## 🔧 开发环境设置

### 1. 克隆代码库

```bash
git clone https://github.com/17625398/opendeepbot.git
cd opendeepbot
```

### 2. 创建虚拟环境

```bash
# 使用 Conda
conda create -n deeptutor python=3.11
conda activate deeptutor

# 或使用 venv
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

### 3. 安装依赖

```bash
# 安装核心依赖
pip install -e .

# 安装所有可选依赖
pip install -e ".[all]"

# 或分别安装需要的通道
pip install -e ".[telegram,discord,slack]"
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入您的 API 密钥
```

### 5. 验证安装

```bash
# 运行 CLI
python -m deeptutor --help

# 或运行测试
python -m pytest tests/
```

---

## 📝 代码规范

### 代码风格

我们使用以下工具保证代码质量：

| 工具 | 用途 |
|-----|-----|
| `black` | 代码格式化 |
| `isort` | 导入排序 |
| `flake8` | 代码检查 |
| `mypy` | 类型检查 |

运行代码检查：

```bash
# 格式化代码
black deeptutor/ examples/ scripts/
isort deeptutor/ examples/ scripts/

# 代码检查
flake8 deeptutor/
mypy deeptutor/
```

### 注释规范

所有公共 API 都应该有文档字符串：

```python
def send_message(self, user_id: str, message: str, **kwargs) -> bool:
    """发送消息给指定用户
    
    Args:
        user_id: 用户 ID
        message: 要发送的消息内容
        **kwargs: 其他可选参数
        
    Returns:
        是否发送成功
    """
    pass
```

---

## 🧪 测试指南

### 运行测试

```bash
# 安装测试依赖
pip install -e ".[dev]"

# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试文件
python -m pytest tests/test_channels.py

# 查看覆盖率
python -m pytest tests/ --cov=deeptutor --cov-report=html
```

### 编写测试

测试文件应该放在 `tests/` 目录下，以 `test_` 开头：

```python
import pytest
from deeptutor.channels import ChannelManager

class TestChannelManager:
    def test_init(self):
        """测试初始化"""
        config = {}
        manager = ChannelManager(config)
        assert manager is not None
    
    @pytest.mark.asyncio
    async def test_register_channel(self):
        """测试注册通道"""
        manager = ChannelManager({})
        # 测试代码...
```

---

## 🤝 如何贡献

### 1. Fork 并克隆

```bash
# 在 GitHub 上 Fork 项目
# 克隆您的 Fork
git clone https://github.com/你的用户名/opendeepbot.git
cd opendeepbot
```

### 2. 创建分支

```bash
git checkout -b feature/你的功能名称
```

### 3. 提交更改

```bash
git add .
git commit -m "feat: 添加你的功能"
```

### 4. 推送并创建 PR

```bash
git push origin feature/你的功能名称
# 在 GitHub 上创建 Pull Request
```

### 提交信息格式

我们使用约定式提交规范：

```
<type>(<scope>): <subject>

<type> 可以是：
- feat: 新功能
- fix: 修复
- docs: 文档
- style: 格式化
- refactor: 重构
- test: 测试
- chore: 构建/工具

示例：
- feat(channels): 添加 Slack 通道
- fix(agent): 修复 YOLO 模式中的空指针
- docs: 更新 README
```

---

## 🔍 调试技巧

### 启用详细日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 使用调试器

```python
import pdb

# 在需要的地方添加
pdb.set_trace()
```

---

## 📚 参考资源

- [nanobot 文档](https://github.com/HKUDS/nanobot)
- [MCP 协议规范](https://modelcontextprotocol.io)
- [DeepTutor 原项目](https://github.com/HKUDS/DeepTutor)

---

## 🆘 获取帮助

如果遇到问题：

1. 查看 [README.md](README.md)
2. 检查 [GitHub Issues](https://github.com/17625398/opendeepbot/issues)
3. 创建新的 Issue 描述问题

祝您开发愉快！🎉
