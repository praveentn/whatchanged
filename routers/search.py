# routers/search.py - Updated to use the fixed search service

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from dependencies import get_analysis_service, get_document_service, get_embedding_service
from services.analysis_service import AnalysisService
from services.document_service import DocumentService
from services.embedding_service import EmbeddingService
from services.search_service import SearchService
from database import get_db
from sqlalchemy.orm import Session

router = APIRouter()

# Pydantic models for request/response (keep existing models)
class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    document_ids: Optional[List[int]] = Field(None, description="Specific document IDs to search")
    document_slug: Optional[str] = Field(None, description="Search within specific document slug")
    intent_filter: Optional[str] = Field(None, description="Filter by intent label")
    domain_filter: Optional[str] = Field(None, description="Filter by document domain")
    search_type: str = Field("semantic", description="Search type: semantic, keyword, or hybrid")
    top_k: int = Field(10, ge=1, le=50, description="Number of results to return")
    similarity_threshold: float = Field(0.5, ge=0.0, le=1.0, description="Minimum similarity score")

class SearchResult(BaseModel):
    """Individual search result"""
    chunk_id: int
    document_id: int
    document_title: str
    document_version: int
    chunk_index: int
    similarity_score: float
    text_preview: str
    full_text: Optional[str] = None
    intent_label: Optional[str] = None
    heading: Optional[str] = None
    subheading: Optional[str] = None
    summary: Optional[str] = None

class SearchResponse(BaseModel):
    """Search response model"""
    query: str
    search_type: str
    total_results: int
    processing_time_ms: float
    results: List[SearchResult]
    suggestions: Optional[List[str]] = None

class GlobalSearchRequest(BaseModel):
    """Global search across all documents"""
    query: str = Field(..., min_length=1, max_length=500)
    search_scope: str = Field("all", description="Search scope: all, titles, content, summaries")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")
    top_k: int = Field(20, ge=1, le=100, description="Number of results to return")

@router.post("/semantic", response_model=SearchResponse)
async def semantic_search(
    request: SearchRequest,
    db: Session = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    """
    Perform semantic search using embeddings and keyword matching
    
    Args:
        request (SearchRequest): Search parameters
        
    Returns:
        SearchResponse: Search results with similarity scores
    """
    try:
        # Create search service instance
        search_service = SearchService(db, embedding_service)
        
        # Perform search
        result = await search_service.semantic_search(
            query=request.query,
            document_slug=request.document_slug,
            intent_filter=request.intent_filter,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold
        )
        
        # Handle errors
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Format results as SearchResult objects
        search_results = []
        for res in result["results"]:
            search_result = SearchResult(
                chunk_id=res["chunk_id"],
                document_id=res["document_id"],
                document_title=res["document_title"],
                document_version=res["document_version"],
                chunk_index=res["chunk_index"],
                similarity_score=res["similarity_score"],
                text_preview=res["text_preview"],
                full_text=res.get("full_text"),
                intent_label=res.get("intent_label"),
                heading=res.get("heading"),
                subheading=res.get("subheading"),
                summary=res.get("summary")
            )
            search_results.append(search_result)
        
        return SearchResponse(
            query=result["query"],
            search_type=result["search_type"],
            total_results=result["total_results"],
            processing_time_ms=result["processing_time_ms"],
            results=search_results,
            suggestions=result.get("suggestions")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/global", response_model=SearchResponse)
async def global_search(
    request: GlobalSearchRequest,
    db: Session = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    """
    Perform global search across all documents
    
    Args:
        request (GlobalSearchRequest): Global search parameters
        
    Returns:
        SearchResponse: Global search results
    """
    try:
        # Create search service instance
        search_service = SearchService(db, embedding_service)
        
        # Perform global search
        result = await search_service.global_search(
            query=request.query,
            search_scope=request.search_scope,
            filters=request.filters,
            top_k=request.top_k
        )
        
        # Handle errors
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Format results as SearchResult objects
        search_results = []
        for res in result["results"]:
            search_result = SearchResult(
                chunk_id=res["chunk_id"],
                document_id=res["document_id"],
                document_title=res["document_title"],
                document_version=res["document_version"],
                chunk_index=res["chunk_index"],
                similarity_score=res["similarity_score"],
                text_preview=res["text_preview"],
                full_text=res.get("full_text"),
                intent_label=res.get("intent_label"),
                heading=res.get("heading"),
                subheading=res.get("subheading"),
                summary=res.get("summary")
            )
            search_results.append(search_result)
        
        return SearchResponse(
            query=result["query"],
            search_type=result["search_type"],
            total_results=result["total_results"],
            processing_time_ms=result["processing_time_ms"],
            results=search_results,
            suggestions=result.get("suggestions")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Global search failed: {str(e)}")

@router.get("/suggestions")
async def get_search_suggestions(
    query: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Get search suggestions based on existing content
    
    Args:
        query (str): Partial query for suggestions
        limit (int): Number of suggestions to return
        
    Returns:
        Dict[str, Any]: Search suggestions
    """
    try:
        from database import Chunk
        from sqlalchemy import func, or_
        
        # Get suggestions from chunk content and summaries
        query_pattern = f"%{query.lower()}%"
        
        # Search in summaries and headings
        chunks = db.query(Chunk).filter(
            or_(
                func.lower(Chunk.summary).like(query_pattern),
                func.lower(Chunk.heading).like(query_pattern),
                func.lower(Chunk.text).like(query_pattern)
            )
        ).limit(limit * 2).all()  # Get more than needed for filtering
        
        suggestions = set()
        
        # Extract relevant terms from found chunks
        for chunk in chunks:
            # Add headings
            if chunk.heading and query.lower() in chunk.heading.lower():
                suggestions.add(chunk.heading)
            
            # Add intent labels
            if chunk.intent_label:
                suggestions.add(chunk.intent_label)
            
            # Add words from summaries
            if chunk.summary:
                words = chunk.summary.split()
                for word in words:
                    if len(word) > 3 and query.lower() in word.lower():
                        suggestions.add(word.strip('.,!?'))
        
        # Convert to list and limit
        suggestion_list = list(suggestions)[:limit]
        
        return {
            "query": query,
            "suggestions": suggestion_list,
            "count": len(suggestion_list)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")

@router.get("/stats")
async def get_search_stats(
    db: Session = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    """
    Get search statistics and indexing status
    
    Returns:
        Dict[str, Any]: Search statistics
    """
    try:
        # Create search service instance
        search_service = SearchService(db, embedding_service)
        
        # Get search statistics
        stats = await search_service.get_search_stats()
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get search stats: {str(e)}")

if __name__ == "__main__":
    # Test the router
    print("🧪 Search router loaded successfully!")
    print("📋 Available endpoints:")
    for route in router.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = list(route.methods)
            print(f"  {methods} {route.path}")