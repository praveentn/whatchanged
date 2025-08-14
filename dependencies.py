# dependencies.py
"""
DocuReview Pro - FastAPI Dependencies
Fixed dependency injection for services and database connections
"""
from functools import lru_cache
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from services.llm_service import LLMService
from services.embedding_service import EmbeddingService
from services.document_service import DocumentService
from services.analysis_service import AnalysisService
from services.comparison_service import ComparisonService
from config import Config

# Cached service instances for performance
@lru_cache()
def get_llm_service() -> LLMService:
    """
    Get LLM service instance (cached)
    
    Returns:
        LLMService: Azure OpenAI service instance
    """
    try:
        return LLMService(
            endpoint=Config.AZURE_OPENAI_ENDPOINT,
            api_key=Config.AZURE_OPENAI_API_KEY,
            api_version=Config.AZURE_OPENAI_API_VERSION,
            deployment=Config.AZURE_OPENAI_DEPLOYMENT
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize LLM service: {str(e)}"
        )

@lru_cache()
def get_embedding_service() -> EmbeddingService:
    """
    Get embedding service instance (cached)
    
    Returns:
        EmbeddingService: Sentence transformer service instance
    """
    try:
        return EmbeddingService(
            model_name=Config.SENTENCE_TRANSFORMER_MODEL,
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize embedding service: {str(e)}"
        )

def get_document_service(db: Session = Depends(get_db)) -> DocumentService:
    """
    Get document service instance
    
    Args:
        db (Session): Database session
    
    Returns:
        DocumentService: Document management service
    """
    return DocumentService(db)

def get_analysis_service(
    db: Session = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
) -> AnalysisService:
    """
    Get analysis service instance
    
    Args:
        db (Session): Database session
        llm_service (LLMService): LLM service
        embedding_service (EmbeddingService): Embedding service
    
    Returns:
        AnalysisService: AI analysis service
    """
    return AnalysisService(db, llm_service, embedding_service)

def get_comparison_service(
    db: Session = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
) -> ComparisonService:
    """
    Get comparison service instance
    
    Args:
        db (Session): Database session
        llm_service (LLMService): LLM service
        embedding_service (EmbeddingService): Embedding service
    
    Returns:
        ComparisonService: Document comparison service
    """
    return ComparisonService(db, llm_service, embedding_service)

def validate_admin_access():
    """
    Validate admin access (placeholder for future authentication)
    
    Returns:
        bool: True if admin access is allowed
    """
    # In v1, no authentication - always allow
    # TODO: Implement proper authentication in future versions
    return True

def get_admin_service(db: Session = Depends(get_db)) -> Session:
    """
    Get admin service - returns DB session for admin operations
    
    Args:
        db (Session): Database session
    
    Returns:
        Session: Database session for admin operations
    """
    # Validate admin access
    validate_admin_access()
    return db

if __name__ == "__main__":
    # Test dependencies
    print("🧪 Testing service dependencies...")
    
    try:
        llm_service = get_llm_service()
        print(f"✅ LLM Service: {type(llm_service).__name__}")
        
        embedding_service = get_embedding_service()
        print(f"✅ Embedding Service: {type(embedding_service).__name__}")
        
        print("✅ All dependencies initialized successfully!")
        
    except Exception as e:
        print(f"❌ Dependency test failed: {e}")