# utils/diff_engine.py
"""
DocuReview Pro - Advanced Diff Engine
Configurable document comparison algorithms with multiple granularities
"""
import re
import difflib
import hashlib
from typing import List, Dict, Any, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum

class DiffType(Enum):
    """Types of differences"""
    ADD = "add"
    DELETE = "delete"
    REPLACE = "replace"
    MOVE = "move"
    EQUAL = "equal"

class GranularityLevel(Enum):
    """Granularity levels for comparison"""
    CHARACTER = "character"
    WORD = "word"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    SEMANTIC = "semantic"

@dataclass
class DiffOperation:
    """Represents a single diff operation"""
    operation: DiffType
    source_start: int
    source_end: int
    target_start: int
    target_end: int
    source_content: List[str]
    target_content: List[str]
    confidence: float = 1.0
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class DiffResult:
    """Complete diff result with metadata"""
    operations: List[DiffOperation]
    source_units: List[str]
    target_units: List[str]
    granularity: GranularityLevel
    similarity_ratio: float
    change_percentage: float
    statistics: Dict[str, Any]
    processing_time_ms: float

class AdvancedDiffEngine:
    """Advanced document comparison engine with multiple algorithms"""
    
    def __init__(self):
        """Initialize diff engine with default settings"""
        self.similarity_threshold = 0.8
        self.move_detection_threshold = 0.9
        self.semantic_threshold = 0.7

    def compare_texts(self, source: str, target: str, 
                     granularity: GranularityLevel = GranularityLevel.WORD,
                     algorithm: str = "hybrid") -> DiffResult:
        """
        Compare two texts with specified granularity and algorithm
        
        Args:
            source (str): Source text
            target (str): Target text
            granularity (GranularityLevel): Comparison granularity
            algorithm (str): Algorithm type (syntactic, semantic, hybrid)
        
        Returns:
            DiffResult: Comprehensive comparison result
        
        Example:
            result = engine.compare_texts(
                "Hello world. This is a test.",
                "Hello universe. This is a demo.",
                GranularityLevel.WORD,
                "hybrid"
            )
        """
        import time
        start_time = time.time()
        
        try:
            # Tokenize based on granularity
            source_units = self._tokenize_text(source, granularity)
            target_units = self._tokenize_text(target, granularity)
            
            # Choose algorithm
            if algorithm == "syntactic":
                operations = self._syntactic_diff(source_units, target_units)
            elif algorithm == "semantic":
                operations = self._semantic_diff(source_units, target_units, granularity)
            elif algorithm == "hybrid":
                operations = self._hybrid_diff(source_units, target_units, granularity)
            else:
                operations = self._syntactic_diff(source_units, target_units)
            
            # Post-process operations
            operations = self._post_process_operations(operations)
            
            # Calculate statistics
            similarity_ratio = self._calculate_similarity(operations, len(source_units), len(target_units))
            change_percentage = (1 - similarity_ratio) * 100
            
            statistics = self._calculate_statistics(operations, source_units, target_units)
            
            processing_time = (time.time() - start_time) * 1000
            
            return DiffResult(
                operations=operations,
                source_units=source_units,
                target_units=target_units,
                granularity=granularity,
                similarity_ratio=similarity_ratio,
                change_percentage=change_percentage,
                statistics=statistics,
                processing_time_ms=round(processing_time, 2)
            )
            
        except Exception as e:
            print(f"❌ Error in text comparison: {e}")
            # Return empty result
            return DiffResult(
                operations=[],
                source_units=[],
                target_units=[],
                granularity=granularity,
                similarity_ratio=0.0,
                change_percentage=100.0,
                statistics={"error": str(e)},
                processing_time_ms=0.0
            )

    def _tokenize_text(self, text: str, granularity: GranularityLevel) -> List[str]:
        """
        Tokenize text based on granularity level
        
        Args:
            text (str): Input text
            granularity (GranularityLevel): Tokenization level
        
        Returns:
            List[str]: Tokenized text units
        """
        if granularity == GranularityLevel.CHARACTER:
            return list(text)
        
        elif granularity == GranularityLevel.WORD:
            # Split on whitespace and punctuation, but keep punctuation
            tokens = re.findall(r'\S+', text)
            return tokens
        
        elif granularity == GranularityLevel.SENTENCE:
            # Split into sentences
            sentences = re.split(r'[.!?]+\s+', text)
            return [s.strip() for s in sentences if s.strip()]
        
        elif granularity == GranularityLevel.PARAGRAPH:
            # Split into paragraphs
            paragraphs = text.split('\n\n')
            return [p.strip() for p in paragraphs if p.strip()]
        
        else:
            # Default to word level
            return re.findall(r'\S+', text)

    def _syntactic_diff(self, source_units: List[str], target_units: List[str]) -> List[DiffOperation]:
        """
        Perform syntactic (text-based) diff using SequenceMatcher
        
        Args:
            source_units (List[str]): Source text units
            target_units (List[str]): Target text units
        
        Returns:
            List[DiffOperation]: Diff operations
        """
        operations = []
        matcher = difflib.SequenceMatcher(None, source_units, target_units)
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                continue  # Skip equal sections
            
            operation_type = {
                'insert': DiffType.ADD,
                'delete': DiffType.DELETE,
                'replace': DiffType.REPLACE
            }.get(tag, DiffType.REPLACE)
            
            operation = DiffOperation(
                operation=operation_type,
                source_start=i1,
                source_end=i2,
                target_start=j1,
                target_end=j2,
                source_content=source_units[i1:i2],
                target_content=target_units[j1:j2],
                confidence=1.0
            )
            operations.append(operation)
        
        return operations

    def _semantic_diff(self, source_units: List[str], target_units: List[str], 
                      granularity: GranularityLevel) -> List[DiffOperation]:
        """
        Perform semantic diff using similarity comparison
        
        Args:
            source_units (List[str]): Source text units
            target_units (List[str]): Target text units
            granularity (GranularityLevel): Granularity level
        
        Returns:
            List[DiffOperation]: Semantic diff operations
        """
        operations = []
        
        # For semantic diff, we need to compare meaning rather than exact text
        # This is a simplified implementation
        used_target = set()
        
        for i, source_unit in enumerate(source_units):
            best_match_j = -1
            best_similarity = 0.0
            
            for j, target_unit in enumerate(target_units):
                if j in used_target:
                    continue
                
                similarity = self._calculate_semantic_similarity(source_unit, target_unit)
                
                if similarity > best_similarity and similarity > self.semantic_threshold:
                    best_similarity = similarity
                    best_match_j = j
            
            if best_match_j >= 0:
                # Found semantic match
                used_target.add(best_match_j)
                
                if best_similarity < 1.0:  # Not exact match
                    operation = DiffOperation(
                        operation=DiffType.REPLACE,
                        source_start=i,
                        source_end=i + 1,
                        target_start=best_match_j,
                        target_end=best_match_j + 1,
                        source_content=[source_unit],
                        target_content=[target_units[best_match_j]],
                        confidence=best_similarity,
                        metadata={"semantic_similarity": best_similarity}
                    )
                    operations.append(operation)
            else:
                # No semantic match found - deletion
                operation = DiffOperation(
                    operation=DiffType.DELETE,
                    source_start=i,
                    source_end=i + 1,
                    target_start=i,  # Approximate position
                    target_end=i,
                    source_content=[source_unit],
                    target_content=[],
                    confidence=1.0
                )
                operations.append(operation)
        
        # Find insertions (target units not matched)
        for j, target_unit in enumerate(target_units):
            if j not in used_target:
                operation = DiffOperation(
                    operation=DiffType.ADD,
                    source_start=j,  # Approximate position
                    source_end=j,
                    target_start=j,
                    target_end=j + 1,
                    source_content=[],
                    target_content=[target_unit],
                    confidence=1.0
                )
                operations.append(operation)
        
        return operations

    def _hybrid_diff(self, source_units: List[str], target_units: List[str],
                    granularity: GranularityLevel) -> List[DiffOperation]:
        """
        Perform hybrid diff combining syntactic and semantic approaches
        
        Args:
            source_units (List[str]): Source text units
            target_units (List[str]): Target text units
            granularity (GranularityLevel): Granularity level
        
        Returns:
            List[DiffOperation]: Hybrid diff operations
        """
        # Start with syntactic diff as base
        syntactic_ops = self._syntactic_diff(source_units, target_units)
        
        # Enhance with semantic analysis for REPLACE operations
        enhanced_ops = []
        
        for op in syntactic_ops:
            if op.operation == DiffType.REPLACE and op.source_content and op.target_content:
                # Calculate semantic similarity for replacements
                if len(op.source_content) == 1 and len(op.target_content) == 1:
                    similarity = self._calculate_semantic_similarity(
                        op.source_content[0], 
                        op.target_content[0]
                    )
                    
                    # If highly similar semantically, adjust confidence
                    if similarity > self.semantic_threshold:
                        op.confidence = similarity
                        op.metadata = {"semantic_similarity": similarity}
                        
                        # If very similar, might be just formatting change
                        if similarity > 0.95:
                            op.metadata["change_type"] = "formatting"
            
            enhanced_ops.append(op)
        
        # Detect moves using semantic similarity
        enhanced_ops = self._detect_moves(enhanced_ops, source_units, target_units)
        
        return enhanced_ops

    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two text units
        
        Args:
            text1 (str): First text
            text2 (str): Second text
        
        Returns:
            float: Similarity score (0-1)
        """
        # Simple semantic similarity calculation
        # In practice, you might use embeddings or more sophisticated NLP
        
        # Exact match
        if text1 == text2:
            return 1.0
        
        # Case-insensitive match
        if text1.lower() == text2.lower():
            return 0.98
        
        # Jaccard similarity of words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        jaccard = intersection / max(union, 1)
        
        # Character-level similarity as backup
        char_similarity = difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
        
        # Combine both measures
        return max(jaccard, char_similarity * 0.8)

    def _detect_moves(self, operations: List[DiffOperation], source_units: List[str], 
                     target_units: List[str]) -> List[DiffOperation]:
        """
        Detect moved content by analyzing delete/add pairs
        
        Args:
            operations (List[DiffOperation]): Current operations
            source_units (List[str]): Source text units
            target_units (List[str]): Target text units
        
        Returns:
            List[DiffOperation]: Operations with moves detected
        """
        enhanced_ops = []
        deletes = []
        adds = []
        
        # Separate deletes and adds
        for op in operations:
            if op.operation == DiffType.DELETE:
                deletes.append(op)
            elif op.operation == DiffType.ADD:
                adds.append(op)
            else:
                enhanced_ops.append(op)
        
        # Try to match deletes with adds
        used_adds = set()
        
        for delete_op in deletes:
            best_add_idx = -1
            best_similarity = 0.0
            
            for i, add_op in enumerate(adds):
                if i in used_adds:
                    continue
                
                # Compare content similarity
                if delete_op.source_content and add_op.target_content:
                    similarity = self._calculate_semantic_similarity(
                        ' '.join(delete_op.source_content),
                        ' '.join(add_op.target_content)
                    )
                    
                    if similarity > best_similarity and similarity > self.move_detection_threshold:
                        best_similarity = similarity
                        best_add_idx = i
            
            if best_add_idx >= 0:
                # Found a move
                add_op = adds[best_add_idx]
                used_adds.add(best_add_idx)
                
                move_op = DiffOperation(
                    operation=DiffType.MOVE,
                    source_start=delete_op.source_start,
                    source_end=delete_op.source_end,
                    target_start=add_op.target_start,
                    target_end=add_op.target_end,
                    source_content=delete_op.source_content,
                    target_content=add_op.target_content,
                    confidence=best_similarity,
                    metadata={"move_similarity": best_similarity}
                )
                enhanced_ops.append(move_op)
            else:
                # Keep as delete
                enhanced_ops.append(delete_op)
        
        # Add remaining adds
        for i, add_op in enumerate(adds):
            if i not in used_adds:
                enhanced_ops.append(add_op)
        
        return enhanced_ops

    def _post_process_operations(self, operations: List[DiffOperation]) -> List[DiffOperation]:
        """
        Post-process operations to merge adjacent similar operations
        
        Args:
            operations (List[DiffOperation]): Raw operations
        
        Returns:
            List[DiffOperation]: Processed operations
        """
        if not operations:
            return operations
        
        # Sort operations by source position
        operations.sort(key=lambda op: (op.source_start, op.target_start))
        
        merged_ops = []
        current_op = operations[0]
        
        for next_op in operations[1:]:
            # Try to merge adjacent operations of same type
            if (current_op.operation == next_op.operation and
                current_op.source_end == next_op.source_start and
                current_op.target_end == next_op.target_start):
                
                # Merge operations
                current_op = DiffOperation(
                    operation=current_op.operation,
                    source_start=current_op.source_start,
                    source_end=next_op.source_end,
                    target_start=current_op.target_start,
                    target_end=next_op.target_end,
                    source_content=current_op.source_content + next_op.source_content,
                    target_content=current_op.target_content + next_op.target_content,
                    confidence=min(current_op.confidence, next_op.confidence)
                )
            else:
                # Can't merge, add current and continue with next
                merged_ops.append(current_op)
                current_op = next_op
        
        # Add final operation
        merged_ops.append(current_op)
        
        return merged_ops

    def _calculate_similarity(self, operations: List[DiffOperation], 
                            source_len: int, target_len: int) -> float:
        """
        Calculate overall similarity ratio from operations
        
        Args:
            operations (List[DiffOperation]): Diff operations
            source_len (int): Source text length
            target_len (int): Target text length
        
        Returns:
            float: Similarity ratio (0-1)
        """
        if source_len == 0 and target_len == 0:
            return 1.0
        
        total_units = max(source_len, target_len)
        changed_units = 0
        
        for op in operations:
            if op.operation in [DiffType.ADD, DiffType.DELETE, DiffType.REPLACE]:
                changed_units += max(len(op.source_content), len(op.target_content))
        
        return max(0.0, 1.0 - (changed_units / max(total_units, 1)))

    def _calculate_statistics(self, operations: List[DiffOperation], 
                            source_units: List[str], target_units: List[str]) -> Dict[str, Any]:
        """
        Calculate detailed statistics from diff operations
        
        Args:
            operations (List[DiffOperation]): Diff operations
            source_units (List[str]): Source text units
            target_units (List[str]): Target text units
        
        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        stats = {
            "total_operations": len(operations),
            "source_length": len(source_units),
            "target_length": len(target_units),
            "operations_by_type": {},
            "content_changes": {},
            "position_changes": []
        }
        
        # Count operations by type
        for op in operations:
            op_type = op.operation.value
            stats["operations_by_type"][op_type] = stats["operations_by_type"].get(op_type, 0) + 1
        
        # Calculate content change statistics
        added_units = sum(len(op.target_content) for op in operations if op.operation == DiffType.ADD)
        deleted_units = sum(len(op.source_content) for op in operations if op.operation == DiffType.DELETE)
        replaced_units = sum(max(len(op.source_content), len(op.target_content)) 
                           for op in operations if op.operation == DiffType.REPLACE)
        moved_units = sum(len(op.source_content) for op in operations if op.operation == DiffType.MOVE)
        
        stats["content_changes"] = {
            "added": added_units,
            "deleted": deleted_units,
            "replaced": replaced_units,
            "moved": moved_units,
            "net_change": added_units - deleted_units
        }
        
        # Track position changes for moves
        for op in operations:
            if op.operation == DiffType.MOVE:
                stats["position_changes"].append({
                    "from_position": op.source_start,
                    "to_position": op.target_start,
                    "content_preview": ' '.join(op.source_content[:3])
                })
        
        return stats

    def generate_html_diff(self, diff_result: DiffResult, 
                          color_scheme: str = "default") -> str:
        """
        Generate HTML representation of diff with highlighting
        
        Args:
            diff_result (DiffResult): Diff result to visualize
            color_scheme (str): Color scheme for highlighting
        
        Returns:
            str: HTML representation of diff
        """
        # Color schemes
        schemes = {
            "default": {
                "add": "#90EE90",      # Light green
                "delete": "#FFB6C1",   # Light pink
                "replace": "#FFD700",  # Gold
                "move": "#87CEEB"      # Sky blue
            },
            "colorblind": {
                "add": "#0066CC",      # Blue
                "delete": "#FF6600",   # Orange
                "replace": "#9900CC",  # Purple
                "move": "#00AA00"      # Green
            },
            "high_contrast": {
                "add": "#000000",      # Black
                "delete": "#FFFFFF",   # White
                "replace": "#808080",  # Gray
                "move": "#404040"      # Dark gray
            }
        }
        
        colors = schemes.get(color_scheme, schemes["default"])
        
        html_parts = []
        html_parts.append('<div class="diff-container">')
        
        # Generate side-by-side view
        html_parts.append('<div class="diff-side-by-side">')
        html_parts.append('<div class="diff-source">')
        html_parts.append('<h3>Source</h3>')
        
        # Process source text
        source_html = self._generate_side_html(
            diff_result.source_units, 
            diff_result.operations, 
            "source", 
            colors
        )
        html_parts.append(source_html)
        html_parts.append('</div>')
        
        html_parts.append('<div class="diff-target">')
        html_parts.append('<h3>Target</h3>')
        
        # Process target text
        target_html = self._generate_side_html(
            diff_result.target_units,
            diff_result.operations,
            "target",
            colors
        )
        html_parts.append(target_html)
        html_parts.append('</div>')
        html_parts.append('</div>')
        
        # Add statistics
        html_parts.append('<div class="diff-stats">')
        html_parts.append(f'<p>Similarity: {diff_result.similarity_ratio:.1%}</p>')
        html_parts.append(f'<p>Changes: {diff_result.change_percentage:.1f}%</p>')
        html_parts.append(f'<p>Operations: {len(diff_result.operations)}</p>')
        html_parts.append('</div>')
        
        html_parts.append('</div>')
        
        return '\n'.join(html_parts)

    def _generate_side_html(self, units: List[str], operations: List[DiffOperation],
                           side: str, colors: Dict[str, str]) -> str:
        """Generate HTML for one side of the diff"""
        html_parts = []
        
        # Create position map
        position_map = {}
        for op in operations:
            if side == "source":
                for i in range(op.source_start, op.source_end):
                    position_map[i] = op
            else:
                for i in range(op.target_start, op.target_end):
                    position_map[i] = op
        
        # Generate HTML for each unit
        for i, unit in enumerate(units):
            if i in position_map:
                op = position_map[i]
                color = colors.get(op.operation.value, "#FFFFFF")
                html_parts.append(f'<span style="background-color: {color}" title="{op.operation.value}">{unit}</span>')
            else:
                html_parts.append(f'<span>{unit}</span>')
        
        return ' '.join(html_parts)

if __name__ == "__main__":
    # Test the diff engine
    print("🧪 Testing Advanced Diff Engine...")
    
    engine = AdvancedDiffEngine()
    
    # Test data
    source_text = "The quick brown fox jumps over the lazy dog. This is a test sentence."
    target_text = "The fast brown fox leaps over the sleepy dog. This is a demo sentence."
    
    # Test word-level diff
    print("\n📝 Testing word-level diff...")
    result = engine.compare_texts(source_text, target_text, GranularityLevel.WORD, "hybrid")
    
    print(f"✅ Similarity: {result.similarity_ratio:.2f}")
    print(f"✅ Change %: {result.change_percentage:.1f}%")
    print(f"✅ Operations: {len(result.operations)}")
    
    for op in result.operations:
        print(f"  {op.operation.value}: '{' '.join(op.source_content)}' → '{' '.join(op.target_content)}'")
    
    # Test sentence-level diff
    print("\n📑 Testing sentence-level diff...")
    result = engine.compare_texts(source_text, target_text, GranularityLevel.SENTENCE, "syntactic")
    print(f"✅ Sentence-level similarity: {result.similarity_ratio:.2f}")
    
    print("\n✅ Diff Engine test completed!")