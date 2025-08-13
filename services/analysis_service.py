# services/analysis_service.py
"""
DocuReview Pro - AI Analysis Service
Comprehensive document analysis using LLM and embeddings
"""
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session

from database import Document, Chunk, VectorIndex
from services.llm_service import LLMService
from services.embedding_service import EmbeddingService
from utils.text_processing import detect_document_structure

class AnalysisService:
    """Service for AI-powered document analysis"""
    
    def __init__(self, db: Session, llm_service: LLMService, embedding_service: EmbeddingService):
        """
        Initialize analysis service
        
        Args:
            db (Session): Database session
            llm_service (LLMService): LLM service for AI analysis
            embedding_service (EmbeddingService): Embedding service for vectors
        
        Example:
            service = AnalysisService(db, llm_service, embedding_service)
        """
        self.db = db
        self.llm_service = llm_service
        self.embedding_service = embedding_service

    async def analyze_document(self, document_id: int, force_reanalysis: bool = False) -> Dict[str, Any]:
        """
        Perform comprehensive AI analysis of document
        
        Args:
            document_id (int): Document ID to analyze
            force_reanalysis (bool): Force reanalysis even if already analyzed
        
        Returns:
            Dict[str, Any]: Analysis results and statistics
        
        Example:
            result = await service.analyze_document(123)
            print(f"Analyzed {result['chunks_processed']} chunks")
        """
        start_time = datetime.utcnow()
        
        try:
            # Get document
            document = self.db.query(Document).filter(Document.id == document_id).first()
            if not document:
                return {"error": "Document not found"}
            
            # Check if already analyzed
            if not force_reanalysis and document.chunks and any(c.intent_label for c in document.chunks):
                return {"message": "Document already analyzed", "document_id": document_id}
            
            # Update status
            document.status = "analyzing"
            self.db.commit()
            
            # Get document content
            content = self._get_document_content(document)
            if not content:
                document.status = "error"
                self.db.commit()
                return {"error": "Could not read document content"}
            
            print(f"🔄 Starting analysis for document {document_id}: {document.title}")
            
            # Step 1: Chunk the document
            chunks = self.embedding_service.chunk_text(content)
            print(f"📄 Generated {len(chunks)} chunks")
            
            # Step 2: Generate embeddings
            chunk_texts = [chunk["text"] for chunk in chunks]
            embeddings = self.embedding_service.embed_texts(chunk_texts)
            print(f"🧠 Generated embeddings: {embeddings.shape}")
            
            # Step 3: Analyze each chunk with LLM
            chunk_analyses = []
            for i, chunk in enumerate(chunks):
                try:
                    analysis = await self.llm_service.analyze_chunk(
                        text=chunk["text"],
                        chunk_index=i,
                        document_title=document.title,
                        context={"total_chunks": len(chunks)}
                    )
                    chunk_analyses.append(analysis)
                    
                    if i % 5 == 0:  # Progress update every 5 chunks
                        print(f"🔄 Analyzed chunk {i+1}/{len(chunks)}")
                        
                except Exception as e:
                    print(f"⚠️  Error analyzing chunk {i}: {e}")
                    chunk_analyses.append(self._fallback_chunk_analysis(chunk, i))
            
            # Step 4: Save chunks to database
            self._save_chunks_to_db(document_id, chunks, chunk_analyses, embeddings)
            
            # Step 5: Build FAISS index
            index_path = self.embedding_service.build_document_index(document_id, chunks)
            self._save_vector_index(document_id, index_path, embeddings.shape[1])
            
            # Step 6: Generate document synthesis
            doc_synthesis = await self.llm_service.synthesize_document(
                document_title=document.title,
                chunk_analyses=chunk_analyses
            )
            
            # Step 7: Update document status and metadata
            document.status = "indexed"
            self.db.commit()
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            analysis_result = {
                "document_id": document_id,
                "chunks_processed": len(chunks),
                "embeddings_generated": embeddings.shape[0],
                "processing_time_seconds": round(processing_time, 2),
                "document_synthesis": doc_synthesis,
                "chunk_intents": self._count_chunk_intents(chunk_analyses),
                "index_path": index_path,
                "success": True
            }
            
            print(f"✅ Analysis completed for document {document_id} in {processing_time:.1f}s")
            return analysis_result
            
        except Exception as e:
            print(f"❌ Analysis failed for document {document_id}: {e}")
            
            # Update status to error
            try:
                document = self.db.query(Document).filter(Document.id == document_id).first()
                if document:
                    document.status = "error"
                    self.db.commit()
            except:
                pass
            
            return {"error": str(e), "document_id": document_id}

    async def reanalyze_chunk(self, chunk_id: int) -> Dict[str, Any]:
        """
        Reanalyze a specific chunk
        
        Args:
            chunk_id (int): Chunk ID to reanalyze
        
        Returns:
            Dict[str, Any]: Updated chunk analysis
        
        Example:
            result = await service.reanalyze_chunk(456)
        """
        try:
            chunk = self.db.query(Chunk).filter(Chunk.id == chunk_id).first()
            if not chunk:
                return {"error": "Chunk not found"}
            
            document = chunk.document
            
            # Reanalyze with LLM
            analysis = await self.llm_service.analyze_chunk(
                text=chunk.text,
                chunk_index=chunk.chunk_ix,
                document_title=document.title
            )
            
            # Update chunk with new analysis
            chunk.intent_label = analysis.get("intent_label")
            chunk.summary = analysis.get("summary")
            chunk.heading = analysis.get("heading")
            chunk.subheading = analysis.get("subheading")
            chunk.key_values = json.dumps(analysis.get("key_values", {}))
            chunk.triples = json.dumps(analysis.get("relationships", []))
            
            self.db.commit()
            
            return {
                "chunk_id": chunk_id,
                "updated_analysis": analysis,
                "success": True
            }
            
        except Exception as e:
            print(f"❌ Error reanalyzing chunk {chunk_id}: {e}")
            return {"error": str(e), "chunk_id": chunk_id}

    def get_document_analysis(self, document_id: int) -> Dict[str, Any]:
        """
        Get analysis results for a document
        
        Args:
            document_id (int): Document ID
        
        Returns:
            Dict[str, Any]: Document analysis data
        
        Example:
            analysis = service.get_document_analysis(123)
        """
        try:
            document = self.db.query(Document).filter(Document.id == document_id).first()
            if not document:
                return {"error": "Document not found"}
            
            # Get chunks with analysis
            chunks_data = []
            for chunk in document.chunks:
                chunk_data = {
                    "id": chunk.id,
                    "chunk_index": chunk.chunk_ix,
                    "text_preview": chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text,
                    "intent_label": chunk.intent_label,
                    "summary": chunk.summary,
                    "heading": chunk.heading,
                    "subheading": chunk.subheading,
                    "key_values": json.loads(chunk.key_values) if chunk.key_values else {},
                    "relationships": json.loads(chunk.triples) if chunk.triples else []
                }
                chunks_data.append(chunk_data)
            
            # Count intents
            intent_counts = {}
            for chunk in document.chunks:
                intent = chunk.intent_label or "unknown"
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
            
            # Get document outline from headings
            outline = self._extract_document_outline(document.chunks)
            
            analysis_summary = {
                "document_info": {
                    "id": document.id,
                    "title": document.title,
                    "version": document.version,
                    "status": document.status,
                    "total_chunks": len(document.chunks)
                },
                "analysis_stats": {
                    "analyzed_chunks": sum(1 for c in document.chunks if c.intent_label),
                    "intent_distribution": intent_counts,
                    "has_embeddings": len(document.vector_indexes) > 0
                },
                "document_outline": outline,
                "chunks": chunks_data
            }
            
            return analysis_summary
            
        except Exception as e:
            print(f"❌ Error getting document analysis: {e}")
            return {"error": str(e)}

    def search_document_chunks(self, document_id: int, query: str, 
                             intent_filter: str = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search document chunks using semantic similarity
        
        Args:
            document_id (int): Document ID to search
            query (str): Search query
            intent_filter (str, optional): Filter by intent label
            top_k (int): Number of results to return
        
        Returns:
            List[Dict[str, Any]]: Search results
        
        Example:
            results = service.search_document_chunks(123, "authentication", "requirements")
        """
        try:
            # Use embedding service for semantic search
            search_results = self.embedding_service.search_document(document_id, query, top_k * 2)
            
            if not search_results:
                return []
            
            # Get chunk details from database
            chunk_indices = [r["chunk_index"] for r in search_results]
            chunks = self.db.query(Chunk).filter(
                Chunk.document_id == document_id,
                Chunk.chunk_ix.in_(chunk_indices)
            ).all()
            
            # Create lookup for chunks by index
            chunk_lookup = {chunk.chunk_ix: chunk for chunk in chunks}
            
            # Combine search results with chunk data
            enhanced_results = []
            for result in search_results:
                chunk_idx = result["chunk_index"]
                chunk = chunk_lookup.get(chunk_idx)
                
                if chunk:
                    # Apply intent filter if specified
                    if intent_filter and chunk.intent_label != intent_filter:
                        continue
                    
                    enhanced_result = {
                        "chunk_id": chunk.id,
                        "chunk_index": chunk.chunk_ix,
                        "similarity_score": result["similarity_score"],
                        "text": chunk.text,
                        "intent_label": chunk.intent_label,
                        "summary": chunk.summary,
                        "heading": chunk.heading,
                        "subheading": chunk.subheading
                    }
                    enhanced_results.append(enhanced_result)
                    
                    if len(enhanced_results) >= top_k:
                        break
            
            return enhanced_results
            
        except Exception as e:
            print(f"❌ Error searching document chunks: {e}")
            return []

    def get_analysis_statistics(self) -> Dict[str, Any]:
        """
        Get overall analysis statistics across all documents
        
        Returns:
            Dict[str, Any]: Analysis statistics
        
        Example:
            stats = service.get_analysis_statistics()
        """
        try:
            # Document counts by status
            status_counts = {}
            documents = self.db.query(Document).all()
            for doc in documents:
                status_counts[doc.status] = status_counts.get(doc.status, 0) + 1
            
            # Chunk statistics
            total_chunks = self.db.query(Chunk).count()
            analyzed_chunks = self.db.query(Chunk).filter(Chunk.intent_label.isnot(None)).count()
            
            # Intent distribution across all chunks
            intent_counts = {}
            chunks = self.db.query(Chunk).filter(Chunk.intent_label.isnot(None)).all()
            for chunk in chunks:
                intent = chunk.intent_label
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
            
            # Vector index statistics
            vector_indexes = self.db.query(VectorIndex).count()
            
            statistics = {
                "documents": {
                    "total": len(documents),
                    "by_status": status_counts,
                    "with_analysis": sum(1 for d in documents if d.chunks and any(c.intent_label for c in d.chunks))
                },
                "chunks": {
                    "total": total_chunks,
                    "analyzed": analyzed_chunks,
                    "analysis_rate": round(analyzed_chunks / max(total_chunks, 1) * 100, 1)
                },
                "intents": {
                    "distribution": intent_counts,
                    "unique_intents": len(intent_counts)
                },
                "indexes": {
                    "vector_indexes": vector_indexes
                }
            }
            
            return statistics
            
        except Exception as e:
            print(f"❌ Error getting analysis statistics: {e}")
            return {"error": str(e)}

    def _get_document_content(self, document: Document) -> Optional[str]:
        """Get document content from file"""
        try:
            if not document.files:
                return None
            
            file_path = document.files[0].path
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"❌ Error reading document content: {e}")
            return None

    def _save_chunks_to_db(self, document_id: int, chunks: List[Dict], 
                          analyses: List[Dict], embeddings: Any):
        """Save chunks and their analyses to database"""
        try:
            # Delete existing chunks for this document
            self.db.query(Chunk).filter(Chunk.document_id == document_id).delete()
            
            # Save new chunks
            for i, (chunk, analysis) in enumerate(zip(chunks, analyses)):
                chunk_record = Chunk(
                    document_id=document_id,
                    chunk_ix=i,
                    text=chunk["text"],
                    token_start=chunk.get("start", 0),
                    token_end=chunk.get("end", 0),
                    heading=analysis.get("heading"),
                    subheading=analysis.get("subheading"),
                    intent_label=analysis.get("intent_label"),
                    summary=analysis.get("summary"),
                    key_values=json.dumps(analysis.get("key_values", {})),
                    triples=json.dumps(analysis.get("relationships", []))
                )
                self.db.add(chunk_record)
            
            self.db.commit()
            print(f"✅ Saved {len(chunks)} chunks to database")
            
        except Exception as e:
            print(f"❌ Error saving chunks: {e}")
            self.db.rollback()
            raise

    def _save_vector_index(self, document_id: int, index_path: str, dimension: int):
        """Save vector index metadata to database"""
        try:
            # Delete existing indexes for this document
            self.db.query(VectorIndex).filter(VectorIndex.document_id == document_id).delete()
            
            # Create new index record
            vector_index = VectorIndex(
                document_id=document_id,
                index_type="faiss:FlatIP",
                dim=dimension,
                path=index_path
            )
            self.db.add(vector_index)
            self.db.commit()
            
            print(f"✅ Vector index saved: {index_path}")
            
        except Exception as e:
            print(f"❌ Error saving vector index: {e}")
            self.db.rollback()
            raise

    def _count_chunk_intents(self, analyses: List[Dict]) -> Dict[str, int]:
        """Count occurrences of each intent label"""
        intent_counts = {}
        for analysis in analyses:
            intent = analysis.get("intent_label", "unknown")
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        return intent_counts

    def _extract_document_outline(self, chunks: List[Chunk]) -> List[Dict[str, Any]]:
        """Extract document outline from chunk headings"""
        outline = []
        current_section = None
        
        for chunk in sorted(chunks, key=lambda c: c.chunk_ix):
            if chunk.heading:
                # New section
                if current_section and current_section["heading"] != chunk.heading:
                    outline.append(current_section)
                
                current_section = {
                    "heading": chunk.heading,
                    "subheadings": [],
                    "chunk_start": chunk.chunk_ix,
                    "intent": chunk.intent_label
                }
                
                if chunk.subheading:
                    current_section["subheadings"].append(chunk.subheading)
            
            elif chunk.subheading and current_section:
                # Add subheading to current section
                if chunk.subheading not in current_section["subheadings"]:
                    current_section["subheadings"].append(chunk.subheading)
        
        # Add final section
        if current_section:
            outline.append(current_section)
        
        return outline

    def _fallback_chunk_analysis(self, chunk: Dict, index: int) -> Dict[str, Any]:
        """Fallback analysis when LLM fails"""
        return {
            "intent_label": "other",
            "summary": f"Text chunk {index} ({len(chunk['text'])} characters)",
            "heading": None,
            "subheading": None,
            "key_values": {},
            "relationships": [],
            "fallback": True
        }

if __name__ == "__main__":
    # Test analysis service
    import asyncio
    from database import SessionLocal, init_database
    from services.llm_service import LLMService
    from services.embedding_service import EmbeddingService
    from services.document_service import DocumentService
    from config import Config
    
    async def test_analysis_service():
        print("🧪 Testing Analysis Service...")
        
        # Initialize services
        init_database()
        db = SessionLocal()
        
        try:
            llm_service = LLMService(
                endpoint=Config.AZURE_OPENAI_ENDPOINT,
                api_key=Config.AZURE_OPENAI_API_KEY,
                api_version=Config.AZURE_OPENAI_API_VERSION,
                deployment=Config.AZURE_OPENAI_DEPLOYMENT
            )
            
            embedding_service = EmbeddingService(
                model_name=Config.SENTENCE_TRANSFORMER_MODEL
            )
            
            document_service = DocumentService(db)
            analysis_service = AnalysisService(db, llm_service, embedding_service)
            
            # Create test document
            test_content = """# System Requirements Document

## Introduction
This document outlines the requirements for the new customer portal system.

## Functional Requirements
The system must support:
- User authentication and authorization
- Real-time data synchronization
- Multi-language support

## Non-Functional Requirements
Performance requirements:
- Response time < 2 seconds
- 99.9% uptime
- Support 10,000 concurrent users

## Security Requirements
- Data encryption at rest and in transit
- Regular security audits
- Compliance with GDPR

## Conclusion
These requirements form the foundation for system development.
            """
            
            doc = document_service.create_document(
                title="System Requirements Test",
                content=test_content,
                metadata={"domain": "technical"}
            )
            
            print(f"✅ Created test document: {doc.id}")
            
            # Test analysis
            result = await analysis_service.analyze_document(doc.id)
            print(f"✅ Analysis result: {result.get('chunks_processed', 0)} chunks processed")
            
            # Test getting analysis
            analysis = analysis_service.get_document_analysis(doc.id)
            print(f"✅ Retrieved analysis: {len(analysis.get('chunks', []))} chunks")
            
            # Test search
            search_results = analysis_service.search_document_chunks(
                doc.id, "authentication requirements", top_k=3
            )
            print(f"✅ Search results: {len(search_results)} matches")
            
        finally:
            db.close()
    
    # Run test
    asyncio.run(test_analysis_service())
    print("✅ Analysis Service test completed!")