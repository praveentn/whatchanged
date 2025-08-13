# utils/chunking.py
"""
DocuReview Pro - Text Chunking Utilities
Rolling window chunking with token-aware splitting
"""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ChunkConfig:
    """Configuration for text chunking"""
    chunk_size: int = 800
    overlap: int = 100
    min_chunk_size: int = 50
    preserve_paragraphs: bool = True
    preserve_sentences: bool = True

class RollingChunker:
    """Rolling window text chunker with smart boundary detection"""
    
    def __init__(self, chunk_size: int = 800, overlap: int = 100, preserve_boundaries: bool = True):
        """
        Initialize rolling chunker
        
        Args:
            chunk_size (int): Target chunk size in tokens/words
            overlap (int): Overlap between chunks
            preserve_boundaries (bool): Try to preserve sentence/paragraph boundaries
        
        Example:
            chunker = RollingChunker(chunk_size=800, overlap=100)
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.preserve_boundaries = preserve_boundaries
        
        # Sentence boundary regex
        self.sentence_pattern = re.compile(r'[.!?]+\s+')
        self.paragraph_pattern = re.compile(r'\n\s*\n')

    def tokenize_simple(self, text: str) -> List[str]:
        """
        Simple word-based tokenization
        
        Args:
            text (str): Input text
        
        Returns:
            List[str]: List of tokens
        
        Example:
            tokens = chunker.tokenize_simple("Hello world! How are you?")
            # Returns: ["Hello", "world!", "How", "are", "you?"]
        """
        # Simple whitespace + punctuation tokenization
        tokens = re.findall(r'\S+', text)
        return tokens

    def find_best_split_point(self, text: str, target_position: int) -> int:
        """
        Find the best position to split text while preserving boundaries
        
        Args:
            text (str): Text to split
            target_position (int): Target character position
        
        Returns:
            int: Best split position
        
        Example:
            pos = chunker.find_best_split_point("Hello world. This is a test.", 12)
            # Returns position after "Hello world." if preserve_boundaries=True
        """
        if not self.preserve_boundaries or target_position >= len(text):
            return min(target_position, len(text))
        
        # Look for sentence boundary within ±50 chars of target
        search_start = max(0, target_position - 50)
        search_end = min(len(text), target_position + 50)
        search_text = text[search_start:search_end]
        
        # Find sentence endings
        sentence_matches = list(self.sentence_pattern.finditer(search_text))
        
        if sentence_matches:
            # Find closest sentence boundary to target
            target_in_search = target_position - search_start
            best_match = min(sentence_matches, 
                           key=lambda m: abs(m.end() - target_in_search))
            return search_start + best_match.end()
        
        # Fall back to paragraph boundary
        para_pos = text.rfind('\n', search_start, search_end)
        if para_pos > search_start:
            return para_pos + 1
        
        # Fall back to word boundary
        word_pos = text.rfind(' ', search_start, search_end)
        if word_pos > search_start:
            return word_pos + 1
        
        # Last resort: exact position
        return target_position

    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks
        
        Args:
            text (str): Input text to chunk
        
        Returns:
            List[Dict[str, Any]]: List of chunk dictionaries
        
        Example:
            chunks = chunker.chunk_text("Long document text...")
            # Returns: [
            #   {"text": "chunk1...", "start": 0, "end": 800, "chunk_index": 0},
            #   {"text": "chunk2...", "start": 700, "end": 1500, "chunk_index": 1}
            # ]
        """
        if not text or not text.strip():
            return []
        
        chunks = []
        text_length = len(text)
        
        # Estimate characters per token (rough approximation)
        tokens = self.tokenize_simple(text)
        chars_per_token = len(text) / max(len(tokens), 1)
        
        # Convert token-based sizes to character positions
        chunk_chars = int(self.chunk_size * chars_per_token)
        overlap_chars = int(self.overlap * chars_per_token)
        
        start_pos = 0
        chunk_index = 0
        
        while start_pos < text_length:
            # Calculate end position
            end_pos = start_pos + chunk_chars
            
            # Find best split point for end
            if end_pos < text_length:
                end_pos = self.find_best_split_point(text, end_pos)
            else:
                end_pos = text_length
            
            # Extract chunk text
            chunk_text = text[start_pos:end_pos].strip()
            
            if chunk_text:  # Only add non-empty chunks
                # Calculate token count for this chunk
                chunk_tokens = self.tokenize_simple(chunk_text)
                
                chunk_data = {
                    "text": chunk_text,
                    "start": start_pos,
                    "end": end_pos,
                    "chunk_index": chunk_index,
                    "token_count": len(chunk_tokens),
                    "char_count": len(chunk_text)
                }
                
                chunks.append(chunk_data)
                chunk_index += 1
            
            # Calculate next start position with overlap
            next_start = end_pos - overlap_chars
            
            # Ensure we make progress
            if next_start <= start_pos:
                next_start = start_pos + 1
            
            start_pos = next_start
            
            # Safety check to prevent infinite loop
            if start_pos >= text_length:
                break
        
        return chunks

    def rechunk_with_config(self, text: str, config: ChunkConfig) -> List[Dict[str, Any]]:
        """
        Chunk text with custom configuration
        
        Args:
            text (str): Input text
            config (ChunkConfig): Chunking configuration
        
        Returns:
            List[Dict[str, Any]]: Chunked text
        
        Example:
            config = ChunkConfig(chunk_size=500, overlap=50)
            chunks = chunker.rechunk_with_config(text, config)
        """
        # Temporarily update settings
        original_chunk_size = self.chunk_size
        original_overlap = self.overlap
        
        self.chunk_size = config.chunk_size
        self.overlap = config.overlap
        
        try:
            chunks = self.chunk_text(text)
            
            # Filter by minimum chunk size
            filtered_chunks = [
                chunk for chunk in chunks 
                if chunk["token_count"] >= config.min_chunk_size
            ]
            
            return filtered_chunks
            
        finally:
            # Restore original settings
            self.chunk_size = original_chunk_size
            self.overlap = original_overlap

class ParagraphChunker:
    """Alternative chunker that respects paragraph boundaries"""
    
    def __init__(self, max_chunk_size: int = 800, target_chunk_size: int = 600):
        """
        Initialize paragraph-based chunker
        
        Args:
            max_chunk_size (int): Maximum tokens per chunk
            target_chunk_size (int): Target tokens per chunk
        """
        self.max_chunk_size = max_chunk_size
        self.target_chunk_size = target_chunk_size

    def chunk_by_paragraphs(self, text: str) -> List[Dict[str, Any]]:
        """
        Chunk text by grouping paragraphs
        
        Args:
            text (str): Input text
        
        Returns:
            List[Dict[str, Any]]: Paragraph-based chunks
        
        Example:
            chunker = ParagraphChunker()
            chunks = chunker.chunk_by_paragraphs(document_text)
        """
        # Split into paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0
        start_pos = 0
        
        for para in paragraphs:
            para_tokens = len(re.findall(r'\S+', para))
            
            # If adding this paragraph would exceed max size, start new chunk
            if current_chunk and (current_size + para_tokens > self.max_chunk_size):
                # Save current chunk
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "start": start_pos,
                    "end": start_pos + len(chunk_text),
                    "chunk_index": len(chunks),
                    "token_count": current_size,
                    "paragraph_count": len(current_chunk)
                })
                
                # Start new chunk
                start_pos += len(chunk_text) + 2  # +2 for paragraph separator
                current_chunk = [para]
                current_size = para_tokens
            else:
                # Add to current chunk
                current_chunk.append(para)
                current_size += para_tokens
        
        # Add final chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "start": start_pos,
                "end": start_pos + len(chunk_text),
                "chunk_index": len(chunks),
                "token_count": current_size,
                "paragraph_count": len(current_chunk)
            })
        
        return chunks

if __name__ == "__main__":
    # Test chunking utilities
    print("🧪 Testing Chunking Utilities...")
    
    # Test data
    test_text = """This is the first paragraph. It contains multiple sentences. Each sentence adds important information.

This is the second paragraph. It discusses different concepts. The information builds upon the previous paragraph.

The third paragraph introduces new ideas. These ideas are complex and require detailed explanation. We need to ensure proper chunking.

Finally, this is the last paragraph. It concludes the document. All previous concepts are summarized here."""
    
    # Test rolling chunker
    print("\n📝 Testing Rolling Chunker...")
    chunker = RollingChunker(chunk_size=50, overlap=10, preserve_boundaries=True)
    chunks = chunker.chunk_text(test_text)
    
    print(f"✅ Generated {len(chunks)} chunks")
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i}: {chunk['token_count']} tokens, chars {chunk['start']}-{chunk['end']}")
        print(f"  Preview: {chunk['text'][:100]}...")
    
    # Test paragraph chunker
    print("\n📑 Testing Paragraph Chunker...")
    para_chunker = ParagraphChunker(max_chunk_size=100, target_chunk_size=80)
    para_chunks = para_chunker.chunk_by_paragraphs(test_text)
    
    print(f"✅ Generated {len(para_chunks)} paragraph chunks")
    for i, chunk in enumerate(para_chunks):
        print(f"Para Chunk {i}: {chunk['paragraph_count']} paragraphs, {chunk['token_count']} tokens")
    
    print("\n✅ Chunking utilities test completed!")