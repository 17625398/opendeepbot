"""MCP Client for DeepTutor

Implements MCP (Model Context Protocol) client for communicating with MCP servers.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class MCPStreamClient:
    """MCP Stream Client - communicates via stdio streams"""
    
    def __init__(self, process: asyncio.subprocess.Process = None):
        self.process = process
        self._lock = asyncio.Lock()
    
    async def initialize(self, command: str, args: List[str] = None):
        """Initialize the MCP server process"""
        args = args or []
        
        try:
            self.process = await asyncio.create_subprocess_exec(
                command,
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            logger.info(f"MCP server started: {command}")
            return True
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            return False
    
    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the MCP server"""
        if not self.process or not self.process.stdin or not self.process.stdout:
            return {"error": "MCP server not initialized"}
        
        async with self._lock:
            try:
                # Send request
                request_json = json.dumps(request) + "\n"
                self.process.stdin.write(request_json.encode())
                await self.process.stdin.drain()
                
                # Read response
                response_line = await self.process.stdout.readline()
                if not response_line:
                    return {"error": "No response from MCP server"}
                
                response = json.loads(response_line.decode().strip())
                return response
            
            except json.JSONDecodeError:
                return {"error": "Invalid JSON response from MCP server"}
            except Exception as e:
                return {"error": f"MCP communication error: {e}"}
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available tools from MCP server"""
        request = {
            "method": "list_tools",
            "params": {}
        }
        return await self.send_request(request)
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool on the MCP server"""
        request = {
            "method": "execute_tool",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        return await self.send_request(request)
    
    async def shutdown(self):
        """Shutdown the MCP server"""
        if self.process:
            try:
                if self.process.stdin:
                    self.process.stdin.close()
                self.process.terminate()
                await self.process.wait()
            except Exception as e:
                logger.error(f"Error shutting down MCP server: {e}")


class MCPClient:
    """MCP Client - base class for MCP communication"""
    
    def __init__(self, server_url: Optional[str] = None):
        self.server_url = server_url
        self._tools: Optional[List[Dict[str, Any]]] = None
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools"""
        if self._tools is None:
            await self._fetch_tools()
        return self._tools or []
    
    async def _fetch_tools(self):
        """Fetch tools from server"""
        pass
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool"""
        pass
    
    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get schema for a specific tool"""
        for tool in self._tools or []:
            if tool.get("name") == tool_name:
                return tool
        return None
    
    def validate_tool_arguments(self, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """Validate tool arguments against schema"""
        schema = self.get_tool_schema(tool_name)
        if not schema:
            return False
        
        params = schema.get("parameters", {})
        required = params.get("required", [])
        
        for param in required:
            if param not in arguments:
                logger.warning(f"Missing required parameter: {param}")
                return False
        
        return True