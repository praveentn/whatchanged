# routers/comparison.py
"""
DocuReview Pro - Comparison API Router
REST API endpoints for document version comparison
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from dependencies import get_comparison_service, get_document_service
from services.comparison_service import ComparisonService, ComparisonConfig
from services.document_service import DocumentService

router = APIRouter()

# Pydantic models for request/response
class ComparisonRequest(BaseModel):
    """Document comparison request"""
    document_a_id: int = Field(..., description="First document ID")
    document_b_id: int = Field(..., description="Second document ID")
    granularity: str = Field("word", description="Comparison granularity")
    algorithm: str = Field("hybrid", description="Comparison algorithm")
    similarity_threshold: float = Field(0.8, ge=0.0, le=1.0, description="Similarity threshold")
    show_only_changes: bool = Field(False, description="Show only changes")
    color_scheme: str = Field("default", description="Color scheme for highlighting")

class ComparisonBySlugRequest(BaseModel):
    """Document comparison by slug and versions"""
    document_slug: str = Field(..., description="Document slug")
    version_a: int = Field(..., description="First version number")
    version_b: int = Field(..., description="Second version number")
    granularity: str = Field("word", description="Comparison granularity")
    algorithm: str = Field("hybrid", description="Comparison algorithm")
    similarity_threshold: float = Field(0.8, ge=0.0, le=1.0, description="Similarity threshold")
    show_only_changes: bool = Field(False, description="Show only changes")
    color_scheme: str = Field("default", description="Color scheme for highlighting")

class ComparisonResponse(BaseModel):
    """Comparison response"""
    comparison_id: Optional[str] = None
    document_info: Dict[str, Any]
    text_diff: Dict[str, Any]
    structure_diff: Dict[str, Any]
    semantic_diff: Optional[Dict[str, Any]] = None
    intent_diff: Dict[str, Any]
    metrics: Dict[str, float]
    ai_summary: Optional[Dict[str, Any]] = None
    processing_time_ms: float
    cached: bool = False

class DiffConfigurationRequest(BaseModel):
    """Diff configuration request"""
    name: str = Field(..., max_length=255)
    granularity: str = Field("word")
    algorithm: str = Field("hybrid")
    color_scheme: str = Field("default")
    similarity_threshold: float = Field(0.8, ge=0.0, le=1.0)
    show_only_changes: bool = Field(False)
    is_default: bool = Field(False)

@router.post("/compare", response_model=ComparisonResponse)
async def compare_documents(
    request: ComparisonRequest,
    background_tasks: BackgroundTasks,
    comparison_service: ComparisonService = Depends(get_comparison_service),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Compare two documents by their IDs
    
    Args:
        request (ComparisonRequest): Comparison parameters
        
    Returns:
        ComparisonResponse: Comprehensive comparison results
    
    Example:
        POST /api/comparison/compare
        {
            "document_a_id": 123,
            "document_b_id": 124,
            "granularity": "word",
            "algorithm": "hybrid"
        }
    """
    try:
        # Validate documents exist
        doc_a = document_service.get_document(request.document_a_id)
        doc_b = document_service.get_document(request.document_b_id)
        
        if not doc_a:
            raise HTTPException(status_code=404, detail=f"Document {request.document_a_id} not found")
        if not doc_b:
            raise HTTPException(status_code=404, detail=f"Document {request.document_b_id} not found")
        
        # Validate comparison configuration
        _validate_comparison_config(request.granularity, request.algorithm, request.color_scheme)
        
        # Create comparison config
        config = ComparisonConfig(
            granularity=request.granularity,
            algorithm=request.algorithm,
            similarity_threshold=request.similarity_threshold,
            show_only_changes=request.show_only_changes,
            color_scheme=request.color_scheme
        )
        
        # Perform comparison
        result = await comparison_service.compare_documents(
            doc_id_a=request.document_a_id,
            doc_id_b=request.document_b_id,
            config=config
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Format response
        return ComparisonResponse(
            comparison_id=f"{doc_a.slug}_v{doc_a.version}_vs_v{doc_b.version}",
            document_info=result["document_info"],
            text_diff=result.get("text_diff", {}),
            structure_diff=result.get("structure_diff", {}),
            semantic_diff=result.get("semantic_diff"),
            intent_diff=result.get("intent_diff", {}),
            metrics=result.get("metrics", {}),
            ai_summary=result.get("ai_summary"),
            processing_time_ms=result.get("processing_time_ms", 0),
            cached=result.get("document_info", {}).get("cached", False)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")

@router.post("/compare-by-slug", response_model=ComparisonResponse)
async def compare_documents_by_slug(
    request: ComparisonBySlugRequest,
    comparison_service: ComparisonService = Depends(get_comparison_service),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Compare two document versions by slug and version numbers
    
    Args:
        request (ComparisonBySlugRequest): Comparison parameters with slug and versions
        
    Returns:
        ComparisonResponse: Comprehensive comparison results
    
    Example:
        POST /api/comparison/compare-by-slug
        {
            "document_slug": "api-documentation",
            "version_a": 1,
            "version_b": 2,
            "granularity": "sentence"
        }
    """
    try:
        # Get documents by slug and version
        doc_a = document_service.get_document_by_slug_version(request.document_slug, request.version_a)
        doc_b = document_service.get_document_by_slug_version(request.document_slug, request.version_b)
        
        if not doc_a:
            raise HTTPException(
                status_code=404, 
                detail=f"Document '{request.document_slug}' version {request.version_a} not found"
            )
        if not doc_b:
            raise HTTPException(
                status_code=404,
                detail=f"Document '{request.document_slug}' version {request.version_b} not found"
            )
        
        # Validate comparison configuration
        _validate_comparison_config(request.granularity, request.algorithm, request.color_scheme)
        
        # Create comparison config
        config = ComparisonConfig(
            granularity=request.granularity,
            algorithm=request.algorithm,
            similarity_threshold=request.similarity_threshold,
            show_only_changes=request.show_only_changes,
            color_scheme=request.color_scheme
        )
        
        # Perform comparison
        result = await comparison_service.compare_documents(
            doc_id_a=doc_a.id,
            doc_id_b=doc_b.id,
            config=config
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Format response
        return ComparisonResponse(
            comparison_id=f"{request.document_slug}_v{request.version_a}_vs_v{request.version_b}",
            document_info=result["document_info"],
            text_diff=result.get("text_diff", {}),
            structure_diff=result.get("structure_diff", {}),
            semantic_diff=result.get("semantic_diff"),
            intent_diff=result.get("intent_diff", {}),
            metrics=result.get("metrics", {}),
            ai_summary=result.get("ai_summary"),
            processing_time_ms=result.get("processing_time_ms", 0),
            cached=result.get("document_info", {}).get("cached", False)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")

@router.get("/history/{document_slug}")
async def get_comparison_history(
    document_slug: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    comparison_service: ComparisonService = Depends(get_comparison_service)
):
    """
    Get comparison history for a document
    
    Args:
        document_slug (str): Document slug
        limit (int): Maximum number of results
        offset (int): Number of results to skip
        
    Returns:
        Dict[str, Any]: Comparison history
    
    Example:
        GET /api/comparison/history/api-documentation?limit=10
    """
    try:
        from database import Comparison
        
        # Get comparisons for this document
        comparisons = comparison_service.db.query(Comparison).filter(
            Comparison.doc_slug == document_slug
        ).order_by(Comparison.created_at.desc()).offset(offset).limit(limit).all()
        
        # Get total count
        total = comparison_service.db.query(Comparison).filter(
            Comparison.doc_slug == document_slug
        ).count()
        
        # Format results
        comparison_list = []
        for comp in comparisons:
            comparison_data = {
                "id": comp.id,
                "version_a": comp.version_a,
                "version_b": comp.version_b,
                "created_at": comp.created_at.isoformat(),
                "similarity_score": comp.similarity_score,
                "change_score": comp.change_score,
                "processing_time_ms": comp.processing_time_ms
            }
            comparison_list.append(comparison_data)
        
        return {
            "document_slug": document_slug,
            "comparisons": comparison_list,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_next": offset + limit < total,
            "has_prev": offset > 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")

@router.get("/configurations")
async def get_diff_configurations(
    comparison_service: ComparisonService = Depends(get_comparison_service)
):
    """
    Get available diff configurations
    
    Returns:
        Dict[str, Any]: Available diff configurations
    
    Example:
        GET /api/comparison/configurations
    """
    try:
        from database import DiffConfiguration
        
        configs = comparison_service.db.query(DiffConfiguration).all()
        
        config_list = []
        for config in configs:
            config_data = {
                "id": config.id,
                "name": config.name,
                "granularity": config.granularity,
                "algorithm": config.algorithm,
                "color_scheme": config.color_scheme,
                "similarity_threshold": config.similarity_threshold,
                "show_only_changes": config.show_only_changes == 'true',
                "is_default": config.is_default == 'true',
                "created_at": config.created_at.isoformat()
            }
            config_list.append(config_data)
        
        return {
            "configurations": config_list,
            "total": len(config_list)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get configurations: {str(e)}")

@router.post("/configurations")
async def create_diff_configuration(
    request: DiffConfigurationRequest,
    comparison_service: ComparisonService = Depends(get_comparison_service)
):
    """
    Create a new diff configuration
    
    Args:
        request (DiffConfigurationRequest): Configuration parameters
        
    Returns:
        Dict[str, Any]: Created configuration
    
    Example:
        POST /api/comparison/configurations
        {
            "name": "Detailed Word Diff",
            "granularity": "word",
            "algorithm": "semantic",
            "similarity_threshold": 0.85
        }
    """
    try:
        from database import DiffConfiguration
        
        # Validate configuration
        _validate_comparison_config(request.granularity, request.algorithm, request.color_scheme)
        
        # If setting as default, unset other defaults
        if request.is_default:
            comparison_service.db.query(DiffConfiguration).update(
                {"is_default": "false"}
            )
        
        # Create configuration
        config = DiffConfiguration(
            name=request.name,
            granularity=request.granularity,
            algorithm=request.algorithm,
            color_scheme=request.color_scheme,
            similarity_threshold=request.similarity_threshold,
            show_only_changes="true" if request.show_only_changes else "false",
            is_default="true" if request.is_default else "false"
        )
        
        comparison_service.db.add(config)
        comparison_service.db.commit()
        
        return {
            "success": True,
            "configuration": {
                "id": config.id,
                "name": config.name,
                "granularity": config.granularity,
                "algorithm": config.algorithm,
                "color_scheme": config.color_scheme,
                "similarity_threshold": config.similarity_threshold,
                "show_only_changes": request.show_only_changes,
                "is_default": request.is_default
            },
            "message": "Configuration created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        comparison_service.db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create configuration: {str(e)}")

@router.get("/algorithms")
async def get_available_algorithms():
    """
    Get available comparison algorithms and granularities
    
    Returns:
        Dict[str, Any]: Available options
    
    Example:
        GET /api/comparison/algorithms
    """
    return {
        "granularities": [
            {"value": "character", "label": "Character Level", "description": "Compare at character level"},
            {"value": "word", "label": "Word Level", "description": "Compare at word level (recommended)"},
            {"value": "sentence", "label": "Sentence Level", "description": "Compare at sentence level"},
            {"value": "paragraph", "label": "Paragraph Level", "description": "Compare at paragraph level"}
        ],
        "algorithms": [
            {"value": "syntactic", "label": "Syntactic", "description": "Text-based comparison only"},
            {"value": "semantic", "label": "Semantic", "description": "Meaning-based comparison using AI"},
            {"value": "hybrid", "label": "Hybrid", "description": "Combined syntactic and semantic (recommended)"}
        ],
        "color_schemes": [
            {"value": "default", "label": "Default", "description": "Standard red/green highlighting"},
            {"value": "colorblind", "label": "Colorblind Friendly", "description": "Blue/orange highlighting"},
            {"value": "high_contrast", "label": "High Contrast", "description": "Black/white highlighting"},
            {"value": "subtle", "label": "Subtle", "description": "Light highlighting"}
        ]
    }

@router.get("/metrics/{document_slug}")
async def get_document_comparison_metrics(
    document_slug: str,
    comparison_service: ComparisonService = Depends(get_comparison_service)
):
    """
    Get aggregated comparison metrics for a document
    
    Args:
        document_slug (str): Document slug
        
    Returns:
        Dict[str, Any]: Aggregated metrics
    
    Example:
        GET /api/comparison/metrics/api-documentation
    """
    try:
        from database import Comparison
        from sqlalchemy import func
        
        # Get all comparisons for this document
        comparisons = comparison_service.db.query(Comparison).filter(
            Comparison.doc_slug == document_slug
        ).all()
        
        if not comparisons:
            return {
                "document_slug": document_slug,
                "total_comparisons": 0,
                "metrics": {}
            }
        
        # Calculate aggregate metrics
        similarity_scores = [c.similarity_score for c in comparisons if c.similarity_score is not None]
        change_scores = [c.change_score for c in comparisons if c.change_score is not None]
        processing_times = [c.processing_time_ms for c in comparisons if c.processing_time_ms is not None]
        
        # Get version evolution (similarity between consecutive versions)
        version_evolution = []
        for comp in sorted(comparisons, key=lambda x: (x.version_a, x.version_b)):
            if comp.version_b == comp.version_a + 1:  # Consecutive versions
                version_evolution.append({
                    "from_version": comp.version_a,
                    "to_version": comp.version_b,
                    "similarity": comp.similarity_score,
                    "change_intensity": comp.change_score
                })
        
        metrics = {
            "avg_similarity": round(sum(similarity_scores) / len(similarity_scores), 3) if similarity_scores else 0,
            "min_similarity": round(min(similarity_scores), 3) if similarity_scores else 0,
            "max_similarity": round(max(similarity_scores), 3) if similarity_scores else 0,
            "avg_change_score": round(sum(change_scores) / len(change_scores), 3) if change_scores else 0,
            "avg_processing_time_ms": round(sum(processing_times) / len(processing_times), 1) if processing_times else 0,
            "version_evolution": version_evolution
        }
        
        return {
            "document_slug": document_slug,
            "total_comparisons": len(comparisons),
            "metrics": metrics,
            "version_count": len(set([c.version_a for c in comparisons] + [c.version_b for c in comparisons]))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

# Helper functions
def _validate_comparison_config(granularity: str, algorithm: str, color_scheme: str):
    """Validate comparison configuration parameters"""
    valid_granularities = ["character", "word", "sentence", "paragraph"]
    valid_algorithms = ["syntactic", "semantic", "hybrid"]
    valid_color_schemes = ["default", "colorblind", "high_contrast", "subtle"]
    
    if granularity not in valid_granularities:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid granularity. Must be one of: {', '.join(valid_granularities)}"
        )
    
    if algorithm not in valid_algorithms:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid algorithm. Must be one of: {', '.join(valid_algorithms)}"
        )
    
    if color_scheme not in valid_color_schemes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid color scheme. Must be one of: {', '.join(valid_color_schemes)}"
        )

if __name__ == "__main__":
    # Test the router
    print("🧪 Comparison router loaded successfully!")
    print("📋 Available endpoints:")
    for route in router.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = list(route.methods)
            print(f"  {methods} {route.path}")