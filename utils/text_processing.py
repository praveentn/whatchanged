# utils/text_processing.py
"""
DocuReview Pro - Text Processing Utilities
Text normalization, cleaning, and preprocessing functions
"""
import re
import hashlib
import unicodedata
from typing import Dict, List, Optional, Tuple
from pathlib import Path

def normalize_text(text: str, aggressive: bool = False) -> str:
    """
    Normalize text for consistent processing
    
    Args:
        text (str): Input text to normalize
        aggressive (bool): If True, apply more aggressive normalization
    
    Returns:
        str: Normalized text
    
    Example:
        clean_text = normalize_text("  Hello\n\nWorld!  \t")
        # Returns: "Hello\n\nWorld!"
    """
    if not text:
        return ""
    
    # Unicode normalization
    text = unicodedata.normalize('NFKC', text)
    
    # Convert to UTF-8 if needed
    if isinstance(text, bytes):
        text = text.decode('utf-8', errors='replace')
    
    # Fix common encoding issues
    text = text.replace('\r\n', '\n')  # Windows line endings
    text = text.replace('\r', '\n')    # Mac line endings
    
    # Remove BOM if present
    text = text.lstrip('\ufeff')
    
    if aggressive:
        # Aggressive normalization for comparison
        # Collapse multiple whitespace to single space
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
    else:
        # Gentle normalization
        # Collapse multiple spaces but preserve line breaks
        text = re.sub(r'[ \t]+', ' ', text)
        # Collapse multiple line breaks to double breaks
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        # Remove trailing whitespace from lines
        text = '\n'.join(line.rstrip() for line in text.split('\n'))
    
    return text

def clean_text_for_embedding(text: str) -> str:
    """
    Clean text specifically for embedding generation
    
    Args:
        text (str): Input text
    
    Returns:
        str: Text optimized for embeddings
    
    Example:
        clean = clean_text_for_embedding("TEXT WITH SYMBOLS!@#$%")
        # Returns cleaner version suitable for embeddings
    """
    if not text:
        return ""
    
    # Basic normalization
    text = normalize_text(text)
    
    # Remove excessive punctuation (keep basic sentence structure)
    text = re.sub(r'[^\w\s.,!?;:\'\"-]', ' ', text)
    
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Trim
    text = text.strip()
    
    return text

def extract_headings(text: str) -> List[Dict[str, any]]:
    """
    Extract potential headings from text using heuristics
    
    Args:
        text (str): Input text
    
    Returns:
        List[Dict[str, any]]: List of detected headings
    
    Example:
        headings = extract_headings(document_text)
        # Returns: [{"text": "Introduction", "level": 1, "position": 0}, ...]
    """
    headings = []
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        if not line:
            continue
        
        # Check for various heading patterns
        heading_info = None
        
        # Pattern 1: All caps line (likely heading)
        if line.isupper() and len(line) > 2 and len(line) < 100:
            heading_info = {"text": line, "level": 1, "pattern": "all_caps"}
        
        # Pattern 2: Title case with no ending punctuation
        elif (line.istitle() and 
              not line.endswith('.') and 
              not line.endswith(',') and 
              len(line) < 80):
            heading_info = {"text": line, "level": 2, "pattern": "title_case"}
        
        # Pattern 3: Lines followed by equals or dashes
        elif i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line and set(next_line) in [{'='}, {'-'}]:
                level = 1 if '=' in next_line else 2
                heading_info = {"text": line, "level": level, "pattern": "underlined"}
        
        # Pattern 4: Numbered sections
        elif re.match(r'^\d+\.?\s+[A-Z]', line):
            heading_info = {"text": line, "level": 2, "pattern": "numbered"}
        
        # Pattern 5: Lines with specific prefixes
        elif re.match(r'^(Chapter|Section|Part|Appendix)\s+', line, re.IGNORECASE):
            heading_info = {"text": line, "level": 1, "pattern": "labeled"}
        
        if heading_info:
            heading_info["position"] = i
            heading_info["char_position"] = sum(len(lines[j]) + 1 for j in range(i))
            headings.append(heading_info)
    
    return headings

def calculate_text_hash(text: str, algorithm: str = 'sha256') -> str:
    """
    Calculate hash of text for change detection
    
    Args:
        text (str): Input text
        algorithm (str): Hash algorithm (sha256, md5, etc.)
    
    Returns:
        str: Hex digest of text hash
    
    Example:
        hash_val = calculate_text_hash("Some text content")
        # Returns: "a1b2c3d4e5f6..."
    """
    if not text:
        return ""
    
    # Normalize text for consistent hashing
    normalized = normalize_text(text, aggressive=True)
    
    # Calculate hash
    hasher = hashlib.new(algorithm)
    hasher.update(normalized.encode('utf-8'))
    
    return hasher.hexdigest()

def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences using regex patterns
    
    Args:
        text (str): Input text
    
    Returns:
        List[str]: List of sentences
    
    Example:
        sentences = split_into_sentences("Hello world. How are you? Fine!")
        # Returns: ["Hello world.", "How are you?", "Fine!"]
    """
    if not text:
        return []
    
    # Handle common abbreviations that shouldn't end sentences
    text = re.sub(r'\b(Dr|Mr|Mrs|Ms|Prof|Inc|Ltd|etc|vs|i\.e|e\.g)\.', r'\1<DOT>', text)
    
    # Split on sentence endings followed by whitespace and capital letter
    sentences = re.split(r'[.!?]+\s+(?=[A-Z])', text)
    
    # Restore abbreviation dots
    sentences = [s.replace('<DOT>', '.').strip() for s in sentences if s.strip()]
    
    return sentences

def extract_keywords(text: str, min_length: int = 3, max_keywords: int = 20) -> List[str]:
    """
    Extract potential keywords from text
    
    Args:
        text (str): Input text
        min_length (int): Minimum keyword length
        max_keywords (int): Maximum number of keywords to return
    
    Returns:
        List[str]: List of keywords
    
    Example:
        keywords = extract_keywords("This document discusses system requirements")
        # Returns: ["document", "discusses", "system", "requirements"]
    """
    if not text:
        return []
    
    # Normalize text
    clean_text = clean_text_for_embedding(text.lower())
    
    # Extract words
    words = re.findall(r'\b[a-zA-Z]{' + str(min_length) + ',}\b', clean_text)
    
    # Common stop words to filter out
    stop_words = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
        'after', 'above', 'below', 'between', 'among', 'this', 'that', 'these',
        'those', 'what', 'which', 'who', 'when', 'where', 'why', 'how', 'all',
        'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such',
        'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can', 'will',
        'just', 'should', 'now', 'have', 'has', 'had', 'been', 'being', 'are',
        'was', 'were', 'would', 'could', 'might', 'must', 'shall'
    }
    
    # Filter and count
    word_counts = {}
    for word in words:
        if word not in stop_words:
            word_counts[word] = word_counts.get(word, 0) + 1
    
    # Sort by frequency and return top keywords
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    
    return [word for word, count in sorted_words[:max_keywords]]

def detect_document_structure(text: str) -> Dict[str, any]:
    """
    Analyze document structure and metadata
    
    Args:
        text (str): Input text
    
    Returns:
        Dict[str, any]: Document structure information
    
    Example:
        structure = detect_document_structure(document_text)
        # Returns: {"headings": [...], "sections": [...], "word_count": 500}
    """
    if not text:
        return {"error": "Empty text"}
    
    # Basic statistics
    lines = text.split('\n')
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    words = len(re.findall(r'\S+', text))
    chars = len(text)
    
    # Extract headings
    headings = extract_headings(text)
    
    # Detect lists
    list_items = len(re.findall(r'^\s*[-*]\s+', text, re.MULTILINE))
    numbered_items = len(re.findall(r'^\s*\d+\.\s+', text, re.MULTILINE))
    
    # Detect code blocks or technical content
    code_blocks = len(re.findall(r'```|`[^`]+`', text))
    technical_terms = len(re.findall(r'\b[A-Z]{2,}[A-Z0-9]*\b', text))
    
    return {
        "word_count": words,
        "char_count": chars,
        "line_count": len(lines),
        "paragraph_count": len(paragraphs),
        "heading_count": len(headings),
        "headings": headings,
        "list_items": list_items,
        "numbered_items": numbered_items,
        "code_blocks": code_blocks,
        "technical_terms": technical_terms,
        "avg_words_per_paragraph": round(words / max(len(paragraphs), 1), 1),
        "keywords": extract_keywords(text)
    }

def generate_document_slug(title: str) -> str:
    """
    Generate URL-friendly slug from document title
    
    Args:
        title (str): Document title
    
    Returns:
        str: URL-friendly slug
    
    Example:
        slug = generate_document_slug("System Requirements Document v2.1")
        # Returns: "system-requirements-document-v2-1"
    """
    if not title:
        return "untitled"
    
    # Convert to lowercase
    slug = title.lower()
    
    # Replace non-alphanumeric characters with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    # Collapse multiple hyphens
    slug = re.sub(r'-+', '-', slug)
    
    # Limit length
    slug = slug[:100]
    
    # Ensure not empty
    if not slug:
        slug = "untitled"
    
    return slug

if __name__ == "__main__":
    # Test text processing utilities
    print("🧪 Testing Text Processing Utilities...")
    
    # Test data
    test_text = """INTRODUCTION

This is a test document. It contains multiple paragraphs and sections.

System Requirements
==================

The system must have the following features:
- User authentication
- Data encryption
- Real-time notifications

Implementation Details
----------------------

1. Use Python FastAPI
2. Implement SQLite database  
3. Add React frontend

CONCLUSION

This document outlines all requirements.
    """
    
    # Test normalization
    print("\n🧹 Testing text normalization...")
    normalized = normalize_text(test_text)
    print(f"✅ Normalized text: {len(normalized)} chars")
    
    # Test heading extraction
    print("\n📝 Testing heading extraction...")
    headings = extract_headings(test_text)
    print(f"✅ Found {len(headings)} headings:")
    for heading in headings:
        print(f"  Level {heading['level']}: {heading['text']} ({heading['pattern']})")
    
    # Test document structure
    print("\n🏗️ Testing document structure analysis...")
    structure = detect_document_structure(test_text)
    print(f"✅ Structure analysis:")
    print(f"  Words: {structure['word_count']}")
    print(f"  Paragraphs: {structure['paragraph_count']}")
    print(f"  Headings: {structure['heading_count']}")
    print(f"  Keywords: {structure['keywords'][:5]}")
    
    # Test slug generation
    print("\n🔗 Testing slug generation...")
    test_titles = [
        "System Requirements Document v2.1",
        "API Documentation & Guidelines",
        "User Manual (Draft)"
    ]
    
    for title in test_titles:
        slug = generate_document_slug(title)
        print(f"  '{title}' → '{slug}'")
    
    # Test hashing
    print("\n🔒 Testing text hashing...")
    hash_val = calculate_text_hash(test_text)
    print(f"✅ SHA256 hash: {hash_val[:16]}...")
    
    print("\n✅ Text processing utilities test completed!")