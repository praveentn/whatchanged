# routers/search.py
"""
DocuReview Pro - Search API Router
Semantic and keyword search across documents and chunks
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from dependencies import get_analysis_service, get_document_service, get_embedding_service
from services.analysis_service import AnalysisService
from services.document_service import DocumentService
from services.embedding_service import EmbeddingService

router = APIRouter()

# Pydantic models for request/response
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
    analysis_service: AnalysisService = Depends(get_analysis_service),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Perform semantic search using embeddings
    
    Args:
        request (SearchRequest): Search parameters
        
    Returns:
        SearchResponse: Search results with similarity scores
    
    Example:
        POST /api/search/semantic
        {
            "query": "user authentication requirements",
            "document_slug": "api-docs",
            "top_k": 10,
            "similarity_threshold": 0.7
        }
    """
    try:
        import time
        start_time = time.time()
        
        results = []
        
        # Determine which documents to search
        if request.document_slug:
            # Search within specific document slug (latest version)
            latest_doc = document_service.get_latest_document_version(request.document_slug)
            if not latest_doc:
                raise HTTPException(status_code=404, detail="Document not found")
            
            search_results = analysis_service.search_document_chunks(
                document_id=latest_doc.id,
                query=request.query,
                intent_filter=request.intent_filter,
                top_k=request.top_k
            )
            
            # Format results
            for result in search_results:
                if result["similarity_score"] >= request.similarity_threshold:
                    search_result = SearchResult(
                        chunk_id=result["chunk_id"],
                        document_id=latest_doc.id,
                        document_title=latest_doc.title,
                        document_version=latest_doc.version,
                        chunk_index=result["chunk_index"],
                        similarity_score=round(result["similarity_score"], 3),
                        text_preview=result["text"][:200] + "..." if len(result["text"]) > 200 else result["text"],
                        full_text=result["text"],
                        intent_label=result.get("intent_label"),
                        heading=result.get("heading"),
                        subheading=result.get("subheading"),
                        summary=result.get("summary")
                    )
                    results.append(search_result)
        
        elif request.document_ids:
            # Search within specific documents
            for doc_id in request.document_ids:
                document = document_service.get_document(doc_id)
                if document:
                    search_results = analysis_service.search_document_chunks(
                        document_id=doc_id,
                        query=request.query,
                        intent_filter=request.intent_filter,
                        top_k=request.top_k
                    )
                    
                    for result in search_results:
                        if result["similarity_score"] >= request.similarity_threshold:
                            search_result = SearchResult(
                                chunk_id=result["chunk_id"],
                                document_id=doc_id,
                                document_title=document.title,
                                document_version=document.version,
                                chunk_index=result["chunk_index"],
                                similarity_score=round(result["similarity_score"], 3),
                                text_preview=result["text"][:200] + "..." if len(result["text"]) > 200 else result["text"],
                                full_text=result["text"],
                                intent_label=result.get("intent_label"),
                                heading=result.get("heading"),
                                subheading=result.get("subheading"),
                                summary=result.get("summary")
                            )
                            results.append(search_result)
        
        else:
            # Global search across all documents
            all_results = await _global_semantic_search(
                query=request.query,
                intent_filter=request.intent_filter,
                domain_filter=request.domain_filter,
                top_k=request.top_k,
                similarity_threshold=request.similarity_threshold,
                analysis_service=analysis_service,
                document_service=document_service
            )
            results.extend(all_results)
        
        # Sort by similarity score
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        # Limit results
        results = results[:request.top_k]
        
        processing_time = (time.time() - start_time) * 1000
        
        return SearchResponse(
            query=request.query,
            search_type="semantic",
            total_results=len(results),
            processing_time_ms=round(processing_time, 2),
            results=results,
            suggestions=_generate_search_suggestions(request.query) if len(results) < 3 else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/global", response_model=SearchResponse)
async def global_search(
    request: GlobalSearchRequest,
    analysis_service: AnalysisService = Depends(get_analysis_service),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Perform global search across all documents
    
    Args:
        request (GlobalSearchRequest): Global search parameters
        
    Returns:
        SearchResponse: Global search results
    
    Example:
        POST /api/search/global
        {
            "query": "security requirements",
            "search_scope": "all",
            "filters": {"domain": "technical"},
            "top_k": 25
        }
    """
    try:
        import time
        start_time = time.time()
        
        results = []
        
        if request.search_scope == "titles":
            # Search document titles only
            doc_results = document_service.list_documents(
                limit=100,
                search=request.query
            )
            
            for doc_data in doc_results["documents"]:
                # Create pseudo search result for title match
                search_result = SearchResult(
                    chunk_id=0,  # No specific chunk
                    document_id=doc_data["id"],
                    document_title=doc_data["title"],
                    document_version=doc_data["version"],
                    chunk_index=0,
                    similarity_score=0.9,  # High score for title match
                    text_preview=f"Document title: {doc_data['title']}",
                    intent_label="overview",
                    heading="Document Title",
                    summary=f"Matched document: {doc_data['title']}"
                )
                results.append(search_result)
        
        elif request.search_scope == "summaries":
            # Search chunk summaries
            results = await _search_chunk_summaries(
                query=request.query,
                filters=request.filters,
                top_k=request.top_k,
                analysis_service=analysis_service,
                document_service=document_service
            )
        
        else:
            # Full content search (default)
            results = await _global_semantic_search(
                query=request.query,
                intent_filter=request.filters.get("intent") if request.filters else None,
                domain_filter=request.filters.get("domain") if request.filters else None,
                top_k=request.top_k,
                similarity_threshold=0.3,  # Lower threshold for global search
                analysis_service=analysis_service,
                document_service=document_service
            )
        
        # Sort and limit results
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        results = results[:request.top_k]
        
        processing_time = (time.time() - start_time) * 1000
        
        return SearchResponse(
            query=request.query,
            search_type="global",
            total_results=len(results),
            processing_time_ms=round(processing_time, 2),
            results=results,
            suggestions=_generate_search_suggestions(request.query) if len(results) < 5 else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Global search failed: {str(e)}")

@router.get("/suggestions")
async def get_search_suggestions(
    query: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(5, ge=1, le=20),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Get search suggestions based on existing content
    
    Args:
        query (str): Partial query for suggestions
        limit (int): Number of suggestions to return
        
    Returns:
        Dict[str, Any]: Search suggestions
    
    Example:
        GET /api/search/suggestions?query=auth&limit=5
    """
    try:
        from database import Chunk
        from sqlalchemy import func, or_
        
        # Get suggestions from chunk content and summaries
        query_pattern = f"%{query.lower()}%"
        
        # Search in summaries and headings
        chunks = analysis_service.db.query(Chunk).filter(
            or_(
                func.lower(Chunk.summary).like(query_pattern),
                func.lower(Chunk.heading).like(query_pattern),
                func.lower(Chunk.intent_label).like(query_pattern)
            )
        ).limit(limit * 2).all()
        
        suggestions = set()
        
        # Extract suggestions from summaries
        for chunk in chunks:
            if chunk.summary and query.lower() in chunk.summary.lower():
                words = chunk.summary.split()
                for i, word in enumerate(words):
                    if query.lower() in word.lower():
                        # Get surrounding context
                        start = max(0, i - 2)
                        end = min(len(words), i + 3)
                        suggestion = " ".join(words[start:end])
                        suggestions.add(suggestion)
            
            if chunk.heading and query.lower() in chunk.heading.lower():
                suggestions.add(chunk.heading)
        
        # Add common search patterns
        common_patterns = [
            f"{query} requirements",
            f"{query} implementation",
            f"{query} documentation",
            f"{query} examples",
            f"{query} configuration"
        ]
        
        for pattern in common_patterns:
            if len(suggestions) < limit:
                suggestions.add(pattern)
        
        return {
            "query": query,
            "suggestions": list(suggestions)[:limit],
            "total": len(suggestions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")

@router.get("/stats")
async def get_search_statistics(
    analysis_service: AnalysisService = Depends(get_analysis_service),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Get search and indexing statistics
    
    Returns:
        Dict[str, Any]: Search statistics
    
    Example:
        GET /api/search/stats
    """
    try:
        from database import Chunk, VectorIndex, Document
        from sqlalchemy import func, distinct
        
        # Get basic statistics
        total_documents = analysis_service.db.query(Document).count()
        total_chunks = analysis_service.db.query(Chunk).count()
        analyzed_chunks = analysis_service.db.query(Chunk).filter(
            Chunk.intent_label.isnot(None)
        ).count()
        vector_indexes = analysis_service.db.query(VectorIndex).count()
        
        # Get intent distribution
        intent_stats = analysis_service.db.query(
            Chunk.intent_label,
            func.count(Chunk.id).label('count')
        ).filter(
            Chunk.intent_label.isnot(None)
        ).group_by(Chunk.intent_label).all()
        
        intent_distribution = {intent: count for intent, count in intent_stats}
        
        # Get domain distribution
        domain_stats = analysis_service.db.query(
            Document.domain,
            func.count(Document.id).label('count')
        ).filter(
            Document.domain.isnot(None),
            Document.domain != ""
        ).group_by(Document.domain).all()
        
        domain_distribution = {domain: count for domain, count in domain_stats}
        
        # Calculate search readiness
        searchable_documents = analysis_service.db.query(Document).filter(
            Document.status == "indexed"
        ).count()
        
        search_readiness = round(searchable_documents / max(total_documents, 1) * 100, 1)
        
        return {
            "indexing_stats": {
                "total_documents": total_documents,
                "total_chunks": total_chunks,
                "analyzed_chunks": analyzed_chunks,
                "vector_indexes": vector_indexes,
                "analysis_coverage": round(analyzed_chunks / max(total_chunks, 1) * 100, 1),
                "search_readiness": search_readiness
            },
            "content_distribution": {
                "intent_distribution": intent_distribution,
                "domain_distribution": domain_distribution,
                "unique_intents": len(intent_distribution),
                "unique_domains": len(domain_distribution)
            },
            "searchable_content": {
                "searchable_documents": searchable_documents,
                "indexed_chunks": analyzed_chunks,
                "avg_chunks_per_document": round(total_chunks / max(total_documents, 1), 1)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

# Helper functions
async def _global_semantic_search(
    query: str,
    intent_filter: Optional[str],
    domain_filter: Optional[str],
    top_k: int,
    similarity_threshold: float,
    analysis_service: AnalysisService,
    document_service: DocumentService
) -> List[SearchResult]:
    """Perform global semantic search across all documents"""
    results = []
    
    try:
        # Get all indexed documents
        doc_list = document_service.list_documents(limit=1000)  # Reasonable limit
        
        for doc_data in doc_list["documents"]:
            # Apply domain filter
            if domain_filter and doc_data.get("domain") != domain_filter:
                continue
            
            # Only search indexed documents
            if doc_data.get("status") != "indexed":
                continue
            
            try:
                search_results = analysis_service.search_document_chunks(
                    document_id=doc_data["id"],
                    query=query,
                    intent_filter=intent_filter,
                    top_k=min(top_k // 4, 10)  # Fewer results per document for global search
                )
                
                for result in search_results:
                    if result["similarity_score"] >= similarity_threshold:
                        search_result = SearchResult(
                            chunk_id=result["chunk_id"],
                            document_id=doc_data["id"],
                            document_title=doc_data["title"],
                            document_version=doc_data["version"],
                            chunk_index=result["chunk_index"],
                            similarity_score=round(result["similarity_score"], 3),
                            text_preview=result["text"][:200] + "..." if len(result["text"]) > 200 else result["text"],
                            full_text=result["text"],
                            intent_label=result.get("intent_label"),
                            heading=result.get("heading"),
                            subheading=result.get("subheading"),
                            summary=result.get("summary")
                        )
                        results.append(search_result)
                        
            except Exception as e:
                print(f"⚠️ Error searching document {doc_data['id']}: {e}")
                continue
        
        return results
        
    except Exception as e:
        print(f"❌ Error in global semantic search: {e}")
        return []

async def _search_chunk_summaries(
    query: str,
    filters: Optional[Dict[str, Any]],
    top_k: int,
    analysis_service: AnalysisService,
    document_service: DocumentService
) -> List[SearchResult]:
    """Search within chunk summaries"""
    from database import Chunk, Document
    from sqlalchemy import func, and_
    
    try:
        # Build query
        query_filters = [func.lower(Chunk.summary).like(f"%{query.lower()}%")]
        
        if filters:
            if filters.get("intent"):
                query_filters.append(Chunk.intent_label == filters["intent"])
            if filters.get("domain"):
                query_filters.append(Document.domain == filters["domain"])
        
        # Execute query
        chunks = analysis_service.db.query(Chunk).join(Document).filter(
            and_(*query_filters)
        ).limit(top_k).all()
        
        results = []
        for chunk in chunks:
            search_result = SearchResult(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                document_title=chunk.document.title,
                document_version=chunk.document.version,
                chunk_index=chunk.chunk_ix,
                similarity_score=0.8,  # Fixed score for keyword match
                text_preview=chunk.summary or chunk.text[:200] + "...",
                intent_label=chunk.intent_label,
                heading=chunk.heading,
                subheading=chunk.subheading,
                summary=chunk.summary
            )
            results.append(search_result)
        
        return results
        
    except Exception as e:
        print(f"❌ Error searching summaries: {e}")
        return []

def _generate_search_suggestions(query: str) -> List[str]:
    """Generate search suggestions for low-result queries"""
    # Simple suggestion generation
    suggestions = []
    
    # Add broader terms
    if len(query.split()) > 1:
        # Suggest individual words
        words = query.split()
        for word in words:
            if len(word) > 3:
                suggestions.append(word)
    
    # Add related terms
    related_terms = {
        "auth": ["authentication", "authorization", "security", "login"],
        "api": ["endpoint", "service", "interface", "rest"],
        "user": ["account", "profile", "customer", "client"],
        "data": ["information", "content", "storage", "database"],
        "config": ["configuration", "settings", "parameters", "options"]
    }
    
    for term, related in related_terms.items():
        if term in query.lower():
            suggestions.extend(related)
    
    return suggestions[:5]

if __name__ == "__main__":
    # Test the router
    print("🧪 Search router loaded successfully!")
    print("📋 Available endpoints:")
    for route in router.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = list(route.methods)
            print(f"  {methods} {route.path}")