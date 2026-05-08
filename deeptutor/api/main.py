from contextlib import asynccontextmanager
from datetime import datetime
import importlib
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from deeptutor.logging import get_logger
from deeptutor.services.path_service import get_path_service

# Note: Don't set service_prefix here - start_web.py already adds [Backend] prefix
logger = get_logger("API")


class _SuppressWsNoise(logging.Filter):
    """Suppress noisy uvicorn logs for WebSocket connection churn."""

    _SUPPRESSED = ("connection open", "connection closed")

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        return not any(f in msg for f in self._SUPPRESSED)


logging.getLogger("uvicorn.error").addFilter(_SuppressWsNoise())

CONFIG_DRIFT_ERROR_TEMPLATE = (
    "Configuration Drift Detected: Capability tool references {drift} are not "
    "registered in the runtime tool registry. Register the missing tools or "
    "remove the stale tool names from the capability manifests."
)


class SafeOutputStaticFiles(StaticFiles):
    """Static file mount that only exposes explicitly whitelisted artifacts."""

    def __init__(self, *args, path_service, **kwargs):
        super().__init__(*args, **kwargs)
        self._path_service = path_service

    async def get_response(self, path: str, scope):
        if not self._path_service.is_public_output_path(path):
            raise HTTPException(status_code=404, detail="Output not found")
        return await super().get_response(path, scope)


def validate_tool_consistency():
    """
    Validate that capability manifests only reference tools that are actually
    registered in the runtime ``ToolRegistry``.
    """
    try:
        from deeptutor.runtime.registry.capability_registry import get_capability_registry
        from deeptutor.runtime.registry.tool_registry import get_tool_registry

        capability_registry = get_capability_registry()
        tool_registry = get_tool_registry()
        available_tools = set(tool_registry.list_tools())

        referenced_tools = set()
        for manifest in capability_registry.get_manifests():
            referenced_tools.update(manifest.get("tools_used", []) or [])

        drift = referenced_tools - available_tools
        if drift:
            raise RuntimeError(CONFIG_DRIFT_ERROR_TEMPLATE.format(drift=drift))
    except RuntimeError:
        logger.exception("Configuration validation failed")
        raise
    except Exception:
        logger.exception("Failed to load configuration for validation")
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management
    Gracefully handle startup and shutdown events, avoid CancelledError
    """
    # Execute on startup
    logger.info("Application startup")

    # Validate configuration consistency
    validate_tool_consistency()

    # Initialize LLM client early so OPENAI_* env vars are available before
    # any downstream provider integrations start.
    try:
        from deeptutor.services.llm import get_llm_client

        llm_client = get_llm_client()
        logger.info(f"LLM client initialized: model={llm_client.config.model}")
    except Exception as e:
        logger.warning(f"Failed to initialize LLM client at startup: {e}")

    try:
        from deeptutor.events.event_bus import get_event_bus

        event_bus = get_event_bus()
        await event_bus.start()
        logger.info("EventBus started")
    except Exception as e:
        logger.warning(f"Failed to start EventBus: {e}")

    try:
        from deeptutor.services.tutorbot import get_tutorbot_manager
        await get_tutorbot_manager().auto_start_bots()
    except Exception as e:
        logger.warning(f"Failed to auto-start TutorBots: {e}")

    yield

    # Execute on shutdown
    logger.info("Application shutdown")

    # Stop TutorBots
    try:
        from deeptutor.services.tutorbot import get_tutorbot_manager
        await get_tutorbot_manager().stop_all()
        logger.info("TutorBots stopped")
    except Exception as e:
        logger.warning(f"Failed to stop TutorBots: {e}")

    # Stop EventBus
    try:
        from deeptutor.events.event_bus import get_event_bus

        event_bus = get_event_bus()
        await event_bus.stop()
        logger.info("EventBus stopped")
    except Exception as e:
        logger.warning(f"Failed to stop EventBus: {e}")

    # Close LLM manager resources
    try:
        from deeptutor.services.llm_manager import llm_manager

        await llm_manager.close()
        logger.info("LLMManager resources closed")
    except Exception as e:
        logger.warning(f"Failed to close LLMManager resources: {e}")


app = FastAPI(
    title="DeepTutor API",
    version="1.3.6",
    lifespan=lifespan,
    # Disable automatic trailing slash redirects to prevent protocol downgrade issues
    # when deployed behind HTTPS reverse proxies (e.g., nginx).
    # Without this, FastAPI's 307 redirects may change HTTPS to HTTP.
    # See: https://github.com/HKUDS/DeepTutor/issues/112
    redirect_slashes=False,
)

# Log only non-200 requests (uvicorn access_log is disabled in run_server.py)
_access_logger = logging.getLogger("uvicorn.access")


@app.middleware("http")
async def selective_access_log(request, call_next):
    response = await call_next(request)
    if response.status_code != 200:
        _access_logger.info(
            '%s - "%s %s" %d',
            request.client.host if request.client else "-",
            request.method,
            request.url.path,
            response.status_code,
        )
    return response


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount a filtered view over user outputs.
# Only whitelisted artifact paths are readable through the static handler.
path_service = get_path_service()
user_dir = path_service.get_public_outputs_root()

# Initialize user directories on startup
try:
    from deeptutor.services.setup import init_user_directories

    init_user_directories()
except Exception:
    # Fallback: just create the main directory if it doesn't exist
    if not user_dir.exists():
        user_dir.mkdir(parents=True)

app.mount(
    "/api/outputs",
    SafeOutputStaticFiles(directory=str(user_dir), path_service=path_service),
    name="outputs",
)

# Hermes WebUI 反向代理集成
try:
    from deeptutor.api.webui_integration import (
        register_webui_routes,
        is_webui_available,
        get_webui_url,
    )
    
    # 注册 WebUI 路由
    register_webui_routes(app, prefix="/hermes/webui")
    
    logger.info(f"Hermes WebUI integration enabled: {get_webui_url()}")
except ImportError:
    logger.warning("Hermes WebUI integration not available")
except Exception as e:
    logger.error(f"Failed to integrate Hermes WebUI: {e}")

# Import routers only after runtime settings are initialized.
# Some router modules load YAML settings at import time.
from deeptutor.api.routers import (
    agent_config,
    attachments,
    auth,
    chat,
    co_writer,
    code_indexer,
    dashboard,
    deerflow,
    dingtalk,
    followup,
    guide,
    hiclaw,
    interrogation,
    knowledge,
    legal_kg,
    legal_prediction,
    legal_qa,
    legal_sentencing,
    mcp,
    memory,
    mindspider,
    mirofish,
    nanobot,
    notebook,
    openkb,
    pdf,
    plugins_api,
    question,
    question_notebook,
    scheduler,
    seafile,
    self_improvement,
    sessions,
    settings,
    solve,
    spaces,
    system,
    trae_agent,
    tutorbot,
    unified_ws,
    vision_solver,
    web_access,
    weknora,
)

# Workspaces router from routes (not routers)
from deeptutor.api.routes import workspaces

# Book router (optional - may fail on import if dependencies are missing)
try:
    from deeptutor.api.routers import book
    app.include_router(book.router, prefix="/api/v1/book", tags=["book"])
except ImportError as e:
    logger.warning(f"Book router not available: {e}")

# Skills router (optional - may fail on import if dependencies are missing)
try:
    from deeptutor.api.routers import skills
    app.include_router(skills.router, prefix="/api/v1/skills", tags=["skills"])
except ImportError as e:
    logger.warning(f"Skills router not available: {e}")

# Skill Catalog router (技能目录管理)
try:
    from deeptutor.api.routers import skill_catalog
    app.include_router(skill_catalog.router, prefix="/api/v1/skill-catalog", tags=["skill-catalog"])
except ImportError as e:
    logger.warning(f"Skill catalog router not available: {e}")

# Include routers
app.include_router(solve.router, prefix="/api/v1", tags=["solve"])
app.include_router(attachments.router, prefix="/api/attachments", tags=["attachments"])
app.include_router(spaces.router, prefix="/api/v1", tags=["spaces"])
app.include_router(workspaces.router, prefix="/api/v1", tags=["workspaces"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(question.router, prefix="/api/v1/question", tags=["question"])
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["knowledge"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(co_writer.router, prefix="/api/v1/co_writer", tags=["co_writer"])
app.include_router(notebook.router, prefix="/api/v1/notebook", tags=["notebook"])
app.include_router(guide.router, prefix="/api/v1/guide", tags=["guide"])
app.include_router(memory.router, prefix="/api/v1/memory", tags=["memory"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
app.include_router(question_notebook.router, prefix="/api/v1/question-notebook", tags=["question-notebook"])
app.include_router(settings.router, prefix="/api/v1/settings", tags=["settings"])
app.include_router(self_improvement.router, prefix="/api/v1/self-improvement", tags=["self-improvement"])
app.include_router(system.router, prefix="/api/v1/system", tags=["system"])
app.include_router(plugins_api.router, prefix="/api/v1/plugins", tags=["plugins"])
app.include_router(agent_config.router, prefix="/api/v1/agent-config", tags=["agent-config"])
app.include_router(vision_solver.router, prefix="/api/v1", tags=["vision-solver"])
app.include_router(tutorbot.router, prefix="/api/v1/tutorbot", tags=["tutorbot"])

# Web Access router (网页搜索和浏览器自动化)
app.include_router(web_access.router, prefix="/api/v1", tags=["web-access"])

# PDF router (PDF 文件处理和转换)
app.include_router(pdf.router, prefix="/api/v1", tags=["pdf"])

# Deerflow router (多智能体研究和工作流)
app.include_router(deerflow.router, prefix="/api/v1", tags=["deerflow"])

# Trae Agent router (Trae Agent 任务管理)
app.include_router(trae_agent.router, prefix="/api/v1", tags=["trae-agent"])

# Scheduler router (定时任务调度)
app.include_router(scheduler.router, prefix="/api/v1", tags=["scheduler"])

# Seafile router (文件存储集成)
app.include_router(seafile.router, prefix="/api/v1", tags=["seafile"])

# DingTalk router (钉钉集成)
app.include_router(dingtalk.router, prefix="/api/v1", tags=["dingtalk"])

# MiroFish router (群体智能预测)
app.include_router(mirofish.router, prefix="/api/v1", tags=["mirofish"])

# MCP router (Model Context Protocol)
app.include_router(mcp.router, prefix="/api/v1", tags=["mcp"])

# Nanobot router (Nanobot 集成)
app.include_router(nanobot.router, prefix="/api/v1", tags=["nanobot"])

# WeKnora router (WeKnora 文档处理)
app.include_router(weknora.router, prefix="/api/v1", tags=["weknora"])

# HiClaw router (HiClaw 管理器-工作器)
app.include_router(hiclaw.router, prefix="/api/v1", tags=["hiclaw"])

# Hermes Skills router (可选 - Hermes Agent Skills Integration)
try:
    from deeptutor.api.routers import hermes_skills
    app.include_router(hermes_skills.router, prefix="/api/v1/hermes/skills", tags=["hermes-skills"])
except ImportError as e:
    logger.warning(f"Hermes skills router not available: {e}")

# Hermes MCP router (optional - Hermes Agent MCP Integration)
try:
    from deeptutor.api.routers import hermes_mcp
    app.include_router(hermes_mcp.router, prefix="/api/v1/hermes/mcp", tags=["hermes-mcp"])
except ImportError as e:
    logger.warning(f"Hermes MCP router not available: {e}")

# Hermes Memory router (optional - Hermes Agent Memory Integration)
try:
    from deeptutor.api.routers import hermes_memory
    app.include_router(hermes_memory.router, prefix="/api/v1/hermes/memory", tags=["hermes-memory"])
except ImportError as e:
    logger.warning(f"Hermes Memory router not available: {e}")

# Hermes Gateway router (optional - Hermes Agent Gateway Integration)
try:
    from deeptutor.api.routers import hermes_gateway
    app.include_router(hermes_gateway.router, prefix="/api/v1/hermes/gateway", tags=["hermes-gateway"])
except ImportError as e:
    logger.warning(f"Hermes Gateway router not available: {e}")

# Hermes Scheduler router (optional - Hermes Agent Scheduler Integration)
try:
    from deeptutor.api.routers import hermes_scheduler
    app.include_router(hermes_scheduler.router, prefix="/api/v1/hermes/scheduler", tags=["hermes-scheduler"])
except ImportError as e:
    logger.warning(f"Hermes Scheduler router not available: {e}")

# Hermes User Modeling router (optional - Hermes Agent User Modeling Integration)
try:
    from deeptutor.api.routers import hermes_users
    app.include_router(hermes_users.router, prefix="/api/v1/hermes/users", tags=["hermes-users"])
except ImportError as e:
    logger.warning(f"Hermes User Modeling router not available: {e}")

# Hermes Migration router (optional - Hermes Agent Migration Tool)
try:
    from deeptutor.api.routers import hermes_migration
    app.include_router(hermes_migration.router, prefix="/api/v1/hermes/migration", tags=["hermes-migration"])
except ImportError as e:
    logger.warning(f"Hermes Migration router not available: {e}")

# Hermes Config router (optional - Hermes Agent Configuration Management)
try:
    from deeptutor.api.routers import hermes_config
    app.include_router(hermes_config.router, prefix="/api/v1/hermes/config", tags=["hermes-config"])
except ImportError as e:
    logger.warning(f"Hermes Config router not available: {e}")

# Hermes Analytics router (optional - Hermes Agent Analytics & Statistics)
try:
    from deeptutor.api.routers import hermes_analytics
    app.include_router(hermes_analytics.router, prefix="/api/v1/hermes/analytics", tags=["hermes-analytics"])
except ImportError as e:
    logger.warning(f"Hermes Analytics router not available: {e}")

# Hermes Logs router (optional - Hermes Agent Log Viewer)
try:
    from deeptutor.api.routers import hermes_logs
    app.include_router(hermes_logs.router, prefix="/api/v1/hermes/logs", tags=["hermes-logs"])
except ImportError as e:
    logger.warning(f"Hermes Logs router not available: {e}")

# Hermes Cron router (optional - Hermes Agent Scheduled Tasks)
try:
    from deeptutor.api.routers import hermes_cron
    app.include_router(hermes_cron.router, prefix="/api/v1/hermes/cron", tags=["hermes-cron"])
except ImportError as e:
    logger.warning(f"Hermes Cron router not available: {e}")

# Hermes Channels router (optional - Hermes Agent Platform Channels)
try:
    from deeptutor.api.routers import hermes_channels
    app.include_router(hermes_channels.router, prefix="/api/v1/hermes/channels", tags=["hermes-channels"])
except ImportError as e:
    logger.warning(f"Hermes Channels router not available: {e}")

# Hermes Profiles router (optional - Hermes Agent Multi-Profile Management)
try:
    from deeptutor.api.routers import hermes_profiles
    app.include_router(hermes_profiles.router, prefix="/api/v1/hermes/profiles", tags=["hermes-profiles"])
except ImportError as e:
    logger.warning(f"Hermes Profiles router not available: {e}")

# Hermes Knowledge router (optional - Hermes Agent Knowledge Management)
try:
    from deeptutor.api.routers import hermes_knowledge
    app.include_router(hermes_knowledge.router, prefix="/api/v1/hermes/knowledge", tags=["hermes-knowledge"])
except ImportError as e:
    logger.warning(f"Hermes Knowledge router not available: {e}")

# Hermes Sessions router (Session Compression, Tags, Search)
try:
    from deeptutor.api.routers import hermes_sessions
    app.include_router(hermes_sessions.router, prefix="/api/v1/hermes/sessions", tags=["hermes-sessions"])
except ImportError as e:
    logger.warning(f"Hermes Sessions router not available: {e}")

# Hermes Env router (Environment & Credential Management)
try:
    from deeptutor.api.routers import hermes_env
    app.include_router(hermes_env.router, prefix="/api/v1/hermes/env", tags=["hermes-env"])
except ImportError as e:
    logger.warning(f"Hermes Env router not available: {e}")

# Hermes Health router (Health Check & Diagnostics)
try:
    from deeptutor.api.routers import hermes_health
    app.include_router(hermes_health.router, prefix="/api/v1/hermes/health", tags=["hermes-health"])
except ImportError as e:
    logger.warning(f"Hermes Health router not available: {e}")

# Hermes Themes router (UI Themes & Customization)
try:
    from deeptutor.api.routers import hermes_themes
    app.include_router(hermes_themes.router, prefix="/api/v1/hermes/themes", tags=["hermes-themes"])
except ImportError as e:
    logger.warning(f"Hermes Themes router not available: {e}")

# Browser Context router (浏览器上下文桥接)
try:
    from deeptutor.api.routers import browser_context as browser_context_router
    app.include_router(browser_context_router.router, prefix="/api/v1/browser-context", tags=["browser-context"])
except ImportError as e:
    logger.warning(f"Browser Context router not available: {e}")

# Unified WebSocket endpoint
app.include_router(unified_ws.router, prefix="/api/v1", tags=["unified-ws"])

# Session export and search router (会话导出和搜索)
try:
    from deeptutor.api.routers import session_export
    app.include_router(session_export.router, prefix="", tags=["session-export"])
except ImportError as e:
    logger.warning(f"Session export router not available: {e}")

# Follow-up suggestions endpoint (追问建议)
app.include_router(followup.router, prefix="/api/v1", tags=["followup"])

# Auth router (认证)
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])

# OpenKB router (OpenKB 知识库集成)
app.include_router(openkb.router, prefix="/api/v1", tags=["openkb"])

# MindSpider router (舆情监测系统)
app.include_router(mindspider.router, prefix="/api/v1/mindspider", tags=["mindspider"])

# Legal routers (法律相关功能)
app.include_router(legal_qa.router, prefix="/api/v1", tags=["legal-qa"])
app.include_router(legal_kg.router, prefix="/api/v1", tags=["legal-kg"])
app.include_router(legal_prediction.router, prefix="/api/v1", tags=["legal-prediction"])
app.include_router(legal_sentencing.router, prefix="/api/v1", tags=["legal-sentencing"])

# Interrogation router (审讯/笔录分析系统)
app.include_router(interrogation.router, prefix="/api/v1", tags=["interrogation"])

# Code Indexer router (代码索引和检索)
app.include_router(code_indexer.router, prefix="/api/v1", tags=["code-indexer"])

# Graphify router (Graphify 知识图谱集成)
try:
    from deeptutor.api.routers import graphify as graphify_router
    app.include_router(graphify_router.router, prefix="/api/v1", tags=["graphify"])
except ImportError:
    logger.warning("Graphify router not available")

# RAGFlow router (RAGFlow 深度集成)
try:
    from deeptutor.api.routers import ragflow as ragflow_router
    app.include_router(ragflow_router.router, prefix="/api/v1", tags=["ragflow"])
except ImportError:
    logger.warning("RAGFlow router not available")

# LlamaIndex router (LlamaIndex 集成)
try:
    from deeptutor.api.routers import llamaindex_api_v2 as llamaindex_router
    app.include_router(llamaindex_router.router, prefix="/api/v1/llamaindex", tags=["llamaindex"])
except ImportError as e:
    logger.warning(f"LlamaIndex router not available: {e}")

# Evidence Analysis router (证据分析)
try:
    from deeptutor.api.routers import evidence_api as evidence_router
    app.include_router(evidence_router.router, prefix="/api/v1/evidence", tags=["evidence"])
except ImportError as e:
    logger.warning(f"Evidence Analysis router not available: {e}")

# Forensic Analysis router (案件笔录卷宗和电子证据取证分析)
try:
    from deeptutor.api.routers import forensic_analysis as forensic_analysis_router
    app.include_router(forensic_analysis_router.router, prefix="/api/v1", tags=["forensic-analysis"])
except ImportError as e:
    logger.warning(f"Forensic Analysis router not available: {e}")


def _include_optional_legacy_router(
    module_path: str,
    *,
    prefix: str | None = None,
    tags: list[str] | None = None,
    router_attr: str = "router",
):
    """
    Migrate legacy routers from ``deeptutor.api`` into the new ``deeptutor.api`` entrypoint.

    The new app remains authoritative. Legacy routers are mounted only when the
    corresponding functionality does not already exist in ``deeptutor.api``.
    Import failures are logged and skipped so the new entrypoint keeps working
    even if a legacy module has optional dependencies.
    """
    try:
        module = importlib.import_module(module_path)
        router = getattr(module, router_attr, None)
        if router is None:
            logger.warning(
                f"Skip legacy router without '{router_attr}': {module_path}"
            )

            return

        include_kwargs = {"tags": tags or []}
        if prefix is not None:
            include_kwargs["prefix"] = prefix
        app.include_router(router, **include_kwargs)
        logger.info(f"Mounted legacy router: {module_path}")
    except Exception as exc:
        logger.warning(f"Failed to mount legacy router {module_path}: {exc}")


LEGACY_ROUTER_SPECS = [
    # Core compatibility for features still implemented under deeptutor.api
    {"module_path": "deeptutor.api.routers.unified_chat", "prefix": "/api/v1", "tags": ["unified-chat"]},
    {"module_path": "deeptutor.api.routers.config", "prefix": "/api/v1/config", "tags": ["config"]},
    {"module_path": "deeptutor.api.routers.config", "prefix": "/api/v1", "tags": ["config"]},
    {"module_path": "deeptutor.api.routers.config_files", "prefix": "/api/v1/config-files", "tags": ["config-files"]},
    {"module_path": "deeptutor.api.routers.models", "prefix": "/api/v1/models", "tags": ["models"]},
    {"module_path": "deeptutor.api.routers.seafile", "prefix": "/api/v1", "tags": ["seafile"]},
    {"module_path": "deeptutor.api.routers.extensions", "prefix": "/api/v1", "tags": ["extensions"]},
    {"module_path": "deeptutor.api.routers.draw", "prefix": "/api/v1", "tags": ["draw"]},
    {"module_path": "deeptutor.api.routers.browser", "prefix": "/api/v1", "tags": ["browser"]},
    {"module_path": "deeptutor.api.routers.skills_new", "prefix": "/api/v1/skills-new", "tags": ["skills-new"]},
    {"module_path": "deeptutor.api.routers.visualization", "prefix": "/api/v1", "tags": ["visualization"]},
    {"module_path": "deeptutor.api.routers.multimodal", "prefix": "/api/v1", "tags": ["multimodal"]},
    {"module_path": "deeptutor.api.routers.deepvisual", "prefix": "/api/v1", "tags": ["deepvisual"]},
    {"module_path": "deeptutor.api.routers.deeptools", "prefix": "/api/v1", "tags": ["deeptools"]},
    {"module_path": "deeptutor.api.routers.deepdata", "prefix": "/api/v1", "tags": ["deepdata"]},
    {"module_path": "deeptutor.api.routers.deepagent", "prefix": "/api/v1", "tags": ["deepagent"]},
    {"module_path": "deeptutor.api.routers.deepanalyze", "prefix": "/api/v1", "tags": ["deepanalyze"]},
    {"module_path": "deeptutor.api.routers.mermaid", "prefix": "/api/v1", "tags": ["mermaid"]},
    {"module_path": "deeptutor.api.routers.graphmd", "prefix": "/api/v1", "tags": ["graphmd"]},
    {"module_path": "deeptutor.api.routers.image_gen", "prefix": "/api/v1/image-gen", "tags": ["image-gen"]},
    {"module_path": "deeptutor.api.routers.tts", "prefix": "/api/v1/tts", "tags": ["tts"]},
    {"module_path": "deeptutor.api.routers.personality", "prefix": "/api/v1/personality", "tags": ["personality"]},
    {"module_path": "deeptutor.api.routers.openrag", "prefix": "/api/v1", "tags": ["openrag"]},
    {"module_path": "deeptutor.api.routers.page_agent", "prefix": "/api/v1", "tags": ["page-agent"]},
    {"module_path": "deeptutor.api.routers.agent_browser", "prefix": "/api/v1", "tags": ["agent-browser"]},
    {"module_path": "deeptutor.api.routers.workflow_executor", "prefix": "/api/v1", "tags": ["workflow-executor"]},
    {"module_path": "deeptutor.api.routers.security", "prefix": "/api/v1/security", "tags": ["security"]},
    {"module_path": "deeptutor.api.routers.security", "prefix": "/api/security", "tags": ["security"]},
    {"module_path": "deeptutor.api.routers.prompt_optimizer", "prefix": "/api/v1", "tags": ["prompt-optimizer"]},
    {"module_path": "deeptutor.api.routers.monitor", "prefix": "/api/v1", "tags": ["monitor"]},
    {"module_path": "deeptutor.api.routers.openclaw", "prefix": "/api/v1", "tags": ["openclaw"]},
    {"module_path": "deeptutor.api.routers.openclaw_skills", "prefix": "/api/v1", "tags": ["openclaw-skills"]},
    {"module_path": "deeptutor.api.routers.paperbanana", "prefix": "/api/v1", "tags": ["paperbanana"]},
    {"module_path": "deeptutor.api.routers.search", "prefix": "/api/v1", "tags": ["search"]},
    {"module_path": "deeptutor.api.routers.knowledge_graph", "prefix": "/api/v1", "tags": ["knowledge-graph"]},
    {"module_path": "deeptutor.api.routers.chunked_upload", "prefix": "/api/v1/upload", "tags": ["chunked-upload"]},
    {"module_path": "deeptutor.api.routers.knowledge_base", "prefix": "/api/v1/kb", "tags": ["knowledge-base"]},
    {"module_path": "deeptutor.api.routers.knowledge_base_ws", "tags": ["knowledge-base-websocket"]},
    {"module_path": "deeptutor.api.routers.quick_commands", "prefix": "/api/v1", "tags": ["quick-commands"]},
    # Legacy admin / platform capability routes
    {"module_path": "deeptutor.api.routes.auth", "prefix": "/api/v1/auth", "tags": ["auth"]},
    {"module_path": "deeptutor.api.routes.auth_jwt", "prefix": "/api/v1", "tags": ["jwt-auth"]},
    {"module_path": "deeptutor.api.routes.rbac", "prefix": "/api/v1", "tags": ["rbac"]},
    {"module_path": "deeptutor.api.routes.users", "prefix": "/api/v1", "tags": ["users"]},
    {"module_path": "deeptutor.api.routes.departments", "prefix": "/api/v1/departments", "tags": ["departments"]},
    {"module_path": "deeptutor.api.routes.positions", "prefix": "/api/v1/positions", "tags": ["positions"]},
    {"module_path": "deeptutor.api.routes.monitoring", "prefix": "/api/v1/monitoring", "tags": ["monitoring"]},
    {"module_path": "deeptutor.api.routes.documents", "prefix": "/api/v1/documents", "tags": ["documents"]},
    {"module_path": "deeptutor.api.routes.documents", "prefix": "/api/v1/knowledge", "tags": ["documents"]},
    {"module_path": "deeptutor.api.routes.graphrag_knowledge", "prefix": "/api/graphrag-knowledge", "tags": ["graphrag-knowledge"]},
    {"module_path": "deeptutor.api.routes.clawx", "prefix": "/api/v1", "tags": ["clawx"]},
    {"module_path": "deeptutor.api.routes.supermemory", "prefix": "/api/v1", "tags": ["supermemory"]},
    {"module_path": "deeptutor.api.routes.openharness", "prefix": "/api/v1", "tags": ["openharness"]},
    {"module_path": "deeptutor.api.routes.permissions", "prefix": "/api/v1", "tags": ["openharness-permissions"]},
    {"module_path": "deeptutor.api.routes.websocket", "tags": ["openharness-websocket"]},
]

# Load legacy routers with batch logging
loaded_count = 0
skipped_count = 0
for legacy_router_spec in LEGACY_ROUTER_SPECS:
    try:
        _include_optional_legacy_router(**legacy_router_spec)
        loaded_count += 1
    except Exception:
        skipped_count += 1
        logger.debug("Skipped legacy router: %s", legacy_router_spec.get("module_path", "unknown"))

if loaded_count > 0:
    logger.info(f"Loaded {loaded_count} legacy routers ({skipped_count} skipped)")


@app.get("/")
async def root():
    return {"message": "Welcome to DeepTutor API"}


@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.3.6",
    }


if __name__ == "__main__":
    from deeptutor.api.run_server import main as run_server_main

    run_server_main()
