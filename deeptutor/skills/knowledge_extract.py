"""
Knowledge Extraction Skill / 知识提取技能

Integrates Hyper-Extract for intelligent knowledge extraction from unstructured text.
集成 Hyper-Extract 实现从非结构化文本中智能提取知识。

Features / 功能特性:
- Knowledge Graph extraction / 知识图谱提取
- Hypergraph extraction / 超图提取
- Spatio-temporal extraction / 时空关系提取
- Domain-specific templates / 领域特定模板
"""

import logging
from typing import Dict, Any, Optional

from deeptutor.tools.knowledge_extractor import get_extractor

logger = logging.getLogger(__name__)


class KnowledgeExtractSkill:
    """
    Knowledge extraction skill for DeepTutor
    
    DeepTutor 知识提取技能
    
    This skill provides intelligent knowledge extraction capabilities using Hyper-Extract.
    本技能使用 Hyper-Extract 提供智能知识提取能力。
    """
    
    NAME = "knowledge_extract"
    DESCRIPTION = "Extract structured knowledge from unstructured text using Hyper-Extract"
    DESCRIPTION_ZH = "使用 Hyper-Extract 从非结构化文本中提取结构化知识"
    
    def __init__(self):
        """Initialize the skill / 初始化技能"""
        self.extractor = get_extractor()
    
    def is_available(self) -> bool:
        """
        Check if the skill is available / 检查技能是否可用
        
        Returns:
            bool: True if Hyper-Extract is available
        """
        return self.extractor.is_available()
    
    def extract(self, text: str, output_type: str = "all", template: str = "general") -> Dict[str, Any]:
        """
        Extract knowledge from text / 从文本中提取知识
        
        Args:
            text: Input text to extract from / 要提取的输入文本
            output_type: Type of output (graph, hypergraph, temporal, spatial, all)
                        / 输出类型（知识图谱、超图、时间、空间、全部）
            template: Domain template name / 领域模板名称
        
        Returns:
            Dict containing extracted knowledge / 包含提取知识的字典
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "Knowledge extraction service not available / 知识提取服务不可用"
            }
        
        try:
            if output_type == "graph":
                return self.extractor.extract_knowledge_graph(text, template)
            elif output_type == "hypergraph":
                return self.extractor.extract_hypergraph(text, template)
            elif output_type == "temporal":
                return self.extractor.extract_temporal(text, template)
            elif output_type == "spatial":
                return self.extractor.extract_spatial(text, template)
            else:
                return self.extractor.extract_all(text, template)
        except Exception as e:
            logger.error(f"Knowledge extraction failed: {e}")
            return {
                "success": False,
                "error": f"Extraction failed: {str(e)} / 提取失败: {str(e)}"
            }
    
    def extract_graph(self, text: str, template: str = "general") -> Dict[str, Any]:
        """
        Extract knowledge graph / 提取知识图谱
        
        Args:
            text: Input text / 输入文本
            template: Domain template / 领域模板
        
        Returns:
            Dictionary with entities and relations / 包含实体和关系的字典
        """
        return self.extract(text, output_type="graph", template=template)
    
    def extract_hypergraph(self, text: str, template: str = "general") -> Dict[str, Any]:
        """
        Extract hypergraph (multi-entity relationships) / 提取超图（多实体关系）
        
        Args:
            text: Input text / 输入文本
            template: Domain template / 领域模板
        
        Returns:
            Dictionary with hyperedges / 包含超边的字典
        """
        return self.extract(text, output_type="hypergraph", template=template)
    
    def extract_temporal(self, text: str, template: str = "general") -> Dict[str, Any]:
        """
        Extract temporal relationships / 提取时间关系
        
        Args:
            text: Input text / 输入文本
            template: Domain template / 领域模板
        
        Returns:
            Dictionary with temporal information / 包含时间信息的字典
        """
        return self.extract(text, output_type="temporal", template=template)
    
    def extract_spatial(self, text: str, template: str = "general") -> Dict[str, Any]:
        """
        Extract spatial relationships / 提取空间关系
        
        Args:
            text: Input text / 输入文本
            template: Domain template / 领域模板
        
        Returns:
            Dictionary with spatial information / 包含空间信息的字典
        """
        return self.extract(text, output_type="spatial", template=template)
    
    def list_templates(self) -> list:
        """
        List available domain templates / 列出可用的领域模板
        
        Returns:
            List of template names / 模板名称列表
        """
        return self.extractor.list_templates()
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """
        Get tool definition for agent integration / 获取工具定义用于代理集成
        
        Returns:
            Tool definition dictionary / 工具定义字典
        """
        return {
            "name": self.NAME,
            "description": self.DESCRIPTION,
            "description_zh": self.DESCRIPTION_ZH,
            "parameters": {
                "text": {
                    "type": "string",
                    "description": "Text to extract knowledge from / 要提取知识的文本",
                    "required": True
                },
                "output_type": {
                    "type": "string",
                    "description": "Output type: graph, hypergraph, temporal, spatial, or all / 输出类型",
                    "default": "all",
                    "required": False
                },
                "template": {
                    "type": "string",
                    "description": "Domain template name / 领域模板名称",
                    "default": "general",
                    "required": False
                }
            },
            "returns": {
                "type": "object",
                "description": "Extracted knowledge structure / 提取的知识结构"
            }
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the skill / 执行技能
        
        Args:
            kwargs: Parameters for extraction / 提取参数
        
        Returns:
            Extracted knowledge / 提取的知识
        """
        text = kwargs.get("text", "")
        output_type = kwargs.get("output_type", "all")
        template = kwargs.get("template", "general")
        
        if not text:
            return {
                "success": False,
                "error": "Text parameter is required / 需要提供文本参数"
            }
        
        return self.extract(text, output_type, template)


# Global skill instance / 全局技能实例
_skill_instance = None

def get_skill() -> KnowledgeExtractSkill:
    """
    Get or create the knowledge extraction skill instance
    获取或创建知识提取技能实例
    """
    global _skill_instance
    if _skill_instance is None:
        _skill_instance = KnowledgeExtractSkill()
    return _skill_instance
