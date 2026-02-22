"""
Tools API Routes - Manual Testing Endpoint for Executor Tools.

This router provides an HTTP endpoint for testing the three executor tools:
- semantic_search
- keyword_search_by_chunk
- ask_questions_on_document

Use this endpoint to manually test tools before integrating with the Planner.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.tools import ToolExecuteRequest, ToolExecuteResponse
from app.services.executor import ExecutorService


router = APIRouter(prefix="/api/tools", tags=["Tools"])


@router.post(
    "/test",
    response_model=ToolExecuteResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute a tool for testing",
    description="""
    Execute one of the three executor tools with given parameters.
    
    This endpoint is for manual testing and debugging. It calls the same
    ExecutorService that the Planner will use.
    
    **Supported Tools:**
    - `semantic_search`: Find chunks by meaning (requires: query, case_id)
    - `keyword_search_by_chunk`: Find chunks with ALL keywords (requires: keywords, case_id)
    - `ask_questions_on_document`: Ask questions about a document (requires: doc_id, questions, case_id)
    
    **Example Requests:**
    
    Semantic Search:
    ```json
    {
        "tool_name": "semantic_search",
        "params": {
            "query": "What was the court's ruling?",
            "case_id": 14919,
            "top_k": 5
        }
    }
    ```
    
    Keyword Search:
    ```json
    {
        "tool_name": "keyword_search_by_chunk",
        "params": {
            "keywords": ["Judge Winmill", "2011"],
            "case_id": 14919,
            "max_results": 5
        }
    }
    ```
    
    Document QA:
    ```json
    {
        "tool_name": "ask_questions_on_document",
        "params": {
            "doc_id": 78342,
            "questions": ["What was the date?", "Who was the judge?"],
            "case_id": 14919,
            "planners_context": "Testing document QA"
        }
    }
    ```
    """
)
async def execute_tool_test(
    request: ToolExecuteRequest,
    db: AsyncSession = Depends(get_db)
) -> ToolExecuteResponse:
    """
    Execute a tool with given parameters.
    
    Args:
        request: Tool name and parameters
        db: Database session (injected by FastAPI)
    
    Returns:
        ToolExecuteResponse with success status and result
    
    Raises:
        HTTPException: If tool execution fails unexpectedly
    """
    print(f"\n🔧 API: Tool test request received")
    print(f"  Tool: {request.tool_name}")
    print(f"  Params: {request.params}")
    
    try:
        # Create executor service
        executor = ExecutorService(db)
        
        # Execute the tool
        result = await executor.execute_tool(
            tool_name=request.tool_name,
            params=request.params
        )
        
        # Check if result is an error
        # ExecutorService returns "[ERROR] ..." strings for errors
        if result.startswith("[ERROR]"):
            return ToolExecuteResponse(
                success=False,
                tool_name=request.tool_name,
                result="",
                error=result.replace("[ERROR] ", "")
            )
        
        # Success!
        return ToolExecuteResponse(
            success=True,
            tool_name=request.tool_name,
            result=result,
            error=None
        )
    
    except Exception as e:
        # Unexpected error (shouldn't happen if ExecutorService is working)
        print(f"❌ Unexpected error in tools endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
