# services/document_service.py
"""
DocuReview Pro - Document Management Service
CRUD operations for documents, files, and chunks
"""
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_

from database import Document, File, Chunk, VectorIndex, AuditLog
from utils.text_processing import normalize_text, generate_document_slug, calculate_text_hash, detect_document_structure
from config import Config

class DocumentService:
    """Service for document management operations"""
    
    def __init__(self, db: Session):
        """
        Initialize document service
        
        Args:
            db (Session): Database session
        
        Example:
            service = DocumentService(db_session)
        """
        self.db = db
        self.upload_folder = Path(Config.UPLOAD_FOLDER)
        self.upload_folder.mkdir(parents=True, exist_ok=True)

    def create_document(self, title: str, content: str, filename: str = None, 
                       metadata: Dict[str, Any] = None) -> Document:
        """
        Create a new document or new version of existing document
        
        Args:
            title (str): Document title
            content (str): Document text content
            filename (str, optional): Original filename
            metadata (Dict[str, Any], optional): Additional metadata
        
        Returns:
            Document: Created document instance
        
        Example:
            doc = service.create_document(
                title="API Documentation",
                content="This document describes...",
                filename="api_docs.txt",
                metadata={"author": "John Doe", "domain": "technical"}
            )
        """
        try:
            # Normalize and validate content
            if not content or not content.strip():
                raise ValueError("Document content cannot be empty")
            
            normalized_content = normalize_text(content)
            content_hash = calculate_text_hash(normalized_content)
            
            # Generate slug from title
            slug = generate_document_slug(title)
            
            # Check if document with this slug exists
            existing_doc = self.db.query(Document).filter(
                Document.slug == slug
            ).order_by(desc(Document.version)).first()
            
            # Determine version number
            if existing_doc:
                # Check if content is identical to latest version
                if existing_doc.checksum == content_hash:
                    return existing_doc  # Return existing if identical
                version = existing_doc.version + 1
            else:
                version = 1
            
            # Extract metadata
            meta = metadata or {}
            author = meta.get("author", "")
            source = meta.get("source", "")
            domain = meta.get("domain", "")
            tags = meta.get("tags", "")
            notes = meta.get("notes", "")
            
            # Create document record
            document = Document(
                slug=slug,
                title=title,
                version=version,
                author=author,
                source=source,
                domain=domain,
                tags=tags if isinstance(tags, str) else ",".join(tags) if tags else "",
                notes=notes,
                checksum=content_hash,
                bytes=len(normalized_content.encode('utf-8')),
                status='uploaded'
            )
            
            self.db.add(document)
            self.db.flush()  # Get the ID
            
            # Save file to disk
            file_path = self._save_document_file(document.id, normalized_content, filename)
            
            # Create file record
            file_record = File(
                document_id=document.id,
                filename=filename or f"{slug}_v{version}.txt",
                path=str(file_path),
                mime="text/plain",
                size=len(normalized_content.encode('utf-8'))
            )
            
            self.db.add(file_record)
            
            # Log the operation
            self._log_operation("upload", "document", document.id, {
                "title": title,
                "version": version,
                "size_bytes": document.bytes
            })
            
            self.db.commit()
            
            print(f"✅ Document created: {title} v{version} (ID: {document.id})")
            return document
            
        except Exception as e:
            self.db.rollback()
            print(f"❌ Error creating document: {e}")
            raise

    def get_document(self, document_id: int) -> Optional[Document]:
        """
        Get document by ID
        
        Args:
            document_id (int): Document ID
        
        Returns:
            Optional[Document]: Document instance or None
        
        Example:
            doc = service.get_document(123)
        """
        return self.db.query(Document).filter(Document.id == document_id).first()

    def get_document_by_slug_version(self, slug: str, version: int) -> Optional[Document]:
        """
        Get specific document version by slug and version
        
        Args:
            slug (str): Document slug
            version (int): Version number
        
        Returns:
            Optional[Document]: Document instance or None
        
        Example:
            doc = service.get_document_by_slug_version("api-docs", 2)
        """
        return self.db.query(Document).filter(
            and_(Document.slug == slug, Document.version == version)
        ).first()

    def get_latest_document_version(self, slug: str) -> Optional[Document]:
        """
        Get latest version of document by slug
        
        Args:
            slug (str): Document slug
        
        Returns:
            Optional[Document]: Latest document version or None
        
        Example:
            latest = service.get_latest_document_version("api-docs")
        """
        return self.db.query(Document).filter(
            Document.slug == slug
        ).order_by(desc(Document.version)).first()

    def list_documents(self, limit: int = 50, offset: int = 0, 
                      search: str = None, domain: str = None) -> Dict[str, Any]:
        """
        List documents with pagination and filtering
        
        Args:
            limit (int): Maximum number of results
            offset (int): Number of results to skip
            search (str, optional): Search term for title/content
            domain (str, optional): Filter by domain
        
        Returns:
            Dict[str, Any]: Paginated results with metadata
        
        Example:
            result = service.list_documents(limit=20, search="API")
            docs = result["documents"]
            total = result["total"]
        """
        try:
            # Base query - get latest version of each document
            subquery = self.db.query(
                Document.slug,
                func.max(Document.version).label('max_version')
            ).group_by(Document.slug).subquery()
            
            query = self.db.query(Document).join(
                subquery,
                and_(
                    Document.slug == subquery.c.slug,
                    Document.version == subquery.c.max_version
                )
            )
            
            # Apply filters
            if search:
                search_pattern = f"%{search}%"
                query = query.filter(
                    Document.title.ilike(search_pattern)
                )
            
            if domain:
                query = query.filter(Document.domain == domain)
            
            # Get total count
            total = query.count()
            
            # Apply pagination and ordering
            documents = query.order_by(desc(Document.updated_at)).offset(offset).limit(limit).all()
            
            # Enhance with additional data
            enhanced_docs = []
            for doc in documents:
                doc_data = {
                    "id": doc.id,
                    "slug": doc.slug,
                    "title": doc.title,
                    "version": doc.version,
                    "created_at": doc.created_at,
                    "updated_at": doc.updated_at,
                    "author": doc.author,
                    "domain": doc.domain,
                    "tags": doc.tags.split(",") if doc.tags else [],
                    "status": doc.status,
                    "bytes": doc.bytes,
                    "chunk_count": len(doc.chunks),
                    "has_analysis": any(chunk.intent_label for chunk in doc.chunks)
                }
                enhanced_docs.append(doc_data)
            
            return {
                "documents": enhanced_docs,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_next": offset + limit < total,
                "has_prev": offset > 0
            }
            
        except Exception as e:
            print(f"❌ Error listing documents: {e}")
            return {"documents": [], "total": 0, "error": str(e)}

    def get_document_versions(self, slug: str) -> List[Dict[str, Any]]:
        """
        Get all versions of a document
        
        Args:
            slug (str): Document slug
        
        Returns:
            List[Dict[str, Any]]: List of document versions
        
        Example:
            versions = service.get_document_versions("api-docs")
        """
        try:
            documents = self.db.query(Document).filter(
                Document.slug == slug
            ).order_by(desc(Document.version)).all()
            
            versions = []
            for doc in documents:
                version_data = {
                    "id": doc.id,
                    "version": doc.version,
                    "created_at": doc.created_at,
                    "updated_at": doc.updated_at,
                    "author": doc.author,
                    "notes": doc.notes,
                    "status": doc.status,
                    "bytes": doc.bytes,
                    "chunk_count": len(doc.chunks),
                    "checksum": doc.checksum[:8] + "..." if doc.checksum else ""
                }
                versions.append(version_data)
            
            return versions
            
        except Exception as e:
            print(f"❌ Error getting document versions: {e}")
            return []

    def get_document_content(self, document_id: int) -> Optional[str]:
        """
        Get document text content from file
        
        Args:
            document_id (int): Document ID
        
        Returns:
            Optional[str]: Document content or None
        
        Example:
            content = service.get_document_content(123)
        """
        try:
            document = self.get_document(document_id)
            if not document or not document.files:
                return None
            
            file_path = Path(document.files[0].path)
            if not file_path.exists():
                print(f"⚠️  File not found: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
                
        except Exception as e:
            print(f"❌ Error reading document content: {e}")
            return None

    def update_document_status(self, document_id: int, status: str, details: str = None) -> bool:
        """
        Update document processing status
        
        Args:
            document_id (int): Document ID
            status (str): New status (uploaded|analyzing|indexed|error)
            details (str, optional): Additional details
        
        Returns:
            bool: Success status
        
        Example:
            success = service.update_document_status(123, "analyzing", "Starting AI analysis")
        """
        try:
            document = self.get_document(document_id)
            if not document:
                return False
            
            document.status = status
            document.updated_at = datetime.utcnow()
            
            # Log status change
            self._log_operation("status_change", "document", document_id, {
                "new_status": status,
                "details": details
            })
            
            self.db.commit()
            return True
            
        except Exception as e:
            print(f"❌ Error updating document status: {e}")
            self.db.rollback()
            return False

    def delete_document(self, document_id: int, delete_all_versions: bool = False) -> bool:
        """
        Delete document (and optionally all versions)
        
        Args:
            document_id (int): Document ID
            delete_all_versions (bool): If True, delete all versions of the document
        
        Returns:
            bool: Success status
        
        Example:
            success = service.delete_document(123, delete_all_versions=True)
        """
        try:
            document = self.get_document(document_id)
            if not document:
                return False
            
            if delete_all_versions:
                # Delete all versions of this document
                all_versions = self.db.query(Document).filter(
                    Document.slug == document.slug
                ).all()
                
                for version_doc in all_versions:
                    self._delete_single_document(version_doc)
            else:
                # Delete only this version
                self._delete_single_document(document)
            
            self.db.commit()
            
            print(f"✅ Document deleted: {document.title} v{document.version}")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting document: {e}")
            self.db.rollback()
            return False

    def get_document_stats(self, document_id: int) -> Dict[str, Any]:
        """
        Get comprehensive document statistics
        
        Args:
            document_id (int): Document ID
        
        Returns:
            Dict[str, Any]: Document statistics
        
        Example:
            stats = service.get_document_stats(123)
        """
        try:
            document = self.get_document(document_id)
            if not document:
                return {"error": "Document not found"}
            
            content = self.get_document_content(document_id)
            if not content:
                return {"error": "Content not accessible"}
            
            # Analyze structure
            structure = detect_document_structure(content)
            
            # Count chunks by intent
            chunk_intents = {}
            for chunk in document.chunks:
                intent = chunk.intent_label or "unknown"
                chunk_intents[intent] = chunk_intents.get(intent, 0) + 1
            
            stats = {
                "document_info": {
                    "id": document.id,
                    "title": document.title,
                    "version": document.version,
                    "created_at": document.created_at,
                    "status": document.status,
                    "bytes": document.bytes
                },
                "content_stats": structure,
                "chunk_stats": {
                    "total_chunks": len(document.chunks),
                    "chunks_by_intent": chunk_intents,
                    "analyzed_chunks": sum(1 for c in document.chunks if c.intent_label)
                },
                "indexing_stats": {
                    "has_vector_index": len(document.vector_indexes) > 0,
                    "index_count": len(document.vector_indexes)
                }
            }
            
            return stats
            
        except Exception as e:
            print(f"❌ Error getting document stats: {e}")
            return {"error": str(e)}

    def _save_document_file(self, document_id: int, content: str, filename: str = None) -> Path:
        """Save document content to file"""
        # Create document-specific directory
        doc_dir = self.upload_folder / f"doc_{document_id}"
        doc_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        if not filename:
            filename = f"document_{document_id}.txt"
        
        file_path = doc_dir / filename
        
        # Save content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return file_path

    def _delete_single_document(self, document: Document):
        """Delete a single document and its files"""
        # Delete physical files
        for file_record in document.files:
            file_path = Path(file_record.path)
            if file_path.exists():
                file_path.unlink()
            
            # Remove document directory if empty
            doc_dir = file_path.parent
            if doc_dir.exists() and not any(doc_dir.iterdir()):
                doc_dir.rmdir()
        
        # Delete FAISS indexes
        for vector_index in document.vector_indexes:
            index_path = Path(vector_index.path)
            if index_path.exists():
                index_path.unlink()
            
            # Delete metadata file
            metadata_path = index_path.with_suffix('.json')
            if metadata_path.exists():
                metadata_path.unlink()
        
        # Log deletion
        self._log_operation("delete", "document", document.id, {
            "title": document.title,
            "version": document.version
        })
        
        # Delete from database (cascades to related records)
        self.db.delete(document)

    def _log_operation(self, operation: str, entity_type: str, entity_id: int, 
                      details: Dict[str, Any], execution_time_ms: float = None):
        """Log operation to audit trail"""
        try:
            audit_log = AuditLog(
                operation=operation,
                entity_type=entity_type,
                entity_id=entity_id,
                details=str(details) if details else None,
                execution_time_ms=execution_time_ms
            )
            self.db.add(audit_log)
        except Exception as e:
            print(f"⚠️  Audit logging failed: {e}")

if __name__ == "__main__":
    # Test document service
    from database import SessionLocal, init_database
    
    print("🧪 Testing Document Service...")
    
    # Initialize database
    init_database()
    
    # Test with database session
    db = SessionLocal()
    try:
        service = DocumentService(db)
        
        # Test document creation
        test_content = """# API Documentation

This document describes the REST API endpoints.

## Authentication
All requests require API key authentication.

## Endpoints
- GET /api/users - List users
- POST /api/users - Create user
        """
        
        doc = service.create_document(
            title="API Documentation v1.0",
            content=test_content,
            filename="api_docs.txt",
            metadata={
                "author": "Test User",
                "domain": "technical",
                "tags": ["api", "documentation"]
            }
        )
        
        print(f"✅ Created document: {doc.title} (ID: {doc.id})")
        
        # Test listing
        results = service.list_documents(limit=10)
        print(f"✅ Listed {len(results['documents'])} documents")
        
        # Test stats
        stats = service.get_document_stats(doc.id)
        print(f"✅ Document stats: {stats['content_stats']['word_count']} words")
        
    finally:
        db.close()
    
    print("✅ Document Service test completed!")