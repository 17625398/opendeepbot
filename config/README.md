# 配置目录

本目录包含 DeepTutor 系统的所有配置文件。配置文件按模块组织，使用 YAML 格式。

## 📁 配置文件

```
config/
├── main.yaml              # 主系统配置（所有模块设置）
├── agents.yaml            # 统一的智能体参数（temperature, max_tokens, model）
├── nanobot.yaml           # Nanobot 服务配置
├── weknora.yaml           # WeKnora 服务配置
├── interrogation_config.yaml  # 审讯系统配置
├── mirofish_config.json   # MiroFish 配置
├── validate_config.py     # 配置验证脚本
└── README.md              # 本文档
```

## 📋 文件说明

### agents.yaml ⭐ 单一事实来源

**统一的智能体参数配置** - 所有智能体 `temperature`、`max_tokens`、`num_ctx` 和 `model` 设置的单一事实来源：

- **用途**：跨所有模块的 LLM 参数集中配置
- **范围**：每个模块为其所有智能体共享一组参数
- **例外**：`narrator` 因 TTS 集成有独立设置

**主要部分：**
```yaml
# 智能体模块 - 核心 AI 智能体
guide:
  temperature: 0.5
  max_tokens: 16192

solve:
  temperature: 0.3
  max_tokens: 8192

research:
  temperature: 0.5
  max_tokens: 12000

question:
  temperature: 0.7
  max_tokens: 4096

ideagen:
  temperature: 0.7
  max_tokens: 4096

co_writer:
  temperature: 0.7
  max_tokens: 4096

draw:
  temperature: 0.5
  max_tokens: 4096

interrogation:
  temperature: 0.1
  max_tokens: 131072
  num_ctx: 131072

deep_analyze:
  temperature: 0.1
  max_tokens: 131072
  num_ctx: 131072

deep_audit:
  temperature: 0.3
  max_tokens: 8192

domain_analysis:
  temperature: 0.5
  max_tokens: 8192

public_opinion:
  temperature: 0.3
  max_tokens: 8192

chat:
  temperature: 0.7
  max_tokens: 4096

assistant:
  temperature: 0.5
  max_tokens: 8192

# 服务层 - src/services/ 中的服务
llm:
  temperature: 0.7
  max_tokens: 4096

llm_manager:
  temperature: 0.7
  max_tokens: 4096

config_manager:
  temperature: 0.7
  max_tokens: 4000

lightweight_agent:
  temperature: 0.7
  max_tokens: 4096

autofigure:
  temperature: 0.5
  max_tokens: 4096

teaching_planner:
  temperature: 0.7
  max_tokens: 4096

prompt_optimizer:
  temperature: 0.7
  max_tokens: 4096

memsearch:
  temperature: 0.7
  max_tokens: 4096

agent_manager:
  temperature: 0.7
  max_tokens: 4096

knowledge_integration:
  temperature: 0.3
  max_tokens: 4096

# API 层 - src/api/ 中的路由
ai_chat:
  temperature: 0.7
  max_tokens: 4096

agents_api:
  temperature: 0.7
  max_tokens: 2048

chatdev:
  temperature: 0.7
  max_tokens: 4096

system_api:
  temperature: 0.1
  max_tokens: 200

interrogation_api:
  temperature: 0.3
  max_tokens: 4096

# 知识层
knowledge:
  temperature: 0.1
  max_tokens: 4000

extract_numbered_items:
  temperature: 0.1
  max_tokens: 2000

ai_assistant:
  temperature: 0.7
  max_tokens: 2000

# Nanobot 层
nanobot_agent:
  temperature: 0.7
  max_tokens: 2048

nanobot_mcp:
  temperature: 0.7
  max_tokens: 2048

nanobot_deep_analyze:
  temperature: 0.3
  max_tokens: 4096

# 其他
narrator:
  temperature: 0.7
  max_tokens: 4000

dslighting:
  temperature: 0.5
  max_tokens: 65536
  num_ctx: 131072
  model: "glm-4.7-flash:q4_K_M"

self_improvement:
  temperature: 0.3
  max_tokens: 4096
```

**代码中使用：**
```python
from src.services.config import get_agent_params

# 获取模块参数
params = get_agent_params("guide")
temperature = params["temperature"]  # 0.5
max_tokens = params["max_tokens"]    # 16192
num_ctx = params.get("num_ctx")      # None 或特定值
model = params.get("model")          # None 或特定模型覆盖
```

> **重要**：不要在智能体/服务代码中硬编码 `temperature`、`max_tokens`、`num_ctx` 或 `model` 值。始终使用 `get_agent_params()` 从此配置加载。

---

### main.yaml

**主系统配置文件** - 包含所有模块共享的设置：

- **服务器配置**：后端和前端端口设置
- **系统设置**：系统范围的语言配置
- **路径配置**：所有模块的数据目录路径
- **工具配置**：通用工具设置（RAG、代码执行、网页搜索、查询项）
- **日志配置**：日志级别、文件输出、控制台输出、LightRAG 转发
- **内存配置**：EverMemOS 集成设置
- **问题模块**：问题生成设置（rag_query_count、智能体特定的非 LLM 参数）
- **研究模块**：规划、研究、报告、RAG、队列和预设配置
- **求解模块**：迭代限制、引用设置、智能体特定的非 LLM 参数
- **服务目录**：服务显示名称、描述和健康检查端点

**主要部分：**
```yaml
system:
  language: zh  # "zh" 或 "en"

paths:
  user_data_dir: ./data/user
  knowledge_bases_dir: ./data/knowledge_bases
  # ... 其他路径

tools:
  rag_tool:
    kb_base_dir: ./data/knowledge_bases
    default_kb: ai_textbook
    init_llm:
      num_ctx: 8192
  run_code:
    workspace: ./data/user/run_code_workspace
  web_search:
    enabled: true
    provider: jina

logging:
  level: DEBUG
  save_to_file: true
  console_output: true

memory:
  provider: evermemos
  enabled: true
  api_url: "http://localhost:8001/api/v1"

# 模块特定设置（非 LLM 参数）
question:
  rag_query_count: 3
  max_parallel_questions: 1

research:
  planning:
    decompose:
      mode: auto
  researching:
    max_iterations: 5
  presets:
    quick: { ... }
    medium: { ... }
    deep: { ... }

solve:
  max_solve_correction_iterations: 3
  enable_citations: true
```

---

### nanobot.yaml

**Nanobot 服务配置** - 机器人连接器和频道设置：

```yaml
agents:
  defaults:
    model: qwen3:30b

nanobot:
  enabled: true
  gatewayPort: 8080
  dataDir: data/nanobot

providers:
  ollama:
    apiBase: http://localhost:11434/v1
    model: huihui_ai/qwenlong-l1.5-abliterated:latest

temperature: 0.7
maxTokens: 2048
```

---

### weknora.yaml

**WeKnora 服务配置** - 知识库和检索设置：

```yaml
llm:
  default:
    model: "glm-4.7-flash:q4_K_M"
    temperature: 0.3
    max_tokens: 1000
  cot:
    model: "qwen3:30b"
    temperature: 0.7
    max_tokens: 2000

vector_store:
  embedding_model: "qwen3-embedding:8b"
  embedding_dim: 4096

retrieval:
  default_top_k: 5
  hybrid:
    enabled: true
```

---

### interrogation_config.yaml

**审讯系统配置** - 案件分析和法律匹配：

```yaml
interrogation:
  output_dir: ./data/user/interrogation
  
  agents:
    extract_agent:
      enabled: true
      max_retries: 3
    legal_match_agent:
      enabled: true
      max_retries: 2
      rag_top_k: 10
    # ... 其他智能体
  
  quality_weights:
    completeness: 0.3
    standardization: 0.25
    logic: 0.25
    legality: 0.2
```

---

### mirofish_config.json

**MiroFish 配置** - 多智能体模拟设置：

```json
{
  "enabled": true,
  "base_url": "http://localhost:5001",
  "api_key": "",
  "default_world_name": "default",
  "timeout_seconds": 1200
}
```

## 🔧 配置层次结构

配置文件遵循层次结构（优先级从高到低）：

1. **代码级覆盖**（直接传递的函数参数）
2. **agents.yaml** - LLM 参数（temperature、max_tokens、num_ctx、model）
3. **main.yaml** - 系统范围共享设置
4. **服务特定配置**（nanobot.yaml、weknora.yaml 等）
5. **环境变量**（`.env` 或 `DeepTutor.env`）
   - LLM API 密钥和端点
   - 模型名称（如果不在配置中则作为后备）

## 📝 配置加载

### 智能体参数（temperature、max_tokens）：

```python
from src.services.config import get_agent_params

# 获取任何模块的参数
params = get_agent_params("module_name")
temperature = params["temperature"]
max_tokens = params["max_tokens"]
num_ctx = params.get("num_ctx")  # 可选
model = params.get("model")      # 可选模型覆盖
```

### 主配置：

```python
from src.services.config import load_config_with_main

# 加载主配置
config = load_config_with_main("main.yaml")
paths = config.get("paths", {})
```

### 服务配置：

```python
from src.services.config import get_config_manager, ConfigType

# 获取统一配置管理器
manager = get_config_manager()
llm_config = manager.get_active_config(ConfigType.LLM)
```

## 🔑 环境变量

必需的环境变量（在 `.env` 或 `DeepTutor.env` 中）：

```bash
# LLM 配置（基本操作必需）
LLM_API_KEY=your_api_key
LLM_HOST=https://api.openai.com/v1
LLM_MODEL=gpt-4o

# 可选 - 服务特定
PERPLEXITY_API_KEY=your_key  # 用于网页搜索
TTS_API_KEY=your_key         # 用于文本转语音
```

## ⚙️ 配置最佳实践

1. **对 LLM 参数使用 agents.yaml**：所有 `temperature`、`max_tokens`、`num_ctx` 设置应在 `agents.yaml` 中
2. **永远不要硬编码 LLM 参数**：始终在代码中使用 `get_agent_params()`
3. **对系统设置使用 main.yaml**：路径、日志、工具、模块特定的非 LLM 设置
4. **对服务特定设置使用服务配置**：Nanobot、WeKnora 等
5. **环境变量用于机密**：切勿将 API 密钥提交到配置文件
6. **相对路径**：使用项目根目录的相对路径以提高可移植性
7. **常见场景的预设**：使用预设（例如 main.yaml 研究部分）应对不同用例

## 🔗 相关模块

- **配置服务**：`src/services/config/` - 配置加载工具
  - `loader.py` - `get_agent_params()`、`load_config_with_main()`
  - `unified_config.py` - `UnifiedConfigManager`、`ConfigType`
- **基础智能体**：`src/agents/base_agent.py` - 使用 `get_agent_params()` 进行 LLM 调用
- **LLM 配置**：`src/services/llm/config.py` - 与 agents.yaml 集成的 LLM 配置

## 🛠️ 修改配置

### 添加新模块配置：

1. 将 LLM 参数（temperature、max_tokens、num_ctx）添加到 `agents.yaml`
2. 将模块特定的非 LLM 设置添加到 `main.yaml`
3. 如有需要更新加载代码
4. 在本文档中记录新选项

### 更改默认值：

1. 编辑 `agents.yaml` 以修改 LLM 参数
2. 编辑 `main.yaml` 以修改其他设置
3. 测试更改
4. 如有需要更新文档

## ⚠️ 重要说明

1. **智能体参数集中化**：所有 LLM 参数（`temperature`、`max_tokens`、`num_ctx`、`model`）必须在 `agents.yaml` 中。不要在代码中硬编码这些值。

2. **模型配置优先级**：
   - 代码参数 > agents.yaml `model` 字段 > 环境变量 `LLM_MODEL` > 默认值

3. **路径一致性**：所有模块使用 `main.yaml` 中的路径以确保一致性。使用项目根目录的相对路径。

4. **语言设置**：系统语言在 `main.yaml` 中设置（`system.language`）并由所有模块共享。

5. **研究预设**：在 `main.yaml` 中使用预设（research.presets: quick/medium/deep/auto）应对不同研究深度要求。

6. **代码执行安全**：`main.yaml` 中的 `run_code` 工具具有受限的 `allowed_roots` 以确保安全。

7. **旁白独立性**：`agents.yaml` 中的 `narrator` 智能体具有独立设置，因为它与 TTS API 集成，该 API 有特定的字符限制（4000 个令牌）。

8. **网页搜索全局开关**：`main.yaml` 中的 `tools.web_search.enabled` 设置是影响所有模块的全局开关。

9. **内存配置**：内存服务（EverMemOS）可在 `main.yaml` 中配置，在不可用时优雅降级。

10. **配置验证**：使用 `get_agent_params()` 时始终提供后备默认值以优雅地处理缺失的配置。

## ✅ 配置验证

### 使用验证脚本

我们提供验证脚本以检查配置是否正确：

```bash
python config/validate_config.py
```

此脚本将：
1. 验证 `agents.yaml` 的格式
2. 检查所有必需的模块配置是否存在
3. 测试配置加载功能
4. 检查服务文件是否正确配置

### 验证输出示例

```
============================================================
配置验证工具
============================================================

============================================================
1. 验证 agents.yaml 文件
============================================================
  ✅ agents.yaml 格式正确，包含 38 个模块配置

  状态: ✅ 通过

============================================================
2. 测试配置读取功能
============================================================
  ✅ 模块 'guide': temperature=0.5, max_tokens=16192
  ✅ 模块 'solve': temperature=0.3, max_tokens=8192
  ...

  状态: ✅ 通过

============================================================
✅ 所有验证通过！配置系统工作正常。
============================================================
```

## 🔄 迁移指南

### 从硬编码参数迁移

如果你有带有硬编码参数的代码，如：

```python
# 旧方式（硬编码）
response = await complete(
    prompt=prompt,
    model="gpt-4o",
    temperature=0.7,
    max_tokens=4096,
)
```

迁移到配置驱动：

```python
# 新方式（配置驱动）
from src.services.config import get_agent_params

def _get_module_params() -> dict:
    """从 agents.yaml 获取模块的参数配置"""
    try:
        params = get_agent_params("module_name")
        return {
            "temperature": params.get("temperature", 0.7),
            "max_tokens": params.get("max_tokens", 4096),
            "model": params.get("model"),  # 可选
        }
    except Exception:
        return {"temperature": 0.7, "max_tokens": 4096, "model": None}

# 使用
config_params = _get_module_params()
response = await complete(
    prompt=prompt,
    model=config_params.get("model") or "gpt-4o",  # 后备到默认值
    temperature=config_params["temperature"],
    max_tokens=config_params["max_tokens"],
)
```

### 添加配置到 agents.yaml

1. 打开 `config/agents.yaml`
2. 添加你的模块配置：

```yaml
your_module_name:
  temperature: 0.7
  max_tokens: 4096
  # 可选：模型覆盖
  # model: "gpt-4o"
  # 可选：上下文窗口大小
  # num_ctx: 8192
```

3. 运行验证脚本确认：
   ```bash
   python config/validate_config.py
   ```

## 📊 配置参考

### 按模块类型的默认参数值

| 模块类型 | 默认 Temperature | 默认 Max Tokens | 典型用例 |
|----------|------------------|-----------------|----------|
| **分析** (interrogation, deep_analyze) | 0.1-0.3 | 131072 | 精确、确定性输出 |
| **创意** (ideagen, co_writer) | 0.7 | 4096 | 多样化、创意输出 |
| **平衡** (guide, research) | 0.5 | 12000 | 创意和精确的平衡 |
| **聊天** (chat, assistant) | 0.7 | 4096 | 对话式、自然响应 |
| **系统** (system_api) | 0.1 | 200 | 测试、最小输出 |

### 参数指南

- **temperature**：确定性任务使用较低值（0.1-0.3），创意任务使用较高值（0.7-0.9）
- **max_tokens**：根据预期输出长度调整
  - 短响应：512-1024
  - 中等响应：2048-4096
  - 长响应：8192+
  - 最大值：131072（用于大上下文模型）
- **num_ctx**：上下文窗口大小，仅特定模型需要（例如 Ollama）
- **model**：可选覆盖，后备到环境变量或默认值

## 🔍 故障排除

### 常见问题

1. **配置未加载**
   - 检查 `agents.yaml` 是否存在于 `config/` 目录
   - 验证 YAML 语法是否有效
   - 运行 `python config/validate_config.py`

2. **模块未找到**
   - 确保代码中的模块名称与 `agents.yaml` 中的配置匹配
   - 检查模块名称中的拼写错误

3. **始终使用默认值**
   - 验证 `get_agent_params()` 被正确调用
   - 检查异常处理是否捕获配置错误
   - 运行验证脚本测试配置加载

4. **更改未生效**
   - 重启应用程序（配置在启动时加载）
   - 验证你正在编辑正确的文件
   - 检查文件权限

### 调试模式

启用调试日志以查看配置加载详情：

```python
import logging
logging.getLogger("src.services.config").setLevel(logging.DEBUG)
```

## 📝 变更日志

### 2024-XX-XX - 配置统一化
- 将所有模型参数统一到 `agents.yaml`
- 将所有服务迁移到使用配置驱动参数
- 添加配置验证脚本
- 使用迁移指南更新文档
