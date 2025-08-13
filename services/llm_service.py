# services/llm_service.py
"""
DocuReview Pro - LLM Service for Azure OpenAI Integration
Enterprise AI-powered document analysis using Azure OpenAI
"""
import json
import asyncio
from typing import Dict, List, Optional, Any
from openai import AzureOpenAI
from datetime import datetime

class LLMService:
    """Azure OpenAI service for document analysis and comparison"""
    
    def __init__(self, endpoint: str, api_key: str, api_version: str, deployment: str):
        """
        Initialize Azure OpenAI client
        
        Args:
            endpoint (str): Azure OpenAI endpoint URL
            api_key (str): Azure OpenAI API key
            api_version (str): API version
            deployment (str): Model deployment name
        
        Example:
            service = LLMService(
                endpoint="https://your-resource.openai.azure.com/",
                api_key="your-api-key",
                api_version="2024-12-01-preview",
                deployment="gpt-4.1-nano"
            )
        """
        self.endpoint = endpoint
        self.deployment = deployment
        
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            api_version=api_version,
            azure_endpoint=endpoint,
            api_key=api_key,
        )
        
        # Analysis prompts
        self.prompts = {
            "chunk_analysis": """You are an expert document analyst. Analyze this text chunk and provide structured analysis.

Text to analyze:
{text}

Context: This is chunk {chunk_index} from document "{document_title}".

Provide your analysis in this exact JSON format:
{
    "intent_label": "one of: overview|requirements|design|procedure|risks|example|conclusion|other",
    "summary": "concise 1-2 sentence summary of this chunk",
    "heading": "inferred section heading (if any)",
    "subheading": "inferred subsection heading (if any)",
    "key_values": {
        "key1": "value1",
        "key2": "value2"
    },
    "entities": ["entity1", "entity2"],
    "relationships": [
        {"subject": "entity1", "predicate": "relates_to", "object": "entity2"}
    ]
}

Focus on accuracy and consistency. Be concise but thorough.""",

            "document_synthesis": """You are an expert document analyst. Synthesize the overall structure and content of this document.

Document: {document_title}
Total chunks: {chunk_count}

Chunk summaries:
{chunk_summaries}

Provide your synthesis in this exact JSON format:
{
    "document_summary": "comprehensive 3-4 sentence overview of the entire document",
    "document_outline": [
        {"heading": "Section 1", "subheadings": ["Sub 1.1", "Sub 1.2"]},
        {"heading": "Section 2", "subheadings": ["Sub 2.1"]}
    ],
    "primary_intent": "overall document purpose",
    "key_themes": ["theme1", "theme2", "theme3"],
    "risk_factors": ["risk1", "risk2"],
    "completion_score": 0.95
}

Focus on document structure and main themes.""",

            "comparison_summary": """You are an expert document analyst. Analyze the differences between two document versions.

Document: {document_title}
Version A: {version_a} vs Version B: {version_b}

Changes detected:
{change_data}

Metrics:
- Text similarity: {text_similarity}%
- Structural changes: {structural_changes}
- Intent changes: {intent_changes}

Provide your analysis in this exact JSON format:
{
    "executive_summary": "2-3 sentence overview of key changes",
    "major_additions": ["addition1", "addition2"],
    "major_removals": ["removal1", "removal2"],
    "structural_changes": ["change1", "change2"],
    "intent_shifts": ["shift1", "shift2"],
    "risk_assessment": "low|medium|high",
    "review_recommendations": ["focus_area1", "focus_area2"],
    "change_significance": "minor|moderate|major|breaking"
}

Focus on business impact and actionable insights."""
        }

    async def analyze_chunk(self, text: str, chunk_index: int, document_title: str, context: Dict = None) -> Dict[str, Any]:
        """
        Analyze a single text chunk with AI
        
        Args:
            text (str): Text chunk to analyze
            chunk_index (int): Index of the chunk in document
            document_title (str): Document title for context
            context (Dict, optional): Additional context
        
        Returns:
            Dict[str, Any]: Analysis results
        
        Example:
            result = await service.analyze_chunk(
                "This document outlines the system requirements...",
                0,
                "System Requirements Document"
            )
        """
        try:
            prompt = self.prompts["chunk_analysis"].format(
                text=text[:2000],  # Limit text for token efficiency
                chunk_index=chunk_index,
                document_title=document_title
            )
            
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a precise document analyst. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3,  # Lower temperature for consistency
                model=self.deployment
            )
            
            # Parse JSON response
            content = response.choices[0].message.content.strip()
            
            # Clean JSON if wrapped in code blocks
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
            
            analysis = json.loads(content)
            
            # Add metadata
            analysis["processing_timestamp"] = datetime.utcnow().isoformat()
            analysis["chunk_index"] = chunk_index
            analysis["token_usage"] = response.usage.total_tokens if response.usage else 0
            
            return analysis
            
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parsing error in chunk analysis: {e}")
            return self._fallback_chunk_analysis(text, chunk_index)
        except Exception as e:
            print(f"❌ Error in chunk analysis: {e}")
            return self._fallback_chunk_analysis(text, chunk_index)

    async def synthesize_document(self, document_title: str, chunk_analyses: List[Dict]) -> Dict[str, Any]:
        """
        Synthesize document-level analysis from chunk analyses
        
        Args:
            document_title (str): Document title
            chunk_analyses (List[Dict]): List of chunk analysis results
        
        Returns:
            Dict[str, Any]: Document synthesis
        
        Example:
            synthesis = await service.synthesize_document(
                "Requirements Document",
                [chunk1_analysis, chunk2_analysis, ...]
            )
        """
        try:
            # Prepare chunk summaries
            chunk_summaries = []
            for i, analysis in enumerate(chunk_analyses):
                chunk_summaries.append(f"Chunk {i}: {analysis.get('summary', 'No summary')}")
            
            prompt = self.prompts["document_synthesis"].format(
                document_title=document_title,
                chunk_count=len(chunk_analyses),
                chunk_summaries="\n".join(chunk_summaries)
            )
            
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert document synthesizer. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.3,
                model=self.deployment
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean JSON
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
            
            synthesis = json.loads(content)
            synthesis["processing_timestamp"] = datetime.utcnow().isoformat()
            synthesis["token_usage"] = response.usage.total_tokens if response.usage else 0
            
            return synthesis
            
        except Exception as e:
            print(f"❌ Error in document synthesis: {e}")
            return self._fallback_document_synthesis(document_title, len(chunk_analyses))

    async def summarize_comparison(self, document_title: str, version_a: int, version_b: int, 
                                 change_data: Dict, metrics: Dict) -> Dict[str, Any]:
        """
        Generate AI summary of document version comparison
        
        Args:
            document_title (str): Document title
            version_a (int): First version number
            version_b (int): Second version number
            change_data (Dict): Detected changes
            metrics (Dict): Comparison metrics
        
        Returns:
            Dict[str, Any]: Comparison summary
        
        Example:
            summary = await service.summarize_comparison(
                "API Documentation",
                1, 2,
                {"added_sections": [...], "removed_sections": [...]},
                {"similarity": 0.85, "changes": 15}
            )
        """
        try:
            prompt = self.prompts["comparison_summary"].format(
                document_title=document_title,
                version_a=version_a,
                version_b=version_b,
                change_data=json.dumps(change_data, indent=2)[:1500],
                text_similarity=round(metrics.get("similarity", 0) * 100, 1),
                structural_changes=metrics.get("structural_changes", 0),
                intent_changes=metrics.get("intent_changes", 0)
            )
            
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert change analyst. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.4,
                model=self.deployment
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean JSON
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
            
            summary = json.loads(content)
            summary["processing_timestamp"] = datetime.utcnow().isoformat()
            summary["token_usage"] = response.usage.total_tokens if response.usage else 0
            
            return summary
            
        except Exception as e:
            print(f"❌ Error in comparison summary: {e}")
            return self._fallback_comparison_summary()

    def _fallback_chunk_analysis(self, text: str, chunk_index: int) -> Dict[str, Any]:
        """Fallback analysis when AI fails"""
        return {
            "intent_label": "other",
            "summary": f"Text chunk {chunk_index} ({len(text)} characters)",
            "heading": None,
            "subheading": None,
            "key_values": {},
            "entities": [],
            "relationships": [],
            "processing_timestamp": datetime.utcnow().isoformat(),
            "chunk_index": chunk_index,
            "fallback": True
        }

    def _fallback_document_synthesis(self, title: str, chunk_count: int) -> Dict[str, Any]:
        """Fallback synthesis when AI fails"""
        return {
            "document_summary": f"Document '{title}' contains {chunk_count} analyzed chunks.",
            "document_outline": [{"heading": "Content", "subheadings": []}],
            "primary_intent": "unknown",
            "key_themes": [],
            "risk_factors": [],
            "completion_score": 0.5,
            "processing_timestamp": datetime.utcnow().isoformat(),
            "fallback": True
        }

    def _fallback_comparison_summary(self) -> Dict[str, Any]:
        """Fallback comparison summary when AI fails"""
        return {
            "executive_summary": "Document versions have been compared with automated analysis.",
            "major_additions": [],
            "major_removals": [],
            "structural_changes": [],
            "intent_shifts": [],
            "risk_assessment": "unknown",
            "review_recommendations": ["Manual review recommended"],
            "change_significance": "unknown",
            "processing_timestamp": datetime.utcnow().isoformat(),
            "fallback": True
        }

if __name__ == "__main__":
    # Test LLM service
    import os
    from config import Config
    
    async def test_llm_service():
        print("🧪 Testing LLM Service...")
        
        service = LLMService(
            endpoint=Config.AZURE_OPENAI_ENDPOINT,
            api_key=Config.AZURE_OPENAI_API_KEY,
            api_version=Config.AZURE_OPENAI_API_VERSION,
            deployment=Config.AZURE_OPENAI_DEPLOYMENT
        )
        
        # Test chunk analysis
        test_text = "This document outlines the system requirements for the new customer portal. The system must support user authentication, data encryption, and real-time notifications."
        
        result = await service.analyze_chunk(test_text, 0, "System Requirements")
        print(f"✅ Chunk analysis result: {json.dumps(result, indent=2)}")
        
        print("✅ LLM Service test completed!")
    
    # Run test
    asyncio.run(test_llm_service())
