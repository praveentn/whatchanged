# services/search_service.py
"""
DocuReview Pro - Search Service (FIXED)
Enhanced search functionality with proper result handling and debugging
"""
import asyncio
import time
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, text

from database import Document, Chunk, VectorIndex
from services.embedding_service import EmbeddingService

class SearchService:
    """Enhanced search service with proper result handling and debugging"""
    
    def __init__(self, db: Session, embedding_service: EmbeddingService = None):
        self.db = db
        self.embedding_service = embedding_service

    async def semantic_search(self, query: str, document_slug: str = None, 
                            intent_filter: str = None, top_k: int = 10,
                            similarity_threshold: float = 0.5) -> Dict[str, Any]:
        """
        Perform semantic search with proper result handling - FIXED
        
        Args:
            query (str): Search query
            document_slug (str, optional): Specific document to search
            intent_filter (str, optional): Filter by intent label
            top_k (int): Number of results to return
            similarity_threshold (float): Minimum similarity score
            
        Returns:
            Dict[str, Any]: Search results with metadata
        """
        try:
            start_time = time.time()
            results = []
            
            print(f"🔍 Starting semantic search for: '{query}'")
            print(f"   Document slug: {document_slug}")
            print(f"   Intent filter: {intent_filter}")
            print(f"   Top K: {top_k}")
            
            # First, let's check if we have any data in the database
            total_docs = self.db.query(Document).count()
            total_chunks = self.db.query(Chunk).count()
            indexed_docs = self.db.query(Document).filter(Document.status == 'indexed').count()
            
            print(f"📊 Database stats: {total_docs} docs, {total_chunks} chunks, {indexed_docs} indexed")
            
            if total_chunks == 0:
                return {
                    "query": query,
                    "search_type": "semantic",
                    "total_results": 0,
                    "processing_time_ms": (time.time() - start_time) * 1000,
                    "results": [],
                    "suggestions": [],
                    "debug_info": "No chunks found in database"
                }
            
            # Build base query for chunks with proper joins
            base_query = self.db.query(
                Chunk.id,
                Chunk.document_id,
                Chunk.chunk_ix,
                Chunk.text,
                Chunk.summary,
                Chunk.intent_label,
                Chunk.heading,
                Chunk.subheading,
                Document.title,
                Document.version,
                Document.slug
            ).join(Document, Chunk.document_id == Document.id)
            
            # Apply filters
            filters = []
            if document_slug:
                filters.append(Document.slug == document_slug)
                print(f"   Filtering by document slug: {document_slug}")
            
            if intent_filter:
                filters.append(Chunk.intent_label == intent_filter)
                print(f"   Filtering by intent: {intent_filter}")
            
            if filters:
                base_query = base_query.filter(and_(*filters))
            
            # Get all matching chunks first
            all_chunks = base_query.all()
            print(f"📋 Found {len(all_chunks)} chunks matching filters")
            
            if not all_chunks:
                return {
                    "query": query,
                    "search_type": "semantic",
                    "total_results": 0,
                    "processing_time_ms": (time.time() - start_time) * 1000,
                    "results": [],
                    "suggestions": self._generate_search_suggestions(query),
                    "debug_info": f"No chunks found after applying filters (doc_slug={document_slug}, intent={intent_filter})"
                }
            
            # For semantic search, try to use embeddings if available
            if self.embedding_service:
                print("🧠 Attempting semantic search with embeddings...")
                semantic_results = await self._perform_semantic_search(query, all_chunks, top_k, similarity_threshold)
                if semantic_results:
                    results = semantic_results
                    print(f"✅ Found {len(results)} semantic results")
                else:
                    print("⚠️ Semantic search returned no results, falling back to keyword search")
            
            # If no semantic results, fall back to keyword search
            if not results:
                print("🔤 Performing keyword search...")
                results = self._perform_keyword_search(query, all_chunks, top_k)
                print(f"📝 Found {len(results)} keyword results")
            
            # Format results
            formatted_results = []
            for result in results[:top_k]:
                formatted_result = {
                    "chunk_id": result["chunk_id"],
                    "document_id": result["document_id"],
                    "document_title": result["document_title"],
                    "document_version": result["document_version"],
                    "chunk_index": result["chunk_index"],
                    "similarity_score": result["similarity_score"],
                    "text_preview": result["text_preview"],
                    "full_text": result.get("full_text"),
                    "intent_label": result.get("intent_label"),
                    "heading": result.get("heading"),
                    "subheading": result.get("subheading"),
                    "summary": result.get("summary")
                }
                formatted_results.append(formatted_result)
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            return {
                "query": query,
                "search_type": "semantic" if self.embedding_service and results else "keyword",
                "total_results": len(formatted_results),
                "processing_time_ms": round(processing_time_ms, 2),
                "results": formatted_results,
                "suggestions": self._generate_search_suggestions(query) if not formatted_results else None
            }
            
        except Exception as e:
            print(f"❌ Error in semantic search: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "query": query,
                "search_type": "error",
                "total_results": 0,
                "processing_time_ms": 0,
                "results": [],
                "error": str(e),
                "debug_info": f"Search failed with error: {e}"
            }

    async def _perform_semantic_search(self, query: str, chunks: List, top_k: int, 
                                     similarity_threshold: float) -> List[Dict[str, Any]]:
        """Perform semantic search using embeddings"""
        try:
            if not self.embedding_service:
                return []
            
            # Extract texts and generate query embedding
            chunk_texts = [chunk.text for chunk in chunks]
            query_embedding = self.embedding_service.embed_texts([query])
            
            if query_embedding.shape[0] == 0:
                print("⚠️ Failed to generate query embedding")
                return []
            
            # Generate embeddings for all chunk texts
            chunk_embeddings = self.embedding_service.embed_texts(chunk_texts)
            
            if chunk_embeddings.shape[0] == 0:
                print("⚠️ Failed to generate chunk embeddings")
                return []
            
            # Calculate similarities
            similarities = chunk_embeddings @ query_embedding.T
            similarities = similarities.flatten()
            
            # Create results with similarity scores
            results = []
            for i, (chunk, similarity) in enumerate(zip(chunks, similarities)):
                if similarity >= similarity_threshold:
                    result = {
                        "chunk_id": chunk.id,
                        "document_id": chunk.document_id,
                        "document_title": chunk.title,
                        "document_version": chunk.version,
                        "chunk_index": chunk.chunk_ix,
                        "similarity_score": float(similarity),
                        "text_preview": self._create_text_preview(chunk.text, query),
                        "full_text": chunk.text,
                        "intent_label": chunk.intent_label,
                        "heading": chunk.heading,
                        "subheading": chunk.subheading,
                        "summary": chunk.summary
                    }
                    results.append(result)
            
            # Sort by similarity score (descending)
            results.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            print(f"🎯 Semantic search found {len(results)} results above threshold {similarity_threshold}")
            return results[:top_k]
            
        except Exception as e:
            print(f"❌ Error in semantic search: {e}")
            return []

    def _perform_keyword_search(self, query: str, chunks: List, top_k: int) -> List[Dict[str, Any]]:
        """Perform keyword-based search as fallback"""
        try:
            query_lower = query.lower().strip()
            query_words = query_lower.split()
            
            results = []
            
            for chunk in chunks:
                # Calculate keyword match score
                text_lower = chunk.text.lower()
                summary_lower = (chunk.summary or "").lower()
                
                # Count word matches
                word_matches = 0
                total_words = len(query_words)
                
                for word in query_words:
                    if word in text_lower:
                        word_matches += 1
                
                # Calculate score based on word matches and text length
                if word_matches > 0:
                    base_score = word_matches / total_words
                    
                    # Boost score if summary also contains matches
                    summary_matches = sum(1 for word in query_words if word in summary_lower)
                    if summary_matches > 0:
                        base_score += 0.1 * (summary_matches / total_words)
                    
                    # Boost score for exact phrase matches
                    if query_lower in text_lower:
                        base_score += 0.3
                    
                    # Normalize score to 0-1 range
                    similarity_score = min(1.0, base_score)
                    
                    result = {
                        "chunk_id": chunk.id,
                        "document_id": chunk.document_id,
                        "document_title": chunk.title,
                        "document_version": chunk.version,
                        "chunk_index": chunk.chunk_ix,
                        "similarity_score": similarity_score,
                        "text_preview": self._create_text_preview(chunk.text, query),
                        "full_text": chunk.text,
                        "intent_label": chunk.intent_label,
                        "heading": chunk.heading,
                        "subheading": chunk.subheading,
                        "summary": chunk.summary
                    }
                    results.append(result)
            
            # Sort by similarity score (descending)
            results.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            print(f"🔤 Keyword search found {len(results)} results")
            return results[:top_k]
            
        except Exception as e:
            print(f"❌ Error in keyword search: {e}")
            return []

    def _create_text_preview(self, text: str, query: str, max_length: int = 200) -> str:
        """Create a text preview highlighting query terms"""
        try:
            query_words = query.lower().split()
            text_lower = text.lower()
            
            # Find the best position to start the preview
            best_pos = 0
            best_score = 0
            
            # Look for positions that contain query words
            for word in query_words:
                pos = text_lower.find(word)
                if pos >= 0:
                    # Count nearby query words
                    start = max(0, pos - 50)
                    end = min(len(text), pos + 50)
                    snippet = text_lower[start:end]
                    
                    score = sum(1 for w in query_words if w in snippet)
                    if score > best_score:
                        best_score = score
                        best_pos = max(0, pos - 50)
            
            # Create preview
            preview_start = best_pos
            preview_end = min(len(text), preview_start + max_length)
            preview = text[preview_start:preview_end]
            
            # Add ellipsis if truncated
            if preview_start > 0:
                preview = "..." + preview
            if preview_end < len(text):
                preview = preview + "..."
            
            return preview.strip()
            
        except Exception as e:
            print(f"⚠️ Error creating text preview: {e}")
            return text[:max_length] + "..." if len(text) > max_length else text

    async def global_search(self, query: str, search_scope: str = "all", 
                          filters: Dict[str, Any] = None, top_k: int = 20) -> Dict[str, Any]:
        """
        Perform global search across all documents - FIXED
        
        Args:
            query (str): Search query
            search_scope (str): Search scope (all, titles, content, summaries)
            filters (Dict[str, Any]): Additional filters
            top_k (int): Number of results to return
            
        Returns:
            Dict[str, Any]: Global search results
        """
        try:
            start_time = time.time()
            
            print(f"🌐 Starting global search for: '{query}' (scope: {search_scope})")
            
            # Check database state
            total_docs = self.db.query(Document).count()
            total_chunks = self.db.query(Chunk).count()
            
            print(f"📊 Database stats: {total_docs} docs, {total_chunks} chunks")
            
            if total_chunks == 0:
                return {
                    "query": query,
                    "search_type": "global",
                    "total_results": 0,
                    "processing_time_ms": (time.time() - start_time) * 1000,
                    "results": [],
                    "suggestions": [],
                    "debug_info": "No content available for search"
                }
            
            # Build query based on search scope
            if search_scope == "titles":
                results = await self._search_document_titles(query, filters, top_k)
            elif search_scope == "summaries":
                results = await self._search_summaries(query, filters, top_k)
            elif search_scope == "content":
                results = await self._search_content(query, filters, top_k)
            else:  # search_scope == "all"
                results = await self._search_all_content(query, filters, top_k)
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            return {
                "query": query,
                "search_type": "global",
                "total_results": len(results),
                "processing_time_ms": round(processing_time_ms, 2),
                "results": results,
                "suggestions": self._generate_search_suggestions(query) if not results else None
            }
            
        except Exception as e:
            print(f"❌ Error in global search: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "query": query,
                "search_type": "global",
                "total_results": 0,
                "processing_time_ms": 0,
                "results": [],
                "error": str(e)
            }

    async def _search_document_titles(self, query: str, filters: Dict[str, Any], top_k: int) -> List[Dict[str, Any]]:
        """Search in document titles"""
        try:
            query_lower = query.lower()
            
            base_query = self.db.query(Document).filter(
                func.lower(Document.title).like(f"%{query_lower}%")
            )
            
            # Apply additional filters
            if filters:
                if filters.get("domain"):
                    base_query = base_query.filter(Document.domain == filters["domain"])
                if filters.get("author"):
                    base_query = base_query.filter(Document.author == filters["author"])
            
            documents = base_query.limit(top_k).all()
            
            results = []
            for doc in documents:
                # Get a representative chunk for preview
                chunk = self.db.query(Chunk).filter(
                    Chunk.document_id == doc.id
                ).order_by(Chunk.chunk_ix).first()
                
                if chunk:
                    result = {
                        "chunk_id": chunk.id,
                        "document_id": doc.id,
                        "document_title": doc.title,
                        "document_version": doc.version,
                        "chunk_index": chunk.chunk_ix,
                        "similarity_score": 0.8,  # High score for title matches
                        "text_preview": self._create_text_preview(chunk.text, query),
                        "full_text": chunk.text,
                        "intent_label": chunk.intent_label,
                        "heading": chunk.heading,
                        "subheading": chunk.subheading,
                        "summary": chunk.summary
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            print(f"❌ Error searching titles: {e}")
            return []

    async def _search_summaries(self, query: str, filters: Dict[str, Any], top_k: int) -> List[Dict[str, Any]]:
        """Search in chunk summaries"""
        try:
            query_lower = query.lower()
            
            base_query = self.db.query(
                Chunk.id,
                Chunk.document_id,
                Chunk.chunk_ix,
                Chunk.text,
                Chunk.summary,
                Chunk.intent_label,
                Chunk.heading,
                Chunk.subheading,
                Document.title,
                Document.version
            ).join(Document, Chunk.document_id == Document.id).filter(
                and_(
                    Chunk.summary.isnot(None),
                    func.lower(Chunk.summary).like(f"%{query_lower}%")
                )
            )
            
            chunks = base_query.limit(top_k).all()
            
            results = []
            for chunk in chunks:
                result = {
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "document_title": chunk.title,
                    "document_version": chunk.version,
                    "chunk_index": chunk.chunk_ix,
                    "similarity_score": 0.7,  # Good score for summary matches
                    "text_preview": self._create_text_preview(chunk.text, query),
                    "full_text": chunk.text,
                    "intent_label": chunk.intent_label,
                    "heading": chunk.heading,
                    "subheading": chunk.subheading,
                    "summary": chunk.summary
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            print(f"❌ Error searching summaries: {e}")
            return []

    async def _search_content(self, query: str, filters: Dict[str, Any], top_k: int) -> List[Dict[str, Any]]:
        """Search in chunk content"""
        try:
            query_lower = query.lower()
            
            base_query = self.db.query(
                Chunk.id,
                Chunk.document_id,
                Chunk.chunk_ix,
                Chunk.text,
                Chunk.summary,
                Chunk.intent_label,
                Chunk.heading,
                Chunk.subheading,
                Document.title,
                Document.version
            ).join(Document, Chunk.document_id == Document.id).filter(
                func.lower(Chunk.text).like(f"%{query_lower}%")
            )
            
            chunks = base_query.limit(top_k * 2).all()  # Get more for scoring
            
            # Score and rank results
            results = []
            for chunk in chunks:
                # Calculate relevance score
                text_lower = chunk.text.lower()
                score = 0.0
                
                # Exact phrase match
                if query_lower in text_lower:
                    score += 0.5
                
                # Word matches
                query_words = query_lower.split()
                word_matches = sum(1 for word in query_words if word in text_lower)
                score += (word_matches / len(query_words)) * 0.3
                
                # Position bonus (earlier matches are better)
                first_match_pos = text_lower.find(query_lower)
                if first_match_pos >= 0:
                    position_score = 1.0 - (first_match_pos / len(text_lower))
                    score += position_score * 0.2
                
                result = {
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "document_title": chunk.title,
                    "document_version": chunk.version,
                    "chunk_index": chunk.chunk_ix,
                    "similarity_score": round(score, 3),
                    "text_preview": self._create_text_preview(chunk.text, query),
                    "full_text": chunk.text,
                    "intent_label": chunk.intent_label,
                    "heading": chunk.heading,
                    "subheading": chunk.subheading,
                    "summary": chunk.summary
                }
                results.append(result)
            
            # Sort by score and return top results
            results.sort(key=lambda x: x["similarity_score"], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            print(f"❌ Error searching content: {e}")
            return []

    async def _search_all_content(self, query: str, filters: Dict[str, Any], top_k: int) -> List[Dict[str, Any]]:
        """Search across all content types"""
        try:
            # Perform searches in different scopes
            title_results = await self._search_document_titles(query, filters, max(5, top_k // 4))
            summary_results = await self._search_summaries(query, filters, max(5, top_k // 4))
            content_results = await self._search_content(query, filters, max(10, top_k // 2))
            
            # Combine and deduplicate results
            all_results = []
            seen_chunks = set()
            
            # Add title results first (highest priority)
            for result in title_results:
                if result["chunk_id"] not in seen_chunks:
                    result["similarity_score"] += 0.1  # Boost title matches
                    all_results.append(result)
                    seen_chunks.add(result["chunk_id"])
            
            # Add summary results
            for result in summary_results:
                if result["chunk_id"] not in seen_chunks:
                    all_results.append(result)
                    seen_chunks.add(result["chunk_id"])
            
            # Add content results
            for result in content_results:
                if result["chunk_id"] not in seen_chunks:
                    all_results.append(result)
                    seen_chunks.add(result["chunk_id"])
            
            # Sort by similarity score and return top results
            all_results.sort(key=lambda x: x["similarity_score"], reverse=True)
            return all_results[:top_k]
            
        except Exception as e:
            print(f"❌ Error in comprehensive search: {e}")
            return []

    def _generate_search_suggestions(self, query: str) -> List[str]:
        """Generate search suggestions based on available content"""
        try:
            suggestions = []
            
            # Get common intent labels
            intent_results = self.db.query(
                Chunk.intent_label,
                func.count(Chunk.id).label('count')
            ).filter(
                Chunk.intent_label.isnot(None)
            ).group_by(Chunk.intent_label).order_by(text('count DESC')).limit(5).all()
            
            for intent, count in intent_results:
                if intent and intent.lower() not in query.lower():
                    suggestions.append(f"intent:{intent}")
            
            # Get common domains
            domain_results = self.db.query(
                Document.domain,
                func.count(Document.id).label('count')
            ).filter(
                Document.domain.isnot(None)
            ).group_by(Document.domain).order_by(text('count DESC')).limit(3).all()
            
            for domain, count in domain_results:
                if domain and domain.lower() not in query.lower():
                    suggestions.append(f"domain:{domain}")
            
            return suggestions[:5]
            
        except Exception as e:
            print(f"⚠️ Error generating suggestions: {e}")
            return []

    async def get_search_stats(self) -> Dict[str, Any]:
        """Get search statistics and indexing status"""
        try:
            # Document statistics
            total_docs = self.db.query(Document).count()
            indexed_docs = self.db.query(Document).filter(Document.status == 'indexed').count()
            
            # Chunk statistics
            total_chunks = self.db.query(Chunk).count()
            chunks_with_summary = self.db.query(Chunk).filter(Chunk.summary.isnot(None)).count()
            
            # Vector index statistics
            vector_indexes = self.db.query(VectorIndex).count()
            
            # Content distribution by intent
            intent_distribution = {}
            intent_results = self.db.query(
                Chunk.intent_label, func.count(Chunk.id)
            ).group_by(Chunk.intent_label).all()
            
            for intent, count in intent_results:
                intent_distribution[intent or "unknown"] = count
            
            return {
                "indexing_stats": {
                    "total_documents": total_docs,
                    "indexed_documents": indexed_docs,
                    "indexing_progress": round((indexed_docs / total_docs) * 100, 1) if total_docs > 0 else 0
                },
                "content_stats": {
                    "total_chunks": total_chunks,
                    "chunks_with_summary": chunks_with_summary,
                    "vector_indexes": vector_indexes
                },
                "content_distribution": intent_distribution,
                "search_readiness": {
                    "ready": indexed_docs > 0 and total_chunks > 0,
                    "message": "Search is ready" if indexed_docs > 0 else "No indexed documents available"
                }
            }
            
        except Exception as e:
            print(f"❌ Failed to get search stats: {e}")
            return {
                "error": str(e),
                "search_readiness": {"ready": False, "message": "Search statistics unavailable"}
            }

    # Additional debugging methods
    async def debug_search(self, query: str) -> Dict[str, Any]:
        """Debug search functionality"""
        try:
            debug_info = {
                "query": query,
                "timestamp": time.time(),
                "database_checks": {},
                "search_results": {}
            }
            
            # Check database state
            debug_info["database_checks"] = {
                "total_documents": self.db.query(Document).count(),
                "total_chunks": self.db.query(Chunk).count(),
                "indexed_documents": self.db.query(Document).filter(Document.status == 'indexed').count(),
                "vector_indexes": self.db.query(VectorIndex).count()
            }
            
            # Test basic keyword search
            query_lower = query.lower()
            matching_chunks = self.db.query(Chunk).join(Document).filter(
                func.lower(Chunk.text).like(f"%{query_lower}%")
            ).limit(5).all()
            
            debug_info["search_results"]["keyword_matches"] = len(matching_chunks)
            debug_info["search_results"]["sample_matches"] = [
                {
                    "chunk_id": chunk.id,
                    "document_title": self.db.query(Document).filter(Document.id == chunk.document_id).first().title,
                    "text_preview": chunk.text[:100] + "..."
                }
                for chunk in matching_chunks[:3]
            ]
            
            # Test embedding service if available
            if self.embedding_service:
                try:
                    test_embedding = self.embedding_service.embed_texts([query])
                    debug_info["search_results"]["embedding_available"] = True
                    debug_info["search_results"]["embedding_shape"] = test_embedding.shape
                except Exception as e:
                    debug_info["search_results"]["embedding_error"] = str(e)
            else:
                debug_info["search_results"]["embedding_available"] = False
            
            return debug_info
            
        except Exception as e:
            return {"error": str(e)}

# Test the service
if __name__ == "__main__":
    print("✅ Fixed Search Service - proper result handling and debugging!")

