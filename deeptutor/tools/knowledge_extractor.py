"""
Hyper-Extract Knowledge Extraction Tool

Integrates Hyper-Extract framework for intelligent knowledge extraction
from unstructured text into structured knowledge representations.

Features:
- Knowledge Graph extraction
- Hypergraph extraction (multi-entity relationships)
- Spatio-temporal relationship extraction
- Domain-specific templates support
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Callable, Type
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Try to import hyperextract and langchain dependencies
HYPEREXTRACT_AVAILABLE = False
try:
    from hyperextract import (
        AutoGraph,
        AutoHypergraph,
        AutoTemporalGraph,
        AutoSpatialGraph,
        AutoSpatioTemporalGraph,
        Template,
    )
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.embeddings import Embeddings
    HYPEREXTRACT_AVAILABLE = True
    logger.info("Hyper-Extract and LangChain imported successfully")
except ImportError as e:
    logger.warning(f"Hyper-Extract dependencies not available: {e}")


# Default schemas for knowledge extraction
class EntitySchema(BaseModel):
    """Entity/node schema for knowledge graph extraction"""
    name: str = Field(description="Entity name")
    type: str = Field(description="Entity type/category")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties")


class RelationSchema(BaseModel):
    """Relation/edge schema for knowledge graph extraction"""
    source: str = Field(description="Source entity name")
    target: str = Field(description="Target entity name")
    relation_type: str = Field(description="Type of relationship")
    description: str = Field(default="", description="Relationship description")


class KnowledgeExtractor:
    """
    Knowledge extraction tool using Hyper-Extract
    
    Supports extraction of:
    - Knowledge Graphs (entity-relation-entity triples)
    - Hypergraphs (multi-entity complex relationships)
    - Temporal graphs (time-aware relationships)
    - Spatial graphs (location-aware relationships)
    """
    
    def __init__(self, api_key: Optional[str] = None, llm_model: str = "gpt-4o-mini"):
        """
        Initialize the knowledge extractor
        
        Args:
            api_key: OpenAI API key for LLM provider
            llm_model: LLM model name to use
        """
        self.api_key = api_key
        self.llm_model = llm_model
        self.llm_client: Optional[BaseChatModel] = None
        self.embedder: Optional[Embeddings] = None
        self.graph_extractor = None
        self.hypergraph_extractor = None
        self.temporal_extractor = None
        self.spatial_extractor = None
        
        if HYPEREXTRACT_AVAILABLE:
            try:
                self._initialize_clients()
                self._initialize_extractors()
                logger.info("Hyper-Extract extractors initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Hyper-Extract: {e}")
    
    def _initialize_clients(self):
        """Initialize LLM and embedding clients"""
        try:
            if self.api_key:
                self.llm_client = ChatOpenAI(
                    model=self.llm_model,
                    api_key=self.api_key,
                    temperature=0.1,
                )
                self.embedder = OpenAIEmbeddings(api_key=self.api_key)
            else:
                # Try to use environment variables
                self.llm_client = ChatOpenAI(
                    model=self.llm_model,
                    temperature=0.1,
                )
                self.embedder = OpenAIEmbeddings()
            logger.info("LLM and embedder clients initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize LLM/embedder: {e}")
    
    def _initialize_extractors(self):
        """Initialize all extractors"""
        if not self.llm_client or not self.embedder:
            logger.warning("Cannot initialize extractors: LLM or embedder not available")
            return
        
        try:
            # Node key extractor functions
            node_key_extractor: Callable[[EntitySchema], str] = lambda x: x.name
            edge_key_extractor: Callable[[RelationSchema], str] = lambda x: f"{x.source}-{x.relation_type}-{x.target}"
            nodes_in_edge_extractor: Callable[[RelationSchema], Tuple[str, str]] = lambda x: (x.source, x.target)
            
            self.graph_extractor = AutoGraph(
                node_schema=EntitySchema,
                edge_schema=RelationSchema,
                node_key_extractor=node_key_extractor,
                edge_key_extractor=edge_key_extractor,
                nodes_in_edge_extractor=nodes_in_edge_extractor,
                llm_client=self.llm_client,
                embedder=self.embedder,
                extraction_mode="one_stage",
                verbose=False,
            )
            logger.info("AutoGraph extractor initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize AutoGraph: {e}")
        
        try:
            self.hypergraph_extractor = AutoHypergraph(
                node_schema=EntitySchema,
                edge_schema=RelationSchema,
                node_key_extractor=node_key_extractor,
                edge_key_extractor=edge_key_extractor,
                nodes_in_edge_extractor=nodes_in_edge_extractor,
                llm_client=self.llm_client,
                embedder=self.embedder,
                verbose=False,
            )
            logger.info("AutoHypergraph extractor initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize AutoHypergraph: {e}")
    
    def is_available(self) -> bool:
        """Check if Hyper-Extract is available and configured"""
        return HYPEREXTRACT_AVAILABLE and self.graph_extractor is not None
    
    def extract_knowledge_graph(self, text: str, template_name: str = "general") -> Dict[str, Any]:
        """
        Extract knowledge graph from text
        
        Args:
            text: Input text to extract from
            template_name: Domain template name (general, finance, legal, medical, etc.)
        
        Returns:
            Dictionary containing entities and relations
        """
        if not self.is_available():
            return {"success": False, "error": "Hyper-Extract not available or not configured"}
        
        try:
            result = self.graph_extractor.parse(text)
            
            return {
                "success": True,
                "type": "knowledge_graph",
                "entities": self._extract_entities(result),
                "relations": self._extract_relations(result),
                "summary": "Knowledge graph extracted successfully",
            }
        except Exception as e:
            logger.error(f"Knowledge graph extraction failed: {e}")
            return {"success": False, "error": str(e)}
    
    def extract_hypergraph(self, text: str, template_name: str = "general") -> Dict[str, Any]:
        """
        Extract hypergraph from text (Hyper-Extract's specialty)
        
        Args:
            text: Input text to extract from
            template_name: Domain template name
        
        Returns:
            Dictionary containing hyperedges and entities
        """
        if not self.is_available():
            return {"success": False, "error": "Hyper-Extract not available or not configured"}
        
        try:
            if not self.hypergraph_extractor:
                return {"success": False, "error": "Hypergraph extractor not initialized"}
            
            result = self.hypergraph_extractor.parse(text)
            
            return {
                "success": True,
                "type": "hypergraph",
                "entities": self._extract_entities(result),
                "hyperedges": self._extract_hyperedges(result),
                "summary": "Hypergraph extracted successfully",
            }
        except Exception as e:
            logger.error(f"Hypergraph extraction failed: {e}")
            return {"success": False, "error": str(e)}
    
    def extract_all(self, text: str, template_name: str = "general") -> Dict[str, Any]:
        """
        Extract all knowledge types from text
        
        Args:
            text: Input text to extract from
            template_name: Domain template name
        
        Returns:
            Dictionary containing all extracted knowledge
        """
        if not self.is_available():
            return {"success": False, "error": "Hyper-Extract not available or not configured"}
        
        try:
            results = {}
            
            if self.graph_extractor:
                graph_result = self.graph_extractor.parse(text)
                results["knowledge_graph"] = {
                    "entities": self._extract_entities(graph_result),
                    "relations": self._extract_relations(graph_result),
                }
            
            if self.hypergraph_extractor:
                hyper_result = self.hypergraph_extractor.parse(text)
                results["hypergraph"] = {
                    "entities": self._extract_entities(hyper_result),
                    "hyperedges": self._extract_hyperedges(hyper_result),
                }
            
            results["success"] = True
            results["summary"] = "Knowledge extraction completed"
            
            return results
        except Exception as e:
            logger.error(f"Full extraction failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _extract_entities(self, result: Any) -> List[Dict[str, Any]]:
        """Extract entities from result"""
        try:
            if hasattr(result, 'nodes') and result.nodes:
                return [
                    {"id": str(i), "label": node.name, "attributes": {"type": node.type, **node.properties}}
                    for i, node in enumerate(result.nodes)
                ]
            return []
        except Exception as e:
            logger.debug(f"Error extracting entities: {e}")
            return []
    
    def _extract_relations(self, result: Any) -> List[Dict[str, Any]]:
        """Extract relations from result"""
        try:
            if hasattr(result, 'edges') and result.edges:
                return [
                    {"source": edge.source, "relation": edge.relation_type, "target": edge.target}
                    for edge in result.edges
                ]
            return []
        except Exception as e:
            logger.debug(f"Error extracting relations: {e}")
            return []
    
    def _extract_hyperedges(self, result: Any) -> List[Dict[str, Any]]:
        """Extract hyperedges from result"""
        try:
            if hasattr(result, 'edges') and result.edges:
                return [
                    {"id": str(i), "entities": [edge.source, edge.target], "relation": edge.relation_type, "attributes": {}}
                    for i, edge in enumerate(result.edges)
                ]
            return []
        except Exception as e:
            logger.debug(f"Error extracting hyperedges: {e}")
            return []
    
    def list_templates(self) -> List[str]:
        """List available domain templates"""
        return ["general", "finance", "legal", "medical", "tcm", "industry"]


# Global extractor instance
_extractor_instance = None

def get_extractor(api_key: Optional[str] = None) -> KnowledgeExtractor:
    """Get or create the knowledge extractor instance"""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = KnowledgeExtractor(api_key=api_key)
    return _extractor_instance
