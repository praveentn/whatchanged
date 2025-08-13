# services/embedding_service.py
"""
DocuReview Pro - Embedding Service for Semantic Analysis
Sentence transformers + FAISS for semantic search and similarity
"""
import os
import json
import numpy as np
import faiss
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
from sentence_transformers import SentenceTransformer
from utils.chunking import RollingChunker
from utils.text_processing import normalize_text
from config import Config

class EmbeddingService:
    """Service for text embeddings and semantic search using FAISS"""
    
    def __init__(self, model_name: str, chunk_size: int = 800, chunk_overlap: int = 100):
        """
        Initialize embedding service
        
        Args:
            model_name (str): Sentence transformer model name
            chunk_size (int): Size of text chunks in tokens
            chunk_overlap (int): Overlap between chunks
        
        Example:
            service = EmbeddingService(
                model_name="all-MiniLM-L6-v2",
                chunk_size=800,
                chunk_overlap=100
            )
        """
        self.model_name = model_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize sentence transformer
        print(f"🔄 Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        print(f"✅ Embedding model loaded. Dimension: {self.embedding_dim}")
        
        # Initialize chunker
        self.chunker = RollingChunker(
            chunk_size=chunk_size,
            overlap=chunk_overlap
        )
        
        # FAISS index directory
        self.faiss_dir = Path(Config.UPLOAD_FOLDER) / "faiss"
        self.faiss_dir.mkdir(parents=True, exist_ok=True)

    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Split text into chunks for embedding
        
        Args:
            text (str): Input text to chunk
        
        Returns:
            List[Dict[str, Any]]: List of chunk dictionaries
        
        Example:
            chunks = service.chunk_text("Long document text...")
            # Returns: [{"text": "chunk1", "start": 0, "end": 100}, ...]
        """
        try:
            # Normalize text first
            normalized_text = normalize_text(text)
            
            # Generate chunks
            chunks = self.chunker.chunk_text(normalized_text)
            
            return chunks
            
        except Exception as e:
            print(f"❌ Error in text chunking: {e}")
            # Fallback: simple paragraph splitting
            paragraphs = text.split('\n\n')
            return [
                {
                    "text": para.strip(),
                    "start": i * 100,  # Approximate
                    "end": (i + 1) * 100,
                    "chunk_index": i
                }
                for i, para in enumerate(paragraphs) if para.strip()
            ]

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for list of texts
        
        Args:
            texts (List[str]): List of texts to embed
        
        Returns:
            np.ndarray: Array of embeddings (n_texts, embedding_dim)
        
        Example:
            embeddings = service.embed_texts(["text1", "text2", "text3"])
            # Returns: numpy array of shape (3, 384) for MiniLM
        """
        try:
            if not texts:
                return np.array([]).reshape(0, self.embedding_dim)
            
            # Generate embeddings
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=len(texts) > 10,
                batch_size=32
            )
            
            # Normalize for cosine similarity
            faiss.normalize_L2(embeddings)
            
            return embeddings
            
        except Exception as e:
            print(f"❌ Error generating embeddings: {e}")
            # Return zero embeddings as fallback
            return np.zeros((len(texts), self.embedding_dim), dtype=np.float32)

    def build_document_index(self, document_id: int, chunks: List[Dict]) -> str:
        """
        Build FAISS index for a document's chunks
        
        Args:
            document_id (int): Document ID
            chunks (List[Dict]): List of chunk dictionaries with text
        
        Returns:
            str: Path to saved FAISS index
        
        Example:
            index_path = service.build_document_index(
                document_id=123,
                chunks=[{"text": "chunk1"}, {"text": "chunk2"}]
            )
        """
        try:
            # Extract text from chunks
            texts = [chunk.get("text", "") for chunk in chunks]
            
            if not texts:
                raise ValueError("No text found in chunks")
            
            # Generate embeddings
            embeddings = self.embed_texts(texts)
            
            if embeddings.shape[0] == 0:
                raise ValueError("Failed to generate embeddings")
            
            # Create FAISS index
            index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product (cosine similarity)
            index.add(embeddings)
            
            # Save index to disk
            index_path = self.faiss_dir / f"doc_{document_id}.faiss"
            faiss.write_index(index, str(index_path))
            
            # Save metadata
            metadata = {
                "document_id": document_id,
                "embedding_dim": self.embedding_dim,
                "num_vectors": embeddings.shape[0],
                "model_name": self.model_name,
                "chunks": [
                    {
                        "chunk_index": i,
                        "text_preview": text[:100] + "..." if len(text) > 100 else text,
                        "text_length": len(text)
                    }
                    for i, text in enumerate(texts)
                ]
            }
            
            metadata_path = self.faiss_dir / f"doc_{document_id}_metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            print(f"✅ FAISS index built for document {document_id}: {embeddings.shape[0]} vectors")
            
            return str(index_path)
            
        except Exception as e:
            print(f"❌ Error building FAISS index: {e}")
            raise

    def search_document(self, document_id: int, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search document using semantic similarity
        
        Args:
            document_id (int): Document ID to search
            query (str): Search query
            top_k (int): Number of results to return
        
        Returns:
            List[Dict[str, Any]]: Search results with similarity scores
        
        Example:
            results = service.search_document(
                document_id=123,
                query="user authentication requirements",
                top_k=5
            )
        """
        try:
            index_path = self.faiss_dir / f"doc_{document_id}.faiss"
            metadata_path = self.faiss_dir / f"doc_{document_id}_metadata.json"
            
            if not index_path.exists():
                return []
            
            # Load index
            index = faiss.read_index(str(index_path))
            
            # Load metadata
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Generate query embedding
            query_embedding = self.embed_texts([query])
            
            # Search
            scores, indices = index.search(query_embedding, min(top_k, index.ntotal))
            
            # Format results
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx >= 0:  # Valid index
                    chunk_metadata = metadata["chunks"][idx] if idx < len(metadata["chunks"]) else {}
                    results.append({
                        "rank": i + 1,
                        "chunk_index": idx,
                        "similarity_score": float(score),
                        "text_preview": chunk_metadata.get("text_preview", ""),
                        "text_length": chunk_metadata.get("text_length", 0)
                    })
            
            return results
            
        except Exception as e:
            print(f"❌ Error searching document: {e}")
            return []

    def compare_embeddings(self, embeddings_a: np.ndarray, embeddings_b: np.ndarray) -> Dict[str, float]:
        """
        Compare two sets of embeddings for similarity analysis
        
        Args:
            embeddings_a (np.ndarray): First set of embeddings
            embeddings_b (np.ndarray): Second set of embeddings
        
        Returns:
            Dict[str, float]: Similarity metrics
        
        Example:
            metrics = service.compare_embeddings(doc1_embeddings, doc2_embeddings)
            # Returns: {"avg_similarity": 0.85, "max_similarity": 0.95, ...}
        """
        try:
            if embeddings_a.shape[0] == 0 or embeddings_b.shape[0] == 0:
                return {"avg_similarity": 0.0, "max_similarity": 0.0, "min_similarity": 0.0}
            
            # Compute pairwise similarities
            similarities = np.dot(embeddings_a, embeddings_b.T)
            
            # Calculate metrics
            max_similarities_a = np.max(similarities, axis=1)  # Best match for each in A
            max_similarities_b = np.max(similarities, axis=0)  # Best match for each in B
            
            metrics = {
                "avg_similarity": float(np.mean(similarities)),
                "max_similarity": float(np.max(similarities)),
                "min_similarity": float(np.min(similarities)),
                "avg_best_match_a": float(np.mean(max_similarities_a)),
                "avg_best_match_b": float(np.mean(max_similarities_b)),
                "overall_similarity": float((np.mean(max_similarities_a) + np.mean(max_similarities_b)) / 2)
            }
            
            return metrics
            
        except Exception as e:
            print(f"❌ Error comparing embeddings: {e}")
            return {"avg_similarity": 0.0, "max_similarity": 0.0, "min_similarity": 0.0}

    def get_chunk_embeddings(self, document_id: int) -> Optional[np.ndarray]:
        """
        Load embeddings for a document from disk
        
        Args:
            document_id (int): Document ID
        
        Returns:
            Optional[np.ndarray]: Embeddings array or None if not found
        
        Example:
            embeddings = service.get_chunk_embeddings(123)
        """
        try:
            index_path = self.faiss_dir / f"doc_{document_id}.faiss"
            
            if not index_path.exists():
                return None
            
            # Load index and extract embeddings
            index = faiss.read_index(str(index_path))
            
            # Extract all vectors from index
            embeddings = np.zeros((index.ntotal, self.embedding_dim), dtype=np.float32)
            index.reconstruct_n(0, index.ntotal, embeddings)
            
            return embeddings
            
        except Exception as e:
            print(f"❌ Error loading chunk embeddings: {e}")
            return None

    def calculate_document_similarity(self, document_id_a: int, document_id_b: int) -> Dict[str, float]:
        """
        Calculate similarity between two documents
        
        Args:
            document_id_a (int): First document ID
            document_id_b (int): Second document ID
        
        Returns:
            Dict[str, float]: Similarity metrics
        
        Example:
            similarity = service.calculate_document_similarity(123, 124)
        """
        try:
            embeddings_a = self.get_chunk_embeddings(document_id_a)
            embeddings_b = self.get_chunk_embeddings(document_id_b)
            
            if embeddings_a is None or embeddings_b is None:
                return {"error": "Embeddings not found for one or both documents"}
            
            return self.compare_embeddings(embeddings_a, embeddings_b)
            
        except Exception as e:
            print(f"❌ Error calculating document similarity: {e}")
            return {"error": str(e)}

if __name__ == "__main__":
    # Test embedding service
    print("🧪 Testing Embedding Service...")
    
    service = EmbeddingService(
        model_name=Config.SENTENCE_TRANSFORMER_MODEL,
        chunk_size=Config.CHUNK_SIZE,
        chunk_overlap=Config.CHUNK_OVERLAP
    )
    
    # Test text chunking
    test_text = """This is a test document. It contains multiple paragraphs.
    
    The first paragraph discusses system requirements. The system must be scalable and secure.
    
    The second paragraph covers implementation details. We will use Python and FastAPI for the backend."""
    
    chunks = service.chunk_text(test_text)
    print(f"✅ Generated {len(chunks)} chunks")
    
    # Test embeddings
    texts = [chunk["text"] for chunk in chunks]
    embeddings = service.embed_texts(texts)
    print(f"✅ Generated embeddings: shape {embeddings.shape}")
    
    # Test search
    try:
        index_path = service.build_document_index(999, chunks)
        print(f"✅ Built test index: {index_path}")
        
        results = service.search_document(999, "system requirements", top_k=3)
        print(f"✅ Search results: {len(results)} matches")
        
    except Exception as e:
        print(f"⚠️  Index test skipped: {e}")
    
    print("✅ Embedding Service test completed!")