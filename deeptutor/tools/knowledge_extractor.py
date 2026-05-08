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
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from hyperextract import Extractor, Template
    from hyperextract.schemas import KnowledgeGraph, Hypergraph, TemporalGraph
    HYPEREXTRACT_AVAILABLE = True
except ImportError:
    HYPEREXTRACT_AVAILABLE = False
    logger.warning("Hyper-Extract not installed, knowledge extraction disabled")


class KnowledgeExtractor:
    """
    Knowledge extraction tool using Hyper-Extract
    
    Supports extraction of:
    - Knowledge Graphs (entity-relation-entity triples)
    - Hypergraphs (multi-entity complex relationships)
    - Spatio-temporal graphs (time and location aware)
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the knowledge extractor
        
        Args:
            api_key: Optional API key for LLM provider
        """
        self.api_key = api_key
        self.extractor = None
        if HYPEREXTRACT_AVAILABLE:
            try:
                self.extractor = Extractor(api_key=api_key)
                logger.info("Hyper-Extract extractor initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Hyper-Extract: {e}")
    
    def is_available(self) -> bool:
        """Check if Hyper-Extract is available"""
        return HYPEREXTRACT_AVAILABLE and self.extractor is not None
    
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
            return {"error": "Hyper-Extract not available"}
        
        try:
            template = self._load_template(template_name)
            result = self.extractor.extract(text, template=template)
            graph = result.to_graph()
            
            return {
                "success": True,
                "type": "knowledge_graph",
                "entities": [{"id": e.id, "label": e.label, "attributes": e.attributes} 
                            for e in graph.entities],
                "relations": [{"source": r.source, "relation": r.relation, "target": r.target}
                             for r in graph.relations],
                "summary": graph.summary
            }
        except Exception as e:
            logger.error(f"Knowledge graph extraction failed: {e}")
            return {"error": str(e)}
    
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
            return {"error": "Hyper-Extract not available"}
        
        try:
            template = self._load_template(template_name)
            result = self.extractor.extract(text, template=template)
            hypergraph = result.to_hypergraph()
            
            return {
                "success": True,
                "type": "hypergraph",
                "entities": [{"id": e.id, "label": e.label} for e in hypergraph.entities],
                "hyperedges": [{"id": h.id, "entities": h.entity_ids, "relation": h.relation, "attributes": h.attributes}
                              for h in hypergraph.hyperedges],
                "summary": hypergraph.summary
            }
        except Exception as e:
            logger.error(f"Hypergraph extraction failed: {e}")
            return {"error": str(e)}
    
    def extract_temporal(self, text: str, template_name: str = "general") -> Dict[str, Any]:
        """
        Extract temporal relationships from text
        
        Args:
            text: Input text to extract from
            template_name: Domain template name
        
        Returns:
            Dictionary containing temporal information
        """
        if not self.is_available():
            return {"error": "Hyper-Extract not available"}
        
        try:
            template = self._load_template(template_name)
            result = self.extractor.extract(text, template=template)
            temporal = result.to_temporal()
            
            return {
                "success": True,
                "type": "temporal",
                "events": [{"id": e.id, "timestamp": e.timestamp, "description": e.description, "entities": e.entity_ids}
                          for e in temporal.events],
                "time_intervals": [{"start": ti.start, "end": ti.end, "label": ti.label}
                                  for ti in temporal.time_intervals],
                "summary": temporal.summary
            }
        except Exception as e:
            logger.error(f"Temporal extraction failed: {e}")
            return {"error": str(e)}
    
    def extract_spatial(self, text: str, template_name: str = "general") -> Dict[str, Any]:
        """
        Extract spatial relationships from text
        
        Args:
            text: Input text to extract from
            template_name: Domain template name
        
        Returns:
            Dictionary containing spatial information
        """
        if not self.is_available():
            return {"error": "Hyper-Extract not available"}
        
        try:
            template = self._load_template(template_name)
            result = self.extractor.extract(text, template=template)
            spatial = result.to_spatial()
            
            return {
                "success": True,
                "type": "spatial",
                "locations": [{"id": l.id, "name": l.name, "coordinates": l.coordinates, "type": l.type}
                             for l in spatial.locations],
                "spatial_relations": [{"source": sr.source, "relation": sr.relation, "target": sr.target}
                                      for sr in spatial.spatial_relations],
                "summary": spatial.summary
            }
        except Exception as e:
            logger.error(f"Spatial extraction failed: {e}")
            return {"error": str(e)}
    
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
            return {"error": "Hyper-Extract not available"}
        
        try:
            template = self._load_template(template_name)
            result = self.extractor.extract(text, template=template)
            
            return {
                "success": True,
                "knowledge_graph": self._graph_to_dict(result.to_graph()),
                "hypergraph": self._hypergraph_to_dict(result.to_hypergraph()),
                "temporal": self._temporal_to_dict(result.to_temporal()),
                "spatial": self._spatial_to_dict(result.to_spatial()),
                "summary": result.summary
            }
        except Exception as e:
            logger.error(f"Full extraction failed: {e}")
            return {"error": str(e)}
    
    def _load_template(self, template_name: str) -> Any:
        """Load a template by name"""
        try:
            return Template.load(template_name)
        except Exception:
            # Fallback to general template
            logger.warning(f"Template {template_name} not found, using general template")
            return Template.load("general")
    
    def _graph_to_dict(self, graph: Any) -> Dict[str, Any]:
        """Convert KnowledgeGraph to dict"""
        return {
            "entities": [{"id": e.id, "label": e.label, "attributes": dict(e.attributes)} 
                        for e in graph.entities],
            "relations": [{"source": r.source, "relation": r.relation, "target": r.target}
                         for r in graph.relations]
        }
    
    def _hypergraph_to_dict(self, hypergraph: Any) -> Dict[str, Any]:
        """Convert Hypergraph to dict"""
        return {
            "entities": [{"id": e.id, "label": e.label} for e in hypergraph.entities],
            "hyperedges": [{"id": h.id, "entities": h.entity_ids, "relation": h.relation, 
                           "attributes": dict(h.attributes)} for h in hypergraph.hyperedges]
        }
    
    def _temporal_to_dict(self, temporal: Any) -> Dict[str, Any]:
        """Convert TemporalGraph to dict"""
        return {
            "events": [{"id": e.id, "timestamp": str(e.timestamp), "description": e.description, 
                       "entities": e.entity_ids} for e in temporal.events],
            "time_intervals": [{"start": str(ti.start), "end": str(ti.end), "label": ti.label}
                              for ti in temporal.time_intervals]
        }
    
    def _spatial_to_dict(self, spatial: Any) -> Dict[str, Any]:
        """Convert spatial result to dict"""
        return {
            "locations": [{"id": l.id, "name": l.name, "coordinates": l.coordinates, "type": l.type}
                         for l in spatial.locations],
            "spatial_relations": [{"source": sr.source, "relation": sr.relation, "target": sr.target}
                                  for sr in spatial.spatial_relations]
        }
    
    def list_templates(self) -> List[str]:
        """List available domain templates"""
        if not HYPEREXTRACT_AVAILABLE:
            return []
        
        try:
            return Template.list_available()
        except Exception as e:
            logger.error(f"Failed to list templates: {e}")
            return ["general"]


# Global extractor instance
_extractor_instance = None

def get_extractor(api_key: Optional[str] = None) -> KnowledgeExtractor:
    """Get or create the knowledge extractor instance"""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = KnowledgeExtractor(api_key=api_key)
    return _extractor_instance
