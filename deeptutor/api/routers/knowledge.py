"""
Knowledge Extraction API Router

Provides REST endpoints for Hyper-Extract knowledge extraction capabilities.

Endpoints:
- POST /api/knowledge/extract - Extract knowledge from text
- POST /api/knowledge/graph - Extract knowledge graph
- POST /api/knowledge/hypergraph - Extract hypergraph
- POST /api/knowledge/temporal - Extract temporal relationships
- POST /api/knowledge/spatial - Extract spatial relationships
- GET /api/knowledge/templates - List available templates
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from deeptutor.tools.knowledge_extractor import get_extractor

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


class ExtractRequest(BaseModel):
    """Request model for knowledge extraction"""
    text: str = Field(..., description="Text to extract knowledge from")
    template: Optional[str] = Field("general", description="Domain template name")
    output_type: Optional[str] = Field("all", description="Output type: graph, hypergraph, temporal, spatial, or all")


class ExtractResponse(BaseModel):
    """Response model for knowledge extraction"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    summary: Optional[str] = None


@router.post("/extract", response_model=ExtractResponse)
async def extract_knowledge(request: ExtractRequest):
    """
    Extract knowledge from text
    
    Supports multiple output types:
    - graph: Knowledge graph (entity-relation-entity triples)
    - hypergraph: Multi-entity complex relationships
    - temporal: Time-aware relationships
    - spatial: Location-aware relationships
    - all: All extraction types
    """
    extractor = get_extractor()
    
    if not extractor.is_available():
        raise HTTPException(status_code=503, detail="Knowledge extraction service not available")
    
    output_type = request.output_type.lower()
    
    if output_type == "graph":
        result = extractor.extract_knowledge_graph(request.text, request.template)
    elif output_type == "hypergraph":
        result = extractor.extract_hypergraph(request.text, request.template)
    elif output_type == "temporal":
        result = extractor.extract_temporal(request.text, request.template)
    elif output_type == "spatial":
        result = extractor.extract_spatial(request.text, request.template)
    elif output_type == "all":
        result = extractor.extract_all(request.text, request.template)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown output_type: {output_type}")
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return ExtractResponse(
        success=result.get("success", False),
        data=result,
        summary=result.get("summary")
    )


@router.post("/graph", response_model=ExtractResponse)
async def extract_graph(request: ExtractRequest):
    """
    Extract knowledge graph from text
    
    Returns entities and their relationships as triples (subject-relation-object).
    """
    extractor = get_extractor()
    
    if not extractor.is_available():
        raise HTTPException(status_code=503, detail="Knowledge extraction service not available")
    
    result = extractor.extract_knowledge_graph(request.text, request.template)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return ExtractResponse(
        success=result.get("success", False),
        data=result,
        summary=result.get("summary")
    )


@router.post("/hypergraph", response_model=ExtractResponse)
async def extract_hypergraph(request: ExtractRequest):
    """
    Extract hypergraph from text
    
    Returns multi-entity relationships (hyperedges) that involve more than two entities.
    This is Hyper-Extract's specialty feature.
    """
    extractor = get_extractor()
    
    if not extractor.is_available():
        raise HTTPException(status_code=503, detail="Knowledge extraction service not available")
    
    result = extractor.extract_hypergraph(request.text, request.template)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return ExtractResponse(
        success=result.get("success", False),
        data=result,
        summary=result.get("summary")
    )


@router.post("/temporal", response_model=ExtractResponse)
async def extract_temporal(request: ExtractRequest):
    """
    Extract temporal relationships from text
    
    Returns events with timestamps and time intervals.
    """
    extractor = get_extractor()
    
    if not extractor.is_available():
        raise HTTPException(status_code=503, detail="Knowledge extraction service not available")
    
    result = extractor.extract_temporal(request.text, request.template)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return ExtractResponse(
        success=result.get("success", False),
        data=result,
        summary=result.get("summary")
    )


@router.post("/spatial", response_model=ExtractResponse)
async def extract_spatial(request: ExtractRequest):
    """
    Extract spatial relationships from text
    
    Returns locations and their spatial relationships.
    """
    extractor = get_extractor()
    
    if not extractor.is_available():
        raise HTTPException(status_code=503, detail="Knowledge extraction service not available")
    
    result = extractor.extract_spatial(request.text, request.template)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return ExtractResponse(
        success=result.get("success", False),
        data=result,
        summary=result.get("summary")
    )


@router.get("/templates", response_model=List[str])
async def list_templates():
    """
    List available domain templates
    
    Returns a list of template names that can be used for extraction.
    Common templates: general, finance, legal, medical, tcm, industry
    """
    extractor = get_extractor()
    return extractor.list_templates()


@router.get("/health")
async def health_check():
    """
    Health check endpoint for knowledge extraction service
    """
    extractor = get_extractor()
    return {
        "status": "available" if extractor.is_available() else "unavailable",
        "service": "hyper-extract"
    }
