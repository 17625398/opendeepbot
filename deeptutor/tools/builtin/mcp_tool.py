"""MCP (Model Context Protocol) tool integration for DeepSeek.
MCP（模型上下文协议）工具集成 - 用于 DeepSeek。
"""

from __future__ import annotations

import asyncio
import json
import subprocess
from typing import Any

from deeptutor.core.tool_protocol import BaseTool, ToolDefinition, ToolParameter, ToolResult


class MCPTool(BaseTool):
    """Generic MCP server integration tool."""

    def __init__(self, server_name: str, command: list[str], env: dict[str, str] | None = None):
        self.server_name = server_name
        self.command = command
        self.env = env or {}
        self._description = f"MCP server: {server_name}"

    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=f"mcp_{self.server_name}",
            description=self._description,
            parameters=[
                ToolParameter(
                    name="tool_name",
                    type="string",
                    description="Name of the tool to call on the MCP server.",
                ),
                ToolParameter(
                    name="arguments",
                    type="string",
                    description="JSON arguments for the tool (as a JSON string).",
                ),
            ],
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        tool_name = kwargs.get("tool_name", "")
        arguments = kwargs.get("arguments", "{}")

        if not tool_name:
            return ToolResult(content="Error: tool_name is required.", success=False)

        try:
            # Call MCP server via mcp-cli (assuming mcp-cli is installed)
            # Format: mcp call <server> <tool> [args_json]
            cmd = ["mcp", "call", self.server_name, tool_name, arguments]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**subprocess.environ, **self.env},
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                error = stderr.decode("utf-8", errors="replace") if stderr else "Unknown error"
                return ToolResult(
                    content=f"MCP call failed: {error}",
                    success=False,
                )

            output = stdout.decode("utf-8", errors="replace")
            return ToolResult(content=output, success=True)

        except Exception as e:
            return ToolResult(content=f"Error calling MCP tool: {e}", success=False)


def discover_mcp_servers(config_path: str | None = None) -> list[dict[str, Any]]:
    """Discover MCP servers from config file (Claude Desktop format)."""
    import os
    from pathlib import Path

    if config_path is None:
        # Default locations
        if os.name == "nt":  # Windows
            config_path = str(
                Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
            )
        else:
            config_path = str(
                Path.home() / ".config" / "Claude" / "claude_desktop_config.json"
            )

    if not Path(config_path).exists():
        return []

    try:
        data = json.loads(Path(config_path).read_text())
        servers = []
        for name, config in data.get("mcpServers", {}).items():
            servers.append({
                "name": name,
                "command": config.get("command", ""),
                "args": config.get("args", []),
                "env": config.get("env", {}),
            })
        return servers
    except Exception:
        return []


async def register_mcp_tools(config_path: str | None = None) -> list[MCPTool]:
    """Discover and register MCP servers as tools."""
    servers = discover_mcp_servers(config_path)
    tools = []
    for server in servers:
        tool = MCPTool(
            server_name=server["name"],
            command=[server["command"]] + server["args"],
            env=server.get("env"),
        )
        tools.append(tool)
    return tools
