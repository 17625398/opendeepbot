"""MCP Manager for DeepTutor

Manages multiple MCP servers and provides unified access to MCP tools.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from .client import MCPStreamClient

logger = logging.getLogger(__name__)


class MCPManager:
    """Manages multiple MCP servers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.clients: Dict[str, MCPStreamClient] = {}
        self._running = False
        self._tasks: List[asyncio.Task] = []
    
    async def start_server(self, name: str, command: str, args: List[str] = None) -> bool:
        """Start an MCP server
        
        Args:
            name: Server name for reference
            command: Command to start the MCP server
            args: Additional arguments
            
        Returns:
            True if server started successfully
        """
        if name in self.clients:
            logger.warning(f"MCP server {name} already running")
            return False
        
        client = MCPStreamClient()
        success = await client.initialize(command, args)
        
        if success:
            self.clients[name] = client
            logger.info(f"MCP server started: {name}")
            return True
        
        return False
    
    async def stop_server(self, name: str) -> bool:
        """Stop an MCP server"""
        if name not in self.clients:
            return False
        
        client = self.clients[name]
        await client.shutdown()
        del self.clients[name]
        logger.info(f"MCP server stopped: {name}")
        return True
    
    async def list_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """List all tools from all MCP servers"""
        all_tools = {}
        
        for name, client in self.clients.items():
            try:
                result = await client.list_tools()
                tools = result.get("result", {}).get("tools", [])
                all_tools[name] = tools
            except Exception as e:
                logger.error(f"Error listing tools from {name}: {e}")
        
        return all_tools
    
    async def execute_tool(self, server_name: str, tool_name: str, 
                          arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool on a specific MCP server"""
        if server_name not in self.clients:
            return {"error": f"MCP server not found: {server_name}"}
        
        client = self.clients[server_name]
        return await client.execute_tool(tool_name, arguments)
    
    async def execute_tool_any(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool on any available server that has it"""
        for name, client in self.clients.items():
            try:
                tools = await client.list_tools()
                tool_list = tools.get("result", {}).get("tools", [])
                tool_names = [t.get("name") for t in tool_list]
                
                if tool_name in tool_names:
                    return await client.execute_tool(tool_name, arguments)
            except Exception as e:
                logger.error(f"Error checking tools on {name}: {e}")
        
        return {"error": f"Tool not found on any MCP server: {tool_name}"}
    
    def list_servers(self) -> List[str]:
        """List all running MCP servers"""
        return list(self.clients.keys())
    
    async def start_all(self):
        """Start all configured MCP servers"""
        servers = self.config.get("servers", [])
        
        for server in servers:
            name = server.get("name")
            command = server.get("command")
            args = server.get("args", [])
            
            if name and command:
                await self.start_server(name, command, args)
    
    async def stop_all(self):
        """Stop all running MCP servers"""
        for name in list(self.clients.keys()):
            await self.stop_server(name)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all MCP servers"""
        health = {
            "status": "healthy",
            "servers": {}
        }
        
        all_healthy = True
        for name, client in self.clients.items():
            try:
                result = await client.list_tools()
                if result.get("error"):
                    health["servers"][name] = {"status": "unhealthy", "error": result["error"]}
                    all_healthy = False
                else:
                    tool_count = len(result.get("result", {}).get("tools", []))
                    health["servers"][name] = {"status": "healthy", "tool_count": tool_count}
            except Exception as e:
                health["servers"][name] = {"status": "unhealthy", "error": str(e)}
                all_healthy = False
        
        health["status"] = "healthy" if all_healthy else "degraded"
        return health