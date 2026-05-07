"""MCP (Model Context Protocol) Module for DeepTutor

Provides MCP client, server, and tool integration capabilities.

Based on the Model Context Protocol specification:
https://github.com/modelcontextprotocol/modelcontextprotocol
"""

from .client import MCPStreamClient, MCPClient
from .server import MCPServer
from .manager import MCPManager
from .adapter import MCPToolAdapter

__all__ = [
    "MCPStreamClient",
    "MCPClient",
    "MCPServer",
    "MCPManager",
    "MCPToolAdapter",
    "get_mcp_manager",
]

_mcp_manager = None


def get_mcp_manager(config: dict = None) -> MCPManager:
    """Get singleton MCP manager instance"""
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPManager(config or {})
    return _mcp_manager