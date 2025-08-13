# models/document.py
"""
DocuReview Pro - Pydantic Models for API Validation
Request/response models for document management endpoints
"""
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum

# Enums for validation
class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    ANALYZING = "analyzing"
    INDEXED = "indexed"
    ERROR = "error"

class IntentLabel(str, Enum):
    OVERVIEW = "overview"
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    PROCEDURE = "procedure"
    RISKS = "risks"
    EXAMPLE = "example"
    CONCLUSION = "conclusion"
    OTHER = "other"

class AnalysisGranularity(str, Enum):
    CHARACTER = "character"
    WORD = "word"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"

class ComparisonAlgorithm(str, Enum):
    SYNTACTIC = "syntactic"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"

# Base models
class BaseDocument(BaseModel):
    """Base document model with common fields"""
    title: str = Field(..., min_length=1, max_length=500, description="Document title")
    author: Optional[str] = Field(None, max_length=255, description="Document author")
    domain: Optional[str] = Field(None, max_length=255, description="Document domain/category")
    tags: Optional[List[str]] = Field(default_factory=list, description="Document tags")
    notes: Optional[str] = Field(None, max_length=2000, description="Additional notes")

class BaseChunk(BaseModel):
    """Base chunk model with common fields"""
    text: str = Field(..., min_length=1, description="Chunk text content")
    chunk_index: int = Field(..., ge=0, description="Chunk index in document")
    token_start: Optional[int] = Field(None, ge=0, description="Starting token position")
    token_end: Optional[int] = Field(None, ge=0, description="Ending token position")

# Document models
class DocumentCreate(BaseDocument):
    """Document creation request"""
    content: Optional[str] = Field(None, description="Document content (for text creation)")
    auto_analyze: bool = Field(True, description="Automatically analyze after upload")
    
    @validator('tags')
    def validate_tags(cls, v):
        if v and len(v) > 20:
            raise ValueError('Maximum 20 tags allowed')
        return v

class DocumentUpdate(BaseModel):
    """Document update request"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    author: Optional[str] = Field(None, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)
    tags: Optional[List[str]] = Field(None)
    notes: Optional[str] = Field(None, max_length=2000)
    status: Optional[DocumentStatus] = Field(None, description="Document status")

class DocumentResponse(BaseDocument):
    """Document response model"""
    id: int = Field(..., description="Document ID")
    slug: str = Field(..., description="Document slug")
    version: int = Field(..., ge=1, description="Document version")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    status: DocumentStatus = Field(..., description="Processing status")
    bytes: int = Field(..., ge=0, description="Document size in bytes")
    checksum: Optional[str] = Field(None, description="Content checksum")
    chunk_count: int = Field(0, ge=0, description="Number of chunks")
    has_analysis: bool = Field(False, description="Whether document has been analyzed")
    
    class Config:
        from_attributes = True

class DocumentDetail(DocumentResponse):
    """Detailed document response with content and analysis"""
    content: Optional[str] = Field(None, description="Full document content")
    file_info: Optional[Dict[str, Any]] = Field(None, description="File metadata")
    analysis_summary: Optional[Dict[str, Any]] = Field(None, description="Analysis summary")
    version_history: Optional[List[Dict[str, Any]]] = Field(None, description="Version history")

class DocumentList(BaseModel):
    """Paginated document list response"""
    documents: List[DocumentResponse] = Field(..., description="List of documents")
    total: int = Field(..., ge=0, description="Total number of documents")
    limit: int = Field(..., ge=1, description="Results per page")
    offset: int = Field(..., ge=0, description="Number of results skipped")
    has_next: bool = Field(..., description="Whether there are more results")
    has_prev: bool = Field(..., description="Whether there are previous results")
    filters_applied: Optional[Dict[str, Any]] = Field(None, description="Applied filters")

# Analysis models
class ChunkAnalysis(BaseChunk):
    """Chunk with analysis results"""
    intent_label: Optional[IntentLabel] = Field(None, description="Classified intent")
    summary: Optional[str] = Field(None, max_length=500, description="Chunk summary")
    heading: Optional[str] = Field(None, max_length=200, description="Inferred heading")
    subheading: Optional[str] = Field(None, max_length=200, description="Inferred subheading")
    key_values: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Extracted key-value pairs")
    entities: Optional[List[str]] = Field(default_factory=list, description="Named entities")
    relationships: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="Entity relationships")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Analysis confidence")

class AnalysisRequest(BaseModel):
    """Document analysis request"""
    document_id: int = Field(..., description="Document ID to analyze")
    force_reanalysis: bool = Field(False, description="Force reanalysis even if already analyzed")
    analysis_options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Analysis configuration")

class AnalysisResponse(BaseModel):
    """Analysis operation response"""
    document_id: int = Field(..., description="Document ID")
    status: str = Field(..., description="Analysis status")
    message: Optional[str] = Field(None, description="Status message")
    chunks_processed: Optional[int] = Field(None, ge=0, description="Number of chunks processed")
    processing_time_seconds: Optional[float] = Field(None, ge=0, description="Processing time")
    analysis_summary: Optional[Dict[str, Any]] = Field(None, description="Analysis summary")
    errors: Optional[List[str]] = Field(default_factory=list, description="Any errors encountered")

class DocumentAnalysis(BaseModel):
    """Complete document analysis result"""
    document_info: DocumentResponse = Field(..., description="Document information")
    chunks: List[ChunkAnalysis] = Field(..., description="Analyzed chunks")
    document_outline: List[Dict[str, Any]] = Field(..., description="Document structure outline")
    analysis_stats: Dict[str, Any] = Field(..., description="Analysis statistics")
    intent_distribution: Dict[str, int] = Field(..., description="Distribution of intent labels")
    processing_metadata: Dict[str, Any] = Field(..., description="Processing metadata")

# Version management models
class VersionInfo(BaseModel):
    """Document version information"""
    version: int = Field(..., ge=1, description="Version number")
    created_at: datetime = Field(..., description="Version creation time")
    author: Optional[str] = Field(None, description="Version author")
    notes: Optional[str] = Field(None, description="Version notes")
    status: DocumentStatus = Field(..., description="Version status")
    bytes: int = Field(..., ge=0, description="Version size")
    checksum: str = Field(..., description="Content checksum")
    is_latest: bool = Field(False, description="Whether this is the latest version")

class VersionList(BaseModel):
    """List of document versions"""
    document_slug: str = Field(..., description="Document slug")
    document_title: str = Field(..., description="Document title")
    versions: List[VersionInfo] = Field(..., description="Version history")
    total_versions: int = Field(..., ge=1, description="Total number of versions")
    latest_version: int = Field(..., ge=1, description="Latest version number")

# File upload models
class FileUpload(BaseModel):
    """File upload request metadata"""
    title: str = Field(..., min_length=1, max_length=500)
    author: Optional[str] = Field(None, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)
    tags: Optional[str] = Field(None, description="Comma-separated tags")
    notes: Optional[str] = Field(None, max_length=2000)
    auto_analyze: bool = Field(True, description="Automatically analyze after upload")
    version_notes: Optional[str] = Field(None, max_length=500, description="Notes for this version")

class UploadResponse(BaseModel):
    """File upload response"""
    success: bool = Field(..., description="Upload success status")
    document: DocumentResponse = Field(..., description="Created document")
    message: str = Field(..., description="Status message")
    warnings: Optional[List[str]] = Field(default_factory=list, description="Any warnings")
    analysis_scheduled: bool = Field(False, description="Whether analysis was scheduled")

# Statistics models
class ContentStats(BaseModel):
    """Content statistics"""
    word_count: int = Field(..., ge=0)
    char_count: int = Field(..., ge=0)
    line_count: int = Field(..., ge=0)
    paragraph_count: int = Field(..., ge=0)
    heading_count: int = Field(..., ge=0)
    avg_words_per_paragraph: float = Field(..., ge=0)
    readability_score: Optional[float] = Field(None, ge=0, le=100)

class DocumentStats(BaseModel):
    """Comprehensive document statistics"""
    document_info: DocumentResponse = Field(..., description="Basic document info")
    content_stats: ContentStats = Field(..., description="Content analysis")
    chunk_stats: Dict[str, Any] = Field(..., description="Chunk analysis statistics")
    indexing_stats: Dict[str, Any] = Field(..., description="Indexing statistics")
    analysis_history: Optional[List[Dict[str, Any]]] = Field(None, description="Analysis history")

# Validation helpers
class DocumentFilter(BaseModel):
    """Document filtering options"""
    search: Optional[str] = Field(None, max_length=255, description="Search term")
    domain: Optional[str] = Field(None, max_length=255, description="Domain filter")
    status: Optional[DocumentStatus] = Field(None, description="Status filter")
    author: Optional[str] = Field(None, max_length=255, description="Author filter")
    tags: Optional[List[str]] = Field(None, description="Tag filters")
    date_from: Optional[datetime] = Field(None, description="Date range start")
    date_to: Optional[datetime] = Field(None, description="Date range end")
    has_analysis: Optional[bool] = Field(None, description="Filter by analysis status")
    
    @validator('date_to')
    def validate_date_range(cls, v, values):
        if v and values.get('date_from') and v < values['date_from']:
            raise ValueError('date_to must be after date_from')
        return v

class PaginationParams(BaseModel):
    """Pagination parameters"""
    limit: int = Field(20, ge=1, le=100, description="Results per page")
    offset: int = Field(0, ge=0, description="Number of results to skip")
    sort_by: Optional[str] = Field("updated_at", description="Sort field")
    sort_order: Optional[str] = Field("desc", regex="^(asc|desc)$", description="Sort order")

# Error models
class ValidationError(BaseModel):
    """Validation error response"""
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Error message")
    value: Optional[Any] = Field(None, description="Invalid value")

class ErrorResponse(BaseModel):
    """API error response"""
    success: bool = Field(False, description="Success status")
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    validation_errors: Optional[List[ValidationError]] = Field(None, description="Validation errors")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

# Success response wrapper
class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool = Field(True, description="Success status")
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

if __name__ == "__main__":
    # Test model validation
    print("🧪 Testing Pydantic Models...")
    
    # Test document creation
    doc_create = DocumentCreate(
        title="Test Document",
        author="Test Author",
        domain="technical",
        tags=["api", "documentation"],
        notes="This is a test document",
        auto_analyze=True
    )
    print(f"✅ Document create model: {doc_create.title}")
    
    # Test validation
    try:
        invalid_doc = DocumentCreate(
            title="",  # Invalid: empty title
            tags=["tag"] * 25  # Invalid: too many tags
        )
    except ValueError as e:
        print(f"✅ Validation working: {e}")
    
    # Test response model
    doc_response = DocumentResponse(
        id=1,
        slug="test-document",
        title="Test Document",
        version=1,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        status=DocumentStatus.INDEXED,
        bytes=1024,
        chunk_count=5,
        has_analysis=True,
        author="Test Author",
        domain="technical",
        tags=["api", "documentation"]
    )
    print(f"✅ Document response model: v{doc_response.version}")
    
    print("✅ Pydantic models test completed!")