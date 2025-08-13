# routers/documents.py
"""
DocuReview Pro - Documents API Router
REST API endpoints for document management and analysis
"""
import asyncio
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from dependencies import get_document_service, get_analysis_service
from services.document_service import DocumentService
from services.analysis_service import AnalysisService

router = APIRouter()

# Pydantic models for request/response
class DocumentCreate(BaseModel):
    """Document creation request"""
    title: str = Field(..., min_length=1, max_length=500)
    author: Optional[str] = Field(None, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)
    tags: Optional[List[str]] = Field(default_factory=list)
    notes: Optional[str] = Field(None, max_length=2000)

class DocumentResponse(BaseModel):
    """Document response model"""
    id: int
    slug: str
    title: str
    version: int
    created_at: str
    updated_at: str
    author: Optional[str]
    domain: Optional[str]
    tags: List[str]
    status: str
    bytes: int
    chunk_count: int
    has_analysis: bool

class DocumentDetail(DocumentResponse):
    """Detailed document response"""
    content: Optional[str] = None
    checksum: Optional[str] = None
    analysis_summary: Optional[Dict[str, Any]] = None

class DocumentListResponse(BaseModel):
    """Paginated document list response"""
    documents: List[DocumentResponse]
    total: int
    limit: int
    offset: int
    has_next: bool
    has_prev: bool

class AnalysisRequest(BaseModel):
    """Analysis request"""
    force_reanalysis: bool = Field(default=False)

class AnalysisResponse(BaseModel):
    """Analysis response"""
    document_id: int
    status: str
    message: Optional[str] = None
    chunks_processed: Optional[int] = None
    processing_time_seconds: Optional[float] = None

@router.post("/upload", response_model=Dict[str, Any])
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    author: str = Form(""),
    domain: str = Form(""),
    tags: str = Form(""),
    notes: str = Form(""),
    auto_analyze: bool = Form(True),
    document_service: DocumentService = Depends(get_document_service),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Upload a new document with automatic analysis
    
    Args:
        file (UploadFile): Document file to upload
        title (str): Document title
        author (str, optional): Document author
        domain (str, optional): Document domain/category
        tags (str, optional): Comma-separated tags
        notes (str, optional): Additional notes
        auto_analyze (bool): Whether to automatically analyze the document
        
    Returns:
        Dict[str, Any]: Upload result with document info
    
    Example:
        POST /api/documents/upload
        Form data: file=document.txt, title="API Docs", auto_analyze=true
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file type
        allowed_extensions = ['.txt', '.md']
        file_ext = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type not supported. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Read file content
        content = await file.read()
        try:
            content_str = content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                content_str = content.decode('latin-1')
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="Could not decode file as text")
        
        # Validate content
        if not content_str.strip():
            raise HTTPException(status_code=400, detail="File appears to be empty")
        
        if len(content_str) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        
        # Prepare metadata
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else []
        metadata = {
            "author": author,
            "domain": domain,
            "tags": tag_list,
            "notes": notes
        }
        
        # Create document
        document = document_service.create_document(
            title=title,
            content=content_str,
            filename=file.filename,
            metadata=metadata
        )
        
        # Schedule analysis if requested
        if auto_analyze:
            background_tasks.add_task(_analyze_document_background, analysis_service, document.id)
        
        return {
            "success": True,
            "document": {
                "id": document.id,
                "slug": document.slug,
                "title": document.title,
                "version": document.version,
                "status": document.status,
                "bytes": document.bytes,
                "analysis_scheduled": auto_analyze
            },
            "message": f"Document uploaded successfully. {'Analysis started.' if auto_analyze else ''}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None, max_length=255),
    domain: Optional[str] = Query(None, max_length=255),
    status: Optional[str] = Query(None),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    List documents with pagination and filtering
    
    Args:
        limit (int): Maximum number of results (1-100)
        offset (int): Number of results to skip
        search (str, optional): Search term for title
        domain (str, optional): Filter by domain
        status (str, optional): Filter by status
        
    Returns:
        DocumentListResponse: Paginated list of documents
    
    Example:
        GET /api/documents/?limit=20&search=API&domain=technical
    """
    try:
        result = document_service.list_documents(
            limit=limit,
            offset=offset,
            search=search,
            domain=domain
        )
        
        # Apply status filter if provided
        documents = result["documents"]
        if status:
            documents = [doc for doc in documents if doc["status"] == status]
        
        # Convert to response format
        document_responses = []
        for doc in documents:
            doc_response = DocumentResponse(
                id=doc["id"],
                slug=doc["slug"],
                title=doc["title"],
                version=doc["version"],
                created_at=doc["created_at"].isoformat(),
                updated_at=doc["updated_at"].isoformat(),
                author=doc["author"],
                domain=doc["domain"],
                tags=doc["tags"],
                status=doc["status"],
                bytes=doc["bytes"],
                chunk_count=doc["chunk_count"],
                has_analysis=doc["has_analysis"]
            )
            document_responses.append(doc_response)
        
        return DocumentListResponse(
            documents=document_responses,
            total=result["total"],
            limit=limit,
            offset=offset,
            has_next=result["has_next"],
            has_prev=result["has_prev"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

@router.get("/{document_id}", response_model=DocumentDetail)
async def get_document(
    document_id: int,
    include_content: bool = Query(False),
    include_analysis: bool = Query(True),
    document_service: DocumentService = Depends(get_document_service),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Get detailed document information
    
    Args:
        document_id (int): Document ID
        include_content (bool): Whether to include full text content
        include_analysis (bool): Whether to include analysis summary
        
    Returns:
        DocumentDetail: Detailed document information
    
    Example:
        GET /api/documents/123?include_content=true&include_analysis=true
    """
    try:
        document = document_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get content if requested
        content = None
        if include_content:
            content = document_service.get_document_content(document_id)
        
        # Get analysis if requested
        analysis_summary = None
        if include_analysis:
            analysis_data = analysis_service.get_document_analysis(document_id)
            if "error" not in analysis_data:
                analysis_summary = analysis_data
        
        # Convert tags
        tags = document.tags.split(',') if document.tags else []
        
        return DocumentDetail(
            id=document.id,
            slug=document.slug,
            title=document.title,
            version=document.version,
            created_at=document.created_at.isoformat(),
            updated_at=document.updated_at.isoformat(),
            author=document.author,
            domain=document.domain,
            tags=tags,
            status=document.status,
            bytes=document.bytes,
            chunk_count=len(document.chunks),
            has_analysis=any(c.intent_label for c in document.chunks),
            content=content,
            checksum=document.checksum,
            analysis_summary=analysis_summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")

@router.get("/slug/{slug}/versions")
async def get_document_versions(
    slug: str,
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Get all versions of a document by slug
    
    Args:
        slug (str): Document slug
        
    Returns:
        Dict[str, Any]: List of document versions
    
    Example:
        GET /api/documents/slug/api-documentation/versions
    """
    try:
        versions = document_service.get_document_versions(slug)
        if not versions:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "slug": slug,
            "versions": versions,
            "total_versions": len(versions),
            "latest_version": max(v["version"] for v in versions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get versions: {str(e)}")

@router.post("/{document_id}/analyze", response_model=AnalysisResponse)
async def analyze_document(
    document_id: int,
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    document_service: DocumentService = Depends(get_document_service),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Start document analysis
    
    Args:
        document_id (int): Document ID to analyze
        request (AnalysisRequest): Analysis configuration
        
    Returns:
        AnalysisResponse: Analysis status
    
    Example:
        POST /api/documents/123/analyze
        {"force_reanalysis": true}
    """
    try:
        document = document_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if analysis is already running
        if document.status == "analyzing":
            return AnalysisResponse(
                document_id=document_id,
                status="analyzing",
                message="Analysis already in progress"
            )
        
        # Start analysis in background
        background_tasks.add_task(
            _analyze_document_background, 
            analysis_service, 
            document_id, 
            request.force_reanalysis
        )
        
        # Update status
        document_service.update_document_status(document_id, "analyzing", "Analysis started")
        
        return AnalysisResponse(
            document_id=document_id,
            status="analyzing",
            message="Analysis started"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")

@router.get("/{document_id}/analysis")
async def get_document_analysis(
    document_id: int,
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Get document analysis results
    
    Args:
        document_id (int): Document ID
        
    Returns:
        Dict[str, Any]: Analysis results
    
    Example:
        GET /api/documents/123/analysis
    """
    try:
        analysis = analysis_service.get_document_analysis(document_id)
        
        if "error" in analysis:
            if analysis["error"] == "Document not found":
                raise HTTPException(status_code=404, detail="Document not found")
            else:
                raise HTTPException(status_code=500, detail=analysis["error"])
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analysis: {str(e)}")

@router.get("/{document_id}/stats")
async def get_document_stats(
    document_id: int,
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Get comprehensive document statistics
    
    Args:
        document_id (int): Document ID
        
    Returns:
        Dict[str, Any]: Document statistics
    
    Example:
        GET /api/documents/123/stats
    """
    try:
        stats = document_service.get_document_stats(document_id)
        
        if "error" in stats:
            if stats["error"] == "Document not found":
                raise HTTPException(status_code=404, detail="Document not found")
            else:
                raise HTTPException(status_code=500, detail=stats["error"])
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    delete_all_versions: bool = Query(False),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Delete a document
    
    Args:
        document_id (int): Document ID to delete
        delete_all_versions (bool): Whether to delete all versions
        
    Returns:
        Dict[str, Any]: Deletion result
    
    Example:
        DELETE /api/documents/123?delete_all_versions=true
    """
    try:
        document = document_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        success = document_service.delete_document(document_id, delete_all_versions)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete document")
        
        return {
            "success": True,
            "message": f"Document {document.title} deleted successfully",
            "deleted_all_versions": delete_all_versions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@router.patch("/{document_id}/status")
async def update_document_status(
    document_id: int,
    status: str,
    details: Optional[str] = None,
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Update document status
    
    Args:
        document_id (int): Document ID
        status (str): New status
        details (str, optional): Additional details
        
    Returns:
        Dict[str, Any]: Update result
    
    Example:
        PATCH /api/documents/123/status
        {"status": "indexed", "details": "Analysis completed"}
    """
    try:
        valid_statuses = ["uploaded", "analyzing", "indexed", "error"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        success = document_service.update_document_status(document_id, status, details)
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "success": True,
            "document_id": document_id,
            "new_status": status,
            "details": details
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update status: {str(e)}")

# Background task functions
async def _analyze_document_background(analysis_service: AnalysisService, document_id: int, 
                                     force_reanalysis: bool = False):
    """Background task for document analysis"""
    try:
        print(f"🔄 Starting background analysis for document {document_id}")
        result = await analysis_service.analyze_document(document_id, force_reanalysis)
        
        if "error" in result:
            print(f"❌ Background analysis failed: {result['error']}")
        else:
            print(f"✅ Background analysis completed for document {document_id}")
            
    except Exception as e:
        print(f"❌ Background analysis exception: {e}")

if __name__ == "__main__":
    # Test the router
    print("🧪 Documents router loaded successfully!")
    print("📋 Available endpoints:")
    for route in router.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = list(route.methods)
            print(f"  {methods} {route.path}")