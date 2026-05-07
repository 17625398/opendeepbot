"""
Graphify MCP 服务器

提供 MCP (Model Context Protocol) 接口让 AI 助手调用 Graphify 功能
"""

import json
import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)

# MCP 工具定义
MCP_TOOLS = [
    {
        "name": "query_graph",
        "description": "查询知识图谱，获取与问题相关的节点和关系",
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "查询问题"
                },
                "max_results": {
                    "type": "number",
                    "description": "最大结果数",
                    "default": 10
                }
            },
            "required": ["question"]
        }
    },
    {
        "name": "get_node",
        "description": "获取指定节点的信息",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {
                    "type": "string",
                    "description": "节点 ID 或名称"
                }
            },
            "required": ["node_id"]
        }
    },
    {
        "name": "get_neighbors",
        "description": "获取节点的邻居节点",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {
                    "type": "string",
                    "description": "节点 ID"
                },
                "max_depth": {
                    "type": "number",
                    "description": "最大深度",
                    "default": 1
                }
            },
            "required": ["node_id"]
        }
    },
    {
        "name": "shortest_path",
        "description": "查找两个节点之间的最短路径",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "源节点 ID"
                },
                "target": {
                    "type": "string",
                    "description": "目标节点 ID"
                }
            },
            "required": ["source", "target"]
        }
    },
    {
        "name": "build_graph",
        "description": "构建知识图谱",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_dir": {
                    "type": "string",
                    "description": "目标目录路径"
                },
                "mode": {
                    "type": "string",
                    "description": "构建模式",
                    "enum": ["normal", "deep"],
                    "default": "normal"
                }
            },
            "required": ["target_dir"]
        }
    },
    {
        "name": "get_statistics",
        "description": "获取图谱统计信息",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_report",
        "description": "获取 GRAPH_REPORT.md 报告内容",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
]


class GraphifyMCPServer:
    """
    Graphify MCP 服务器
    
    提供 MCP 协议接口供 AI 助手调用
    """

    def __init__(self):
        """初始化 MCP 服务器"""
        self.tools = MCP_TOOLS
        self._service = None

    def _get_service(self):
        """获取 Graphify 服务"""
        if self._service is None:
            from deeptutor.services.graphify_service import get_graphify_service
            self._service = get_graphify_service()
        return self._service

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        列出所有可用工具
        
        Returns:
            工具定义列表
        """
        return self.tools

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        调用工具
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具执行结果
        """
        try:
            if tool_name == "query_graph":
                return await self._query_graph(**arguments)
            elif tool_name == "get_node":
                return await self._get_node(**arguments)
            elif tool_name == "get_neighbors":
                return await self._get_neighbors(**arguments)
            elif tool_name == "shortest_path":
                return await self._shortest_path(**arguments)
            elif tool_name == "build_graph":
                return await self._build_graph(**arguments)
            elif tool_name == "get_statistics":
                return await self._get_statistics()
            elif tool_name == "get_report":
                return await self._get_report()
            else:
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}"
                }
        except Exception as e:
            logger.exception(f"MCP tool call failed: {tool_name}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _query_graph(
        self,
        question: str,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """查询图谱"""
        service = self._get_service()
        result = await service.query(
            question=question,
            max_results=max_results
        )
        
        return {
            "success": result.success,
            "answer": result.answer,
            "nodes": [n.to_dict() for n in result.nodes],
            "edges": [e.to_dict() for e in result.edges],
            "sources": result.sources,
            "error": result.error
        }

    async def _get_node(self, node_id: str) -> Dict[str, Any]:
        """获取节点"""
        service = self._get_service()
        node = await service.get_node(node_id)
        
        if node is None:
            return {
                "success": False,
                "error": f"Node not found: {node_id}"
            }
        
        return {
            "success": True,
            "node": node.to_dict()
        }

    async def _get_neighbors(
        self,
        node_id: str,
        max_depth: int = 1
    ) -> Dict[str, Any]:
        """获取邻居"""
        service = self._get_service()
        neighbors = await service.get_neighbors(node_id, max_depth)
        
        return {
            "success": True,
            "node_id": node_id,
            "neighbors": [n.to_dict() for n in neighbors]
        }

    async def _shortest_path(self, source: str, target: str) -> Dict[str, Any]:
        """查找路径"""
        service = self._get_service()
        path = await service.shortest_path(source, target)
        
        return {
            "success": True,
            "source": source,
            "target": target,
            "path": path,
            "length": len(path) - 1 if path else 0
        }

    async def _build_graph(
        self,
        target_dir: str,
        mode: str = "normal"
    ) -> Dict[str, Any]:
        """构建图谱"""
        service = self._get_service()
        result = await service.build(
            target_dir=target_dir,
            mode=mode
        )
        
        return {
            "success": result.success,
            "output_dir": result.output_dir,
            "nodes_count": result.nodes_count,
            "edges_count": result.edges_count,
            "duration": result.duration,
            "error": result.error
        }

    async def _get_statistics(self) -> Dict[str, Any]:
        """获取统计"""
        service = self._get_service()
        stats = service.get_statistics()
        
        return {
            "success": True,
            **stats
        }

    async def _get_report(self) -> Dict[str, Any]:
        """获取报告"""
        service = self._get_service()
        report = await service.get_report()
        
        if report is None:
            return {
                "success": False,
                "error": "Report not found. Run build_graph first."
            }
        
        return {
            "success": True,
            "report": report
        }


# 全局 MCP 服务器实例
_graphify_mcp: Optional[GraphifyMCPServer] = None


def get_graphify_mcp() -> GraphifyMCPServer:
    """获取 Graphify MCP 服务器实例"""
    global _graphify_mcp
    if _graphify_mcp is None:
        _graphify_mcp = GraphifyMCPServer()
    return _graphify_mcp
