"""MCP Tool Adapter for DeepTutor

Provides adapters to integrate existing tools with MCP protocol.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional

from deeptutor.integrations.nanobot.agent.tools.base import BaseTool, ToolRegistry

logger = logging.getLogger(__name__)


class MCPToolAdapter:
    """Adapter for converting tools to MCP format"""
    
    def __init__(self, tool_registry: Optional[ToolRegistry] = None):
        self.tool_registry = tool_registry or ToolRegistry()
    
    def adapt_tool(self, tool: BaseTool) -> Callable:
        """Adapt a BaseTool to MCP-compatible handler"""
        
        async def handler(**kwargs) -> Dict[str, Any]:
            """MCP-compatible tool handler"""
            try:
                result = await tool.run(**kwargs)
                
                if result.success:
                    return {"success": True, "data": result.data}
                else:
                    return {"success": False, "error": result.error}
            
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # Copy metadata
        handler.__doc__ = tool.description
        handler.__name__ = tool.name
        
        return handler
    
    def adapt_sync_tool(self, func: Callable) -> Callable:
        """Adapt a synchronous function to MCP-compatible handler"""
        
        async def handler(**kwargs) -> Dict[str, Any]:
            """MCP-compatible sync tool handler"""
            try:
                result = func(**kwargs)
                return {"success": True, "data": result}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        handler.__doc__ = func.__doc__
        handler.__name__ = func.__name__
        
        return handler
    
    def adapt_all_tools(self) -> Dict[str, Callable]:
        """Adapt all tools in registry to MCP format"""
        mcp_tools = {}
        
        for tool_name in self.tool_registry.list_tools():
            tool = self.tool_registry.get(tool_name)
            if tool:
                mcp_tools[tool_name] = self.adapt_tool(tool)
        
        return mcp_tools
    
    def get_tool_schema(self, tool: BaseTool) -> Dict[str, Any]:
        """Get MCP-compatible tool schema"""
        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters
        }
    
    def get_all_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get schemas for all adapted tools"""
        schemas = []
        
        for tool_name in self.tool_registry.list_tools():
            tool = self.tool_registry.get(tool_name)
            if tool:
                schemas.append(self.get_tool_schema(tool))
        
        return schemas


class MCPToNativeAdapter:
    """Adapter for converting MCP tools to native tools"""
    
    def __init__(self, mcp_client):
        self.mcp_client = mcp_client
    
    def create_native_tool(self, tool_name: str, schema: Dict[str, Any]) -> BaseTool:
        """Create a native tool wrapper for an MCP tool"""
        adapter = self
        
        class MCPWrappedTool(BaseTool):
            name = tool_name
            description = schema.get("description", "")
            parameters = schema.get("parameters", {})
            
            async def execute(self, **kwargs):
                result = await adapter.mcp_client.execute_tool(tool_name, kwargs)
                
                if result.get("error"):
                    return {"success": False, "error": result["error"]}
                
                output = result.get("result", {}).get("output", {})
                return {"success": output.get("success", True), "data": output.get("data")}
        
        return MCPWrappedTool()
    
    async def sync_tools(self, tool_registry: ToolRegistry):
        """Sync MCP tools to native tool registry"""
        tools = await self.mcp_client.list_tools()
        
        for tool_info in tools.get("result", {}).get("tools", []):
            tool_name = tool_info.get("name")
            if tool_name:
                native_tool = self.create_native_tool(tool_name, tool_info)
                tool_registry.register(native_tool)