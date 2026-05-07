"""MCP Server for DeepTutor

Implements MCP (Model Context Protocol) server for hosting tools.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class MCPServer:
    """MCP Server - hosts tools and responds to MCP requests"""
    
    def __init__(self, tools: Dict[str, Callable] = None):
        self.tools = tools or {}
        self._running = False
        self._server_task: Optional[asyncio.Task] = None
    
    def register_tool(self, name: str, handler: Callable):
        """Register a tool with the server"""
        self.tools[name] = handler
        logger.info(f"Registered MCP tool: {name}")
    
    def unregister_tool(self, name: str):
        """Unregister a tool"""
        if name in self.tools:
            del self.tools[name]
            logger.info(f"Unregistered MCP tool: {name}")
    
    async def _handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an MCP request"""
        method = request.get("method")
        params = request.get("params", {})
        
        try:
            if method == "list_tools":
                return await self._handle_list_tools()
            elif method == "execute_tool":
                return await self._handle_execute_tool(params)
            else:
                return {"error": f"Unknown method: {method}"}
        
        except Exception as e:
            logger.error(f"MCP request error: {e}")
            return {"error": str(e)}
    
    async def _handle_list_tools(self) -> Dict[str, Any]:
        """Handle list_tools request"""
        tools = []
        
        for name, handler in self.tools.items():
            tool_info = {
                "name": name,
                "description": getattr(handler, "__doc__", ""),
                "parameters": {}
            }
            tools.append(tool_info)
        
        return {"result": {"tools": tools}}
    
    async def _handle_execute_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle execute_tool request"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name not in self.tools:
            return {"error": f"Tool not found: {tool_name}"}
        
        try:
            handler = self.tools[tool_name]
            
            if asyncio.iscoroutinefunction(handler):
                result = await handler(**arguments)
            else:
                result = handler(**arguments)
            
            return {"result": {"output": result}}
        
        except Exception as e:
            return {"error": str(e)}
    
    async def _run(self):
        """Run the MCP server"""
        logger.info("Starting MCP server...")
        
        while self._running:
            try:
                # Read request from stdin
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                
                if not line:
                    break
                
                try:
                    request = json.loads(line.strip())
                except json.JSONDecodeError:
                    response = {"error": "Invalid JSON"}
                    print(json.dumps(response), flush=True)
                    continue
                
                # Process request
                response = await self._handle_request(request)
                
                # Write response to stdout
                print(json.dumps(response), flush=True)
                
            except Exception as e:
                logger.error(f"MCP server error: {e}")
                await asyncio.sleep(1)
    
    async def start(self):
        """Start the MCP server"""
        if self._running:
            return
        
        self._running = True
        self._server_task = asyncio.create_task(self._run())
        logger.info("MCP server started")
    
    async def stop(self):
        """Stop the MCP server"""
        self._running = False
        
        if self._server_task:
            self._server_task.cancel()
            try:
                await self._server_task
            except asyncio.CancelledError:
                pass
        
        logger.info("MCP server stopped")
    
    def run_sync(self):
        """Run the server synchronously (for use as standalone script)"""
        asyncio.run(self.start())
        
        try:
            asyncio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            asyncio.run(self.stop())