# services/comparison_service.py
"""
DocuReview Pro - Document Comparison Service
Advanced document version comparison with configurable algorithms
"""
import json
import difflib
import re
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session
from dataclasses import dataclass

from database import Document, Chunk, Comparison, DiffConfiguration
from services.llm_service import LLMService
from services.embedding_service import EmbeddingService
from utils.text_processing import normalize_text, split_into_sentences

@dataclass
class ComparisonConfig:
    """Configuration for document comparison"""
    granularity: str = "word"  # character|word|sentence|paragraph
    algorithm: str = "hybrid"  # syntactic|semantic|hybrid
    similarity_threshold: float = 0.8
    show_only_changes: bool = False
    color_scheme: str = "default"

class ComparisonService:
    """Service for document version comparison and analysis"""
    
    def __init__(self, db: Session, llm_service: LLMService, embedding_service: EmbeddingService):
        """
        Initialize comparison service
        
        Args:
            db (Session): Database session
            llm_service (LLMService): LLM service for AI analysis
            embedding_service (EmbeddingService): Embedding service for semantic analysis
        
        Example:
            service = ComparisonService(db, llm_service, embedding_service)
        """
        self.db = db
        self.llm_service = llm_service
        self.embedding_service = embedding_service

    async def compare_documents(self, doc_id_a: int, doc_id_b: int, 
                              config: ComparisonConfig = None) -> Dict[str, Any]:
        """
        Compare two document versions with configurable algorithms
        
        Args:
            doc_id_a (int): First document ID
            doc_id_b (int): Second document ID
            config (ComparisonConfig, optional): Comparison configuration
        
        Returns:
            Dict[str, Any]: Comprehensive comparison results
        
        Example:
            result = await service.compare_documents(123, 124)
            similarity_score = result["metrics"]["overall_similarity"]
        """
        start_time = datetime.utcnow()
        
        try:
            # Get documents
            doc_a = self.db.query(Document).filter(Document.id == doc_id_a).first()
            doc_b = self.db.query(Document).filter(Document.id == doc_id_b).first()
            
            if not doc_a or not doc_b:
                return {"error": "One or both documents not found"}
            
            # Use default config if not provided
            if not config:
                config = self._get_default_config()
            
            print(f"🔄 Comparing documents: {doc_a.title} v{doc_a.version} vs v{doc_b.version}")
            
            # Check if comparison already exists and is recent
            existing_comparison = self._get_cached_comparison(doc_a.slug, doc_a.version, doc_b.version)
            if existing_comparison:
                print("✅ Using cached comparison result")
                return self._format_comparison_result(existing_comparison)
            
            # Get document contents
            content_a = self._get_document_content(doc_a)
            content_b = self._get_document_content(doc_b)
            
            if not content_a or not content_b:
                return {"error": "Could not read document contents"}
            
            # Perform multi-level comparison
            comparison_result = {
                "document_info": {
                    "doc_a": {"id": doc_a.id, "title": doc_a.title, "version": doc_a.version},
                    "doc_b": {"id": doc_b.id, "title": doc_b.title, "version": doc_b.version},
                    "comparison_config": config.__dict__
                }
            }
            
            # 1. Text-level comparison
            text_diff = self._compute_text_diff(content_a, content_b, config)
            comparison_result["text_diff"] = text_diff
            
            # 2. Structural comparison
            structure_diff = self._compute_structure_diff(doc_a, doc_b)
            comparison_result["structure_diff"] = structure_diff
            
            # 3. Semantic comparison (if both documents have embeddings)
            semantic_diff = await self._compute_semantic_diff(doc_a, doc_b)
            comparison_result["semantic_diff"] = semantic_diff
            
            # 4. Intent comparison
            intent_diff = self._compute_intent_diff(doc_a, doc_b)
            comparison_result["intent_diff"] = intent_diff
            
            # 5. Calculate overall metrics
            metrics = self._calculate_comparison_metrics(
                text_diff, structure_diff, semantic_diff, intent_diff
            )
            comparison_result["metrics"] = metrics
            
            # 6. Generate AI summary
            ai_summary = await self._generate_comparison_summary(
                doc_a, doc_b, comparison_result
            )
            comparison_result["ai_summary"] = ai_summary
            
            # 7. Cache the comparison
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            comparison_result["processing_time_ms"] = round(processing_time, 2)
            
            self._cache_comparison(doc_a.slug, doc_a.version, doc_b.version, 
                                 comparison_result, processing_time)
            
            print(f"✅ Comparison completed in {processing_time:.0f}ms")
            return comparison_result
            
        except Exception as e:
            print(f"❌ Comparison failed: {e}")
            return {"error": str(e)}

    def _compute_text_diff(self, content_a: str, content_b: str, 
                          config: ComparisonConfig) -> Dict[str, Any]:
        """
        Compute text-level differences between documents
        
        Args:
            content_a (str): First document content
            content_b (str): Second document content
            config (ComparisonConfig): Comparison configuration
        
        Returns:
            Dict[str, Any]: Text difference analysis
        """
        try:
            # Normalize content based on granularity
            if config.granularity == "character":
                units_a = list(content_a)
                units_b = list(content_b)
            elif config.granularity == "word":
                units_a = content_a.split()
                units_b = content_b.split()
            elif config.granularity == "sentence":
                units_a = split_into_sentences(content_a)
                units_b = split_into_sentences(content_b)
            elif config.granularity == "paragraph":
                units_a = [p.strip() for p in content_a.split('\n\n') if p.strip()]
                units_b = [p.strip() for p in content_b.split('\n\n') if p.strip()]
            else:
                # Default to word level
                units_a = content_a.split()
                units_b = content_b.split()
            
            # Compute diff operations
            matcher = difflib.SequenceMatcher(None, units_a, units_b)
            diff_ops = []
            
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == 'equal':
                    continue
                
                operation = {
                    "operation": tag,
                    "a_start": i1,
                    "a_end": i2,
                    "b_start": j1,
                    "b_end": j2,
                    "a_content": units_a[i1:i2] if tag != 'insert' else [],
                    "b_content": units_b[j1:j2] if tag != 'delete' else []
                }
                diff_ops.append(operation)
            
            # Calculate statistics
            total_a = len(units_a)
            total_b = len(units_b)
            
            # Count changes
            added_count = sum(len(op["b_content"]) for op in diff_ops if op["operation"] == "insert")
            deleted_count = sum(len(op["a_content"]) for op in diff_ops if op["operation"] == "delete")
            modified_count = sum(max(len(op["a_content"]), len(op["b_content"])) 
                               for op in diff_ops if op["operation"] == "replace")
            
            # Calculate similarity ratio
            similarity = matcher.ratio()
            
            text_diff_result = {
                "granularity": config.granularity,
                "algorithm": "syntactic",
                "operations": diff_ops,
                "statistics": {
                    "total_a": total_a,
                    "total_b": total_b,
                    "added": added_count,
                    "deleted": deleted_count,
                    "modified": modified_count,
                    "unchanged": total_a - deleted_count - modified_count,
                    "similarity_ratio": round(similarity, 3),
                    "change_percentage": round((1 - similarity) * 100, 1)
                }
            }
            
            return text_diff_result
            
        except Exception as e:
            print(f"❌ Error in text diff: {e}")
            return {"error": str(e)}

    def _compute_structure_diff(self, doc_a: Document, doc_b: Document) -> Dict[str, Any]:
        """
        Compare document structure (headings, sections, organization)
        
        Args:
            doc_a (Document): First document
            doc_b (Document): Second document
        
        Returns:
            Dict[str, Any]: Structural difference analysis
        """
        try:
            # Extract headings from chunks
            headings_a = []
            headings_b = []
            
            for chunk in sorted(doc_a.chunks, key=lambda c: c.chunk_ix):
                if chunk.heading:
                    headings_a.append({
                        "text": chunk.heading,
                        "level": 1 if chunk.heading.isupper() else 2,
                        "position": chunk.chunk_ix,
                        "subheading": chunk.subheading
                    })
            
            for chunk in sorted(doc_b.chunks, key=lambda c: c.chunk_ix):
                if chunk.heading:
                    headings_b.append({
                        "text": chunk.heading,
                        "level": 1 if chunk.heading.isupper() else 2,
                        "position": chunk.chunk_ix,
                        "subheading": chunk.subheading
                    })
            
            # Compare heading structures
            heading_texts_a = [h["text"] for h in headings_a]
            heading_texts_b = [h["text"] for h in headings_b]
            
            matcher = difflib.SequenceMatcher(None, heading_texts_a, heading_texts_b)
            
            # Find added, removed, and moved headings
            added_headings = []
            removed_headings = []
            moved_headings = []
            unchanged_headings = []
            
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == 'insert':
                    added_headings.extend(headings_b[j1:j2])
                elif tag == 'delete':
                    removed_headings.extend(headings_a[i1:i2])
                elif tag == 'replace':
                    removed_headings.extend(headings_a[i1:i2])
                    added_headings.extend(headings_b[j1:j2])
                elif tag == 'equal':
                    unchanged_headings.extend(headings_a[i1:i2])
            
            # Calculate structural similarity
            total_headings = max(len(headings_a), len(headings_b), 1)
            structural_similarity = len(unchanged_headings) / total_headings
            
            structure_diff_result = {
                "headings_a": headings_a,
                "headings_b": headings_b,
                "changes": {
                    "added": added_headings,
                    "removed": removed_headings,
                    "moved": moved_headings,
                    "unchanged": unchanged_headings
                },
                "statistics": {
                    "total_headings_a": len(headings_a),
                    "total_headings_b": len(headings_b),
                    "structural_similarity": round(structural_similarity, 3),
                    "headings_added": len(added_headings),
                    "headings_removed": len(removed_headings),
                    "headings_unchanged": len(unchanged_headings)
                }
            }
            
            return structure_diff_result
            
        except Exception as e:
            print(f"❌ Error in structure diff: {e}")
            return {"error": str(e)}

    async def _compute_semantic_diff(self, doc_a: Document, doc_b: Document) -> Dict[str, Any]:
        """
        Compare documents using semantic similarity (embeddings)
        
        Args:
            doc_a (Document): First document
            doc_b (Document): Second document
        
        Returns:
            Dict[str, Any]: Semantic difference analysis
        """
        try:
            # Check if both documents have embeddings
            if not doc_a.vector_indexes or not doc_b.vector_indexes:
                return {"warning": "One or both documents lack vector embeddings"}
            
            # Get embeddings for both documents
            embeddings_a = self.embedding_service.get_chunk_embeddings(doc_a.id)
            embeddings_b = self.embedding_service.get_chunk_embeddings(doc_b.id)
            
            if embeddings_a is None or embeddings_b is None:
                return {"warning": "Could not load embeddings"}
            
            # Compare embeddings
            similarity_metrics = self.embedding_service.compare_embeddings(embeddings_a, embeddings_b)
            
            # Align chunks based on semantic similarity
            chunk_alignments = self._align_chunks_semantically(doc_a.chunks, doc_b.chunks, 
                                                             embeddings_a, embeddings_b)
            
            # Identify semantically similar and different chunks
            semantic_changes = {
                "highly_similar": [],    # >0.9 similarity
                "moderately_similar": [], # 0.7-0.9 similarity
                "different": [],         # <0.7 similarity
                "unmatched_a": [],       # Chunks in A with no good match in B
                "unmatched_b": []        # Chunks in B with no good match in A
            }
            
            for alignment in chunk_alignments:
                similarity = alignment["similarity"]
                if similarity > 0.9:
                    semantic_changes["highly_similar"].append(alignment)
                elif similarity > 0.7:
                    semantic_changes["moderately_similar"].append(alignment)
                else:
                    semantic_changes["different"].append(alignment)
            
            semantic_diff_result = {
                "similarity_metrics": similarity_metrics,
                "chunk_alignments": chunk_alignments,
                "semantic_changes": semantic_changes,
                "statistics": {
                    "chunks_a": len(doc_a.chunks),
                    "chunks_b": len(doc_b.chunks),
                    "aligned_pairs": len(chunk_alignments),
                    "avg_similarity": similarity_metrics.get("overall_similarity", 0),
                    "semantic_similarity_score": round(similarity_metrics.get("overall_similarity", 0), 3)
                }
            }
            
            return semantic_diff_result
            
        except Exception as e:
            print(f"❌ Error in semantic diff: {e}")
            return {"error": str(e)}

    def _compute_intent_diff(self, doc_a: Document, doc_b: Document) -> Dict[str, Any]:
        """
        Compare documents based on intent labels and purpose
        
        Args:
            doc_a (Document): First document
            doc_b (Document): Second document
        
        Returns:
            Dict[str, Any]: Intent difference analysis
        """
        try:
            # Extract intent distributions
            intents_a = {}
            intents_b = {}
            
            for chunk in doc_a.chunks:
                intent = chunk.intent_label or "unknown"
                intents_a[intent] = intents_a.get(intent, 0) + 1
            
            for chunk in doc_b.chunks:
                intent = chunk.intent_label or "unknown"
                intents_b[intent] = intents_b.get(intent, 0) + 1
            
            # Calculate intent changes
            all_intents = set(intents_a.keys()) | set(intents_b.keys())
            intent_changes = {}
            
            for intent in all_intents:
                count_a = intents_a.get(intent, 0)
                count_b = intents_b.get(intent, 0)
                change = count_b - count_a
                
                intent_changes[intent] = {
                    "count_a": count_a,
                    "count_b": count_b,
                    "change": change,
                    "change_type": "added" if count_a == 0 else "removed" if count_b == 0 else "modified"
                }
            
            # Calculate intent similarity
            total_chunks_a = sum(intents_a.values())
            total_chunks_b = sum(intents_b.values())
            
            intent_similarity = 0.0
            if total_chunks_a > 0 and total_chunks_b > 0:
                # Calculate weighted similarity based on intent proportions
                similarity_sum = 0.0
                for intent in all_intents:
                    prop_a = intents_a.get(intent, 0) / total_chunks_a
                    prop_b = intents_b.get(intent, 0) / total_chunks_b
                    similarity_sum += min(prop_a, prop_b)
                intent_similarity = similarity_sum
            
            intent_diff_result = {
                "intent_distribution_a": intents_a,
                "intent_distribution_b": intents_b,
                "intent_changes": intent_changes,
                "statistics": {
                    "total_chunks_a": total_chunks_a,
                    "total_chunks_b": total_chunks_b,
                    "unique_intents_a": len(intents_a),
                    "unique_intents_b": len(intents_b),
                    "intent_similarity": round(intent_similarity, 3),
                    "major_intent_shifts": sum(1 for change in intent_changes.values() 
                                             if abs(change["change"]) > 2)
                }
            }
            
            return intent_diff_result
            
        except Exception as e:
            print(f"❌ Error in intent diff: {e}")
            return {"error": str(e)}

    def _align_chunks_semantically(self, chunks_a: List[Chunk], chunks_b: List[Chunk],
                                 embeddings_a, embeddings_b) -> List[Dict[str, Any]]:
        """Align chunks from two documents based on semantic similarity"""
        try:
            import numpy as np
            
            # Compute pairwise similarities
            similarities = np.dot(embeddings_a, embeddings_b.T)
            
            alignments = []
            used_b = set()
            
            # For each chunk in A, find best match in B
            for i, chunk_a in enumerate(sorted(chunks_a, key=lambda c: c.chunk_ix)):
                best_similarity = -1
                best_j = -1
                
                for j in range(len(chunks_b)):
                    if j not in used_b and similarities[i, j] > best_similarity:
                        best_similarity = similarities[i, j]
                        best_j = j
                
                if best_j >= 0 and best_similarity > 0.5:  # Minimum threshold
                    chunk_b = sorted(chunks_b, key=lambda c: c.chunk_ix)[best_j]
                    used_b.add(best_j)
                    
                    alignment = {
                        "chunk_a_id": chunk_a.id,
                        "chunk_b_id": chunk_b.id,
                        "chunk_a_index": chunk_a.chunk_ix,
                        "chunk_b_index": chunk_b.chunk_ix,
                        "similarity": float(best_similarity),
                        "chunk_a_preview": chunk_a.text[:100] + "..." if len(chunk_a.text) > 100 else chunk_a.text,
                        "chunk_b_preview": chunk_b.text[:100] + "..." if len(chunk_b.text) > 100 else chunk_b.text
                    }
                    alignments.append(alignment)
            
            return alignments
            
        except Exception as e:
            print(f"❌ Error aligning chunks: {e}")
            return []

    def _calculate_comparison_metrics(self, text_diff: Dict, structure_diff: Dict,
                                    semantic_diff: Dict, intent_diff: Dict) -> Dict[str, float]:
        """Calculate overall comparison metrics"""
        try:
            # Text similarity
            text_similarity = text_diff.get("statistics", {}).get("similarity_ratio", 0.0)
            
            # Structural similarity
            structural_similarity = structure_diff.get("statistics", {}).get("structural_similarity", 0.0)
            
            # Semantic similarity
            semantic_similarity = semantic_diff.get("statistics", {}).get("semantic_similarity_score", 0.0)
            
            # Intent similarity
            intent_similarity = intent_diff.get("statistics", {}).get("intent_similarity", 0.0)
            
            # Calculate weighted overall similarity
            weights = {"text": 0.4, "structure": 0.2, "semantic": 0.3, "intent": 0.1}
            
            overall_similarity = (
                text_similarity * weights["text"] +
                structural_similarity * weights["structure"] +
                semantic_similarity * weights["semantic"] +
                intent_similarity * weights["intent"]
            )
            
            # Calculate change intensity (inverse of similarity)
            change_intensity = 1.0 - overall_similarity
            
            metrics = {
                "overall_similarity": round(overall_similarity, 3),
                "change_intensity": round(change_intensity, 3),
                "text_similarity": round(text_similarity, 3),
                "structural_similarity": round(structural_similarity, 3),
                "semantic_similarity": round(semantic_similarity, 3),
                "intent_similarity": round(intent_similarity, 3),
                "change_significance": self._classify_change_significance(change_intensity)
            }
            
            return metrics
            
        except Exception as e:
            print(f"❌ Error calculating metrics: {e}")
            return {"error": str(e)}

    def _classify_change_significance(self, change_intensity: float) -> str:
        """Classify the significance of changes"""
        if change_intensity < 0.1:
            return "minimal"
        elif change_intensity < 0.3:
            return "minor"
        elif change_intensity < 0.6:
            return "moderate"
        elif change_intensity < 0.8:
            return "major"
        else:
            return "extensive"

    async def _generate_comparison_summary(self, doc_a: Document, doc_b: Document, 
                                         comparison_result: Dict) -> Dict[str, Any]:
        """Generate AI-powered comparison summary"""
        try:
            # Extract key metrics and changes
            metrics = comparison_result.get("metrics", {})
            text_diff = comparison_result.get("text_diff", {})
            structure_diff = comparison_result.get("structure_diff", {})
            intent_diff = comparison_result.get("intent_diff", {})
            
            # Prepare change data for LLM
            change_data = {
                "text_changes": text_diff.get("statistics", {}),
                "structural_changes": structure_diff.get("changes", {}),
                "intent_changes": intent_diff.get("intent_changes", {}),
                "overall_metrics": metrics
            }
            
            # Generate summary using LLM
            summary = await self.llm_service.summarize_comparison(
                document_title=doc_a.title,
                version_a=doc_a.version,
                version_b=doc_b.version,
                change_data=change_data,
                metrics=metrics
            )
            
            return summary
            
        except Exception as e:
            print(f"❌ Error generating comparison summary: {e}")
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

    def _get_default_config(self) -> ComparisonConfig:
        """Get default comparison configuration"""
        try:
            default_config = self.db.query(DiffConfiguration).filter(
                DiffConfiguration.is_default == 'true'
            ).first()
            
            if default_config:
                return ComparisonConfig(
                    granularity=default_config.granularity,
                    algorithm=default_config.algorithm,
                    similarity_threshold=default_config.similarity_threshold,
                    show_only_changes=default_config.show_only_changes == 'true',
                    color_scheme=default_config.color_scheme
                )
            else:
                return ComparisonConfig()
                
        except Exception as e:
            print(f"⚠️  Could not load default config: {e}")
            return ComparisonConfig()

    def _get_cached_comparison(self, doc_slug: str, version_a: int, version_b: int) -> Optional[Comparison]:
        """Get cached comparison if it exists and is recent"""
        try:
            comparison = self.db.query(Comparison).filter(
                Comparison.doc_slug == doc_slug,
                Comparison.version_a == version_a,
                Comparison.version_b == version_b
            ).first()
            
            # Check if comparison is recent (within last hour)
            if comparison:
                age_hours = (datetime.utcnow() - comparison.created_at).total_seconds() / 3600
                if age_hours < 1.0:  # Use cached result if less than 1 hour old
                    return comparison
            
            return None
            
        except Exception as e:
            print(f"❌ Error checking cached comparison: {e}")
            return None

    def _cache_comparison(self, doc_slug: str, version_a: int, version_b: int,
                         comparison_result: Dict, processing_time_ms: float):
        """Cache comparison result"""
        try:
            # Delete existing comparison for these versions
            self.db.query(Comparison).filter(
                Comparison.doc_slug == doc_slug,
                Comparison.version_a == version_a,
                Comparison.version_b == version_b
            ).delete()
            
            # Create new comparison record
            comparison = Comparison(
                doc_slug=doc_slug,
                version_a=version_a,
                version_b=version_b,
                text_diff_json=json.dumps(comparison_result.get("text_diff", {})),
                section_map_json=json.dumps(comparison_result.get("structure_diff", {})),
                metrics_json=json.dumps(comparison_result.get("metrics", {})),
                llm_summary=json.dumps(comparison_result.get("ai_summary", {})),
                processing_time_ms=processing_time_ms,
                similarity_score=comparison_result.get("metrics", {}).get("overall_similarity", 0.0),
                change_score=comparison_result.get("metrics", {}).get("change_intensity", 0.0)
            )
            
            self.db.add(comparison)
            self.db.commit()
            
            print(f"✅ Comparison cached for {doc_slug} v{version_a} vs v{version_b}")
            
        except Exception as e:
            print(f"❌ Error caching comparison: {e}")
            self.db.rollback()

    def _format_comparison_result(self, comparison: Comparison) -> Dict[str, Any]:
        """Format cached comparison for API response"""
        try:
            return {
                "document_info": {
                    "doc_slug": comparison.doc_slug,
                    "version_a": comparison.version_a,
                    "version_b": comparison.version_b,
                    "comparison_date": comparison.created_at,
                    "cached": True
                },
                "text_diff": json.loads(comparison.text_diff_json) if comparison.text_diff_json else {},
                "structure_diff": json.loads(comparison.section_map_json) if comparison.section_map_json else {},
                "metrics": json.loads(comparison.metrics_json) if comparison.metrics_json else {},
                "ai_summary": json.loads(comparison.llm_summary) if comparison.llm_summary else {},
                "processing_time_ms": comparison.processing_time_ms
            }
        except Exception as e:
            print(f"❌ Error formatting comparison result: {e}")
            return {"error": str(e)}

if __name__ == "__main__":
    # Test comparison service
    import asyncio
    from database import SessionLocal, init_database
    from services.llm_service import LLMService
    from services.embedding_service import EmbeddingService
    from services.document_service import DocumentService
    from config import Config
    
    async def test_comparison_service():
        print("🧪 Testing Comparison Service...")
        
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
            comparison_service = ComparisonService(db, llm_service, embedding_service)
            
            # Create test documents
            content_v1 = """# API Documentation v1
            
## Authentication
Users must authenticate using API keys.

## Endpoints
- GET /users - List users
- POST /users - Create user
            """
            
            content_v2 = """# API Documentation v2
            
## Authentication  
Users must authenticate using OAuth 2.0 tokens.

## Endpoints
- GET /users - List all users with pagination
- POST /users - Create new user
- PUT /users/:id - Update user
- DELETE /users/:id - Delete user

## Rate Limiting
API calls are limited to 1000 requests per hour.
            """
            
            doc_v1 = document_service.create_document(
                title="API Documentation", content=content_v1, 
                metadata={"version_note": "Initial version"}
            )
            
            doc_v2 = document_service.create_document(
                title="API Documentation", content=content_v2,
                metadata={"version_note": "Added OAuth and rate limiting"}
            )
            
            print(f"✅ Created test documents: v{doc_v1.version} and v{doc_v2.version}")
            
            # Test comparison
            result = await comparison_service.compare_documents(doc_v1.id, doc_v2.id)
            
            if "error" not in result:
                metrics = result.get("metrics", {})
                print(f"✅ Comparison completed:")
                print(f"  Overall similarity: {metrics.get('overall_similarity', 0):.2f}")
                print(f"  Change significance: {metrics.get('change_significance', 'unknown')}")
                print(f"  Processing time: {result.get('processing_time_ms', 0):.0f}ms")
            else:
                print(f"❌ Comparison failed: {result['error']}")
            
        finally:
            db.close()
    
    # Run test
    asyncio.run(test_comparison_service())
    print("✅ Comparison Service test completed!")