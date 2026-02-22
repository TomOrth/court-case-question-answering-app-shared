"""
Schemas for Executor Tool responses.

These Pydantic models and dataclasses define the structure of data returned by our executor tools (search, document QA, etc.).
"""

from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field
from dataclasses import dataclass

# ==========
# SEARCH RESULT SCHEMAS

@dataclass
class ChunkResult:
    """
    A single chunk result from semantic or keyword search.
    """
    chunk_id: str
    chunk_text: str
    doc_id: int
    doc_title: str
    doc_date: Optional[date]
    similarity_score: Optional[float] = None

    def format_for_planner(self) -> str:
        """
        Format this chunk for the Planner to read.
        
        Returns a string with:
        - Chunk metadata (doc_id, title, date)
        - The chunk text with inline citation marker
        """
        # Build metadata line
        metadata = f"--- Chunk (doc_id: {self.doc_id}, chunk_id: {self.chunk_id})"
        if self.similarity_score is not None:
            metadata += f", similarity: {self.similarity_score:.2f}"
        metadata += ") ---"

        # Add document context
        doc_context = f"Document ID {self.doc_id}: {self.doc_title}"
        if self.doc_date:
            doc_context += f" ({self.doc_date})"

        # Assemble with inline citation
        return (
            f"{metadata}\n"
            f"{self.chunk_text} [CITE:{self.chunk_id}]\n"
            f"(From: {doc_context})"
        )


class SearchResponse(BaseModel):
    """
    Response wrapper for search tool results.
    
    This is what gets returned to the Planner when it calls semantic_search or keyword_search_by_chunk.
    """
    tool_name: str = Field(..., description="Name of the tool that was called")
    query: str = Field(..., description="The search query or keywords")
    total_results: int = Field(..., description="Number of chunks found")
    chunks: List[ChunkResult] = Field(default_factory=list, description="The actual chunk results")

    def format_for_planner(self) -> str:
        """
        Format the entire search response for the Planner.
        
        This creates the structured text that the Planner will see as the "tool result" in its reasoning loop.
        """
        lines = [
            f"[Tool: {self.tool_name}]",
            f"[Query: \"{self.query}\"]",
            f"[Results: {self.total_results} chunks found]",
            ""
        ]

        for i, chunk in enumerate(self.chunks, 1):
            if i > 1:
                lines.append("")  # Blank line between chunks
            lines.append(chunk.format_for_planner())

        return "\n".join(lines)


# ==========
# TOOL PLAYGROUND API SCHEMAS

from typing import Dict, Any


class ToolExecuteRequest(BaseModel):
    """
    Request schema for executing a tool via API.
    
    Used by POST /api/tools/test endpoint for manual testing.
    """
    tool_name: str = Field(
        ...,
        description="Name of the tool to execute",
        examples=["semantic_search", "keyword_search_by_chunk", "ask_questions_on_document"]
    )
    params: Dict[str, Any] = Field(
        ...,
        description="Parameters for the tool",
        examples=[{
            "query": "What was the court's ruling?",
            "case_id": 14919,
            "top_k": 5
        }]
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "tool_name": "semantic_search",
                    "params": {
                        "query": "What was the preliminary injunction about?",
                        "case_id": 14919,
                        "top_k": 5
                    }
                },
                {
                    "tool_name": "keyword_search_by_chunk",
                    "params": {
                        "keywords": ["Judge Winmill", "2011"],
                        "case_id": 14919,
                        "max_results": 5
                    }
                },
                {
                    "tool_name": "ask_questions_on_document",
                    "params": {
                        "doc_id": 78342,
                        "questions": ["What was the date?", "Who was the judge?"],
                        "case_id": 14919,
                        "planners_context": "Testing document QA"
                    }
                }
            ]
        }


class ToolExecuteResponse(BaseModel):
    """
    Response schema for tool execution via API.
    
    Returns the formatted result string that the Planner would receive.
    """
    success: bool = Field(
        ...,
        description="Whether the tool executed successfully"
    )
    tool_name: str = Field(
        ...,
        description="Name of the tool that was executed"
    )
    result: str = Field(
        ...,
        description="Formatted result string with inline citations"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if execution failed"
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": True,
                    "tool_name": "semantic_search",
                    "result": "[Tool: semantic_search]\n[Query: \"What was the ruling?\"]\n[Results: 5 chunks found]\n\n--- Result 1 ---\n[Chunk ID: doc_123_chunk_00005]\n...",
                    "error": None
                },
                {
                    "success": False,
                    "tool_name": "unknown_tool",
                    "result": "",
                    "error": "Unknown tool: unknown_tool"
                }
            ]
        }