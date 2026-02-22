"""
Type definitions for the Planner Agent.

These Pydantic models define the structure of:
1. Tool calls (what the Planner wants to execute)
2. Planner responses  (structured output from the LLM)
3. Reasoning loop state (tracking progress through the loop)
"""


from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ToolCall(BaseModel):
    """
    Represents a single tool call that the Planner wants to execute.
    
    Example:
        {
            "tool": "semantic_search",
            "parameters": {
                "query": "What was the court's ruling?",
                "case_id": 14919
            }
        }
    
    The ExecutorService will receive this and route to the appropriate tool.
    """
    id: Optional[str] = Field(
        default=None,
        description="Unique identifier (UUID) for this tool call, assigned before streaming"
    )
    tool: str = Field(
        ...,
        description="Name of the tool to execute"
    )
    parameters: Dict[str, Any] = Field(
        ...,
        description="Parameters to pass to the tool"
    )

    class Config:
        extra = "allow"  # Allow extra fields (for flexibility)


class PlannerResponse(BaseModel):
    """
    Structured response from the Planner LLM during the reasoning loop.
    
    This is what we expect the LLM to output in JSON format:
    {
        "gathered_context": "From the search results, I learned...",
        "reasoning_step": "I need to find more information about...",
        "tool_calls": [
            {"tool": "semantic_search", "parameters": {...}}
        ]
    }
    Why this structure?
    - gathered_context: Distills bulky tool results into key information
    - reasoning_step: Shows the Planner's thinking (transparency!)
    - tool_calls: Next actions to take (empty = ready to answer)
    """
    gathered_context: str = Field(
        ...,
        description="Key information extracted from the last tool results"
    )
    reasoning_step: str = Field(
        ...,
        description="The Planner's current thinking and next steps"
    )
    tool_calls: List[ToolCall] = Field(
        default_factory=list,  # Empty list by default
        description="List of tools to execute next (if empty, means the planner is ready to formulate final answer)"
    )

    class Config:
        # Example for documentation (Pydantic v2 renamed schema_extra to json_schema_extra)
        json_schema_extra = {
            "example": {
                "gathered_context": "The court granted the motion [CITE:doc_123_chunk_00005]",
                "reasoning_step": "I found the ruling. Now I need to find the judge's name.",
                "tool_calls": [
                    {
                        "tool": "keyword_search_by_chunk",
                        "parameters": {
                            "keywords": ["judge", "presiding"],
                            "case_id": 14919
                        }
                    }
                ]
            }
        }


class ReasoningLoopState(BaseModel):
    """
    Tracks the state of the reasoning loop as it progresses.
    
    Why do we need this?
    - The loop runs multiple times (up to 20 steps)
    - We need to remember what happened in previous steps
    - We need to build up the context for the LLM
    
    Think of this as the Planner's "working memory".
    """
    step_number: int = Field(
        default=0,
        description="Current step in the reasoning loop (0-19)"
    )

    # These lists grow as the loop progresses
    gathered_contexts: List[str] = Field(
        default_factory=list,
        description="All gathered contexts from each step"
    )
    reasoning_steps: List[str] = Field(
        default_factory=list,
        description="All reasoning steps (the Planner's thoughts)"
    )
    tool_calls_history: List[List[ToolCall]] = Field(
        default_factory=list,
        description="All tool calls from each step (list of lists)"
    )
    tool_results_history: List[List[str]] = Field(
        default_factory=list,
        description="All tool results from each step (list of lists)"
    )

    # The full context sent to the LLM
    # This gets rebuilt on each iteration
    current_context: str = Field(
        default="",
        description="The complete context sent to LLM (includes everything)"
    )

    class Config:
        # Allow mutation (we'll update these fields as we go)
        validate_assignment = True


class StreamEvent(BaseModel):
    """
    Represents a single event to stream to the frontend.
    
    Event types:
    - "gathered_context": Show what information was extracted
    - "reasoning": Show the Planner's thinking
    - "tool_call": Show which tool is being called
    - "tool_result": Show the tool's response
    - "content": Stream the final answer (word by word)

    The frontend already knows how to handle these!
    """
    type: str = Field(
        ...,
        description="Event type (gathered_context, reasoning, tool_call, tool_result, content)"
    )
    data: Any = Field(
        ...,
        description="Event data (structure depends on type)"
    )

    def to_ndjson(self) -> str:
        """
        Convert to NDJSON format (Newline Delimited JSON).
        
        Example output:
            '{"type": "reasoning", "data": {"content": "I need to search..."}}\n'
        
        The \n at the end is critical for NDJSON/        
        """
        import json
        return json.dumps(self.dict()) + "\n"
