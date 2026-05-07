"""
Tool Registry
=============

Central registry that discovers and manages all tools (built-in and plugin).
Provides lookup, listing, and OpenAI schema generation.
"""

from __future__ import annotations

import logging
from typing import Any

from deeptutor.core.tool_protocol import BaseTool, ToolDefinition, ToolPromptHints
from deeptutor.tools.builtin import (
    BUILTIN_TOOL_TYPES,
    TOOL_ALIASES,
    _get_chat_parser_tool,
    _get_doc_llama_tool,
    _get_forensics_py_tool,
    _get_langextract_tool,
    _get_legal_ie_tool,
    _get_log_parser_tool,
    _get_memagent_tool,
)
from deeptutor.tools.prompting import ToolPromptComposer

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Singleton-ish registry of all available tools.

    Usage::

        registry = ToolRegistry()
        registry.load_builtins()
        rag = registry.get("rag")
        result = await rag.execute(query="hello")
    """

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        name = tool.name
        self._tools[name] = tool
        logger.debug("Registered tool: %s", name)

    def load_builtins(self) -> None:
        """Instantiate and register all built-in tools."""
        for tool_type in BUILTIN_TOOL_TYPES:
            try:
                tool = tool_type()
            except Exception:
                logger.warning("Failed to instantiate built-in tool %s", tool_type, exc_info=True)
                continue
            if tool.name in self._tools:
                continue
            self.register(tool)
        # Load forensic analysis tools
        self._load_forensic_tools()
        # Load MCP tools (discovered from Claude Desktop config)
        self._load_mcp_tools()

    def _load_forensic_tools(self) -> None:
        """Load forensic analysis tools (lazy-loaded to avoid import issues)."""
        forensic_loaders = [
            _get_legal_ie_tool,
            _get_langextract_tool,
            _get_log_parser_tool,
            _get_chat_parser_tool,
            _get_doc_llama_tool,
            _get_forensics_py_tool,
            _get_memagent_tool,
        ]
        for loader in forensic_loaders:
            try:
                tool = loader()
                if tool.name not in self._tools:
                    self.register(tool)
            except Exception:
                logger.warning("Failed to load forensic tool from %s", loader.__name__, exc_info=True)

    def _load_mcp_tools(self) -> None:
        """Load MCP tools discovered from Claude Desktop config."""
        try:
            import asyncio

            from deeptutor.tools.builtin.mcp_tool import register_mcp_tools
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're in an async context, create a new loop
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        tools = pool.submit(asyncio.run, register_mcp_tools()).result()
                else:
                    tools = asyncio.run(register_mcp_tools())
            except RuntimeError:
                # No event loop running, use asyncio.run
                tools = asyncio.run(register_mcp_tools())
            for tool in tools:
                if tool.name not in self._tools:
                    self.register(tool)
                    logger.info("Registered MCP tool: %s", tool.name)
        except Exception:
            logger.warning("Failed to load MCP tools", exc_info=True)

    def _resolve_request(
        self,
        name: str,
        kwargs: dict[str, Any] | None = None,
    ) -> tuple[str, dict[str, Any]]:
        if name in self._tools:
            return name, dict(kwargs or {})

        resolved_name, default_kwargs = TOOL_ALIASES.get(name, (name, {}))
        merged_kwargs = {**default_kwargs, **(kwargs or {})}

        if resolved_name == "code_execution" and "query" in merged_kwargs:
            merged_kwargs.setdefault("intent", merged_kwargs.pop("query"))

        return resolved_name, merged_kwargs

    def get(self, name: str) -> BaseTool | None:
        resolved_name, _ = self._resolve_request(name)
        return self._tools.get(resolved_name)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def get_enabled(self, names: list[str]) -> list[BaseTool]:
        """Return tool instances for the given names (skipping unknown)."""
        enabled: list[BaseTool] = []
        seen: set[str] = set()
        for name in names:
            tool = self.get(name)
            if tool is None or tool.name in seen:
                continue
            enabled.append(tool)
            seen.add(tool.name)
        return enabled

    def get_definitions(self, names: list[str] | None = None) -> list[ToolDefinition]:
        """Return definitions for *names* (or all if None)."""
        tools = self._tools.values() if names is None else self.get_enabled(names)
        return [t.get_definition() for t in tools]

    def get_prompt_hints(
        self,
        names: list[str],
        language: str = "en",
    ) -> list[tuple[str, ToolPromptHints]]:
        """Return prompt hints for the given tool names."""
        entries: list[tuple[str, ToolPromptHints]] = []
        for tool in self.get_enabled(names):
            entries.append((tool.name, tool.get_prompt_hints(language=language)))
        return entries

    def build_prompt_text(
        self,
        names: list[str],
        format: str = "list",
        language: str = "en",
        **opts: Any,
    ) -> str:
        """Compose prompt text for the given tools."""
        composer = ToolPromptComposer(language=language)
        hints = self.get_prompt_hints(names, language=language)
        if format == "list":
            return composer.format_list(hints, kb_name=opts.get("kb_name", ""))
        if format == "table":
            return composer.format_table(
                hints,
                control_actions=opts.get("control_actions"),
            )
        if format == "aliases":
            return composer.format_aliases(hints)
        if format == "phased":
            return composer.format_phased(hints)
        raise ValueError(f"Unsupported prompt format: {format}")

    def build_openai_schemas(self, names: list[str] | None = None) -> list[dict[str, Any]]:
        """Build OpenAI function-calling tool schemas."""
        return [d.to_openai_schema() for d in self.get_definitions(names)]

    async def execute(self, name: str, **kwargs: Any):
        """Resolve aliases, execute the tool, and return its ToolResult."""
        resolved_name, resolved_kwargs = self._resolve_request(name, kwargs)
        tool = self._tools.get(resolved_name)
        if tool is None:
            raise KeyError(f"Unknown tool: {name}")
        return await tool.execute(**resolved_kwargs)


_default_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    """Return the global ToolRegistry (creating & loading builtins on first call)."""
    global _default_registry
    if _default_registry is None:
        _default_registry = ToolRegistry()
        _default_registry.load_builtins()
    return _default_registry
