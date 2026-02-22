"""
Executor Service - Tool Router and Response Formatter.

This service acts as the orchestrator for all executor tools. It:
1. Routes tool calls to the appropriate service
2. Validates parameters
3. Formats responses consistently for the Planner
4. Handles errors gracefully

The Planner will call this service during its reasoning loop.
"""

from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.search import SearchService
from app.services.document_qa import DocumentQAService
from app.schemas.tools import ChunkResult
from app.utils.llm_logger import get_llm_logger

TOP_K_SEMANTIC_SEARCH = 10
TOP_K_KEYWORD_SEARCH = 10

class ExecutorService:
    """
    Orchestrates execution of all executor tools.
    
    This is the single entry point for the Planner to invoke tools.
    """
    
    # Define supported tools
    SUPPORTED_TOOLS = {
        # "semantic_search",
        "keyword_search_by_chunk",
        "ask_questions_on_document"
    }
    
    def __init__(self, db: AsyncSession):
        """
        Initialize with database session.
        
        Args:
            db: Async SQLAlchemy session for database queries
        """
        self.db = db
        self.search_service = SearchService(db)
        self.doc_qa_service = DocumentQAService(db)
    
    async def execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        logger=None
    ) -> str:
        """
        Execute a tool by name with given parameters.
        
        This is the main entry point that the Planner will use.
        It routes to the appropriate service and formats the response.
        
        Args:
            tool_name: Name of the tool to execute
            params: Dictionary of parameters for the tool
            logger: Optional LLMCallLogger instance for this request
        
        Returns:
            Formatted response string for the Planner
        
        Raises:
            ValueError: If tool name is invalid or parameters are missing
        
        Example:
            result = await executor.execute_tool(
                tool_name="semantic_search",
                params={"query": "What was the ruling?", "case_id": 14919}
            )
        """
        # STEP 1: Validate tool name
        if tool_name not in self.SUPPORTED_TOOLS:
            error_msg = (
                f"Unknown tool: {tool_name}\n"
                f"Supported tools: {', '.join(sorted(self.SUPPORTED_TOOLS))}"
            )
            print(f"❌ {error_msg}")
            return f"[ERROR] {error_msg}"
        
        # STEP 2: Route to appropriate handler
        try:
            # if tool_name == "semantic_search":
            #     result = await self._handle_semantic_search(params)
            
            if tool_name == "keyword_search_by_chunk":
                result = await self._handle_keyword_search(params)
            
            elif tool_name == "ask_questions_on_document":
                result = await self._handle_document_qa(params, logger=logger)
            
            else:
                # Should never reach here due to validation above
                result = f"[ERROR] Tool {tool_name} not implemented"
            
            return result
        
        except ValueError as e:
            # Parameter validation errors
            error_msg = f"Invalid parameters for {tool_name}: {str(e)}"
            print(f"❌ {error_msg}")
            return f"[ERROR] {error_msg}"
        
        except Exception as e:
            # Unexpected errors
            error_msg = f"Error executing {tool_name}: {str(e)}"
            print(f"❌ {error_msg}")
            return f"[ERROR] {error_msg}"
    
    # async def _handle_semantic_search(self, params: Dict[str, Any]) -> str:
    #     """
    #     Handle semantic_search tool call.
        
    #     Required params:
    #         - query: str
    #         - case_id: int
        
    #     Optional params:
    #         - top_k: int (default: TOP_K_SEMANTIC_SEARCH)
    #     """
    #     # Validate and extract required parameters
    #     query = params.get("query")
    #     case_id = params.get("case_id")
        
    #     if not query:
    #         raise ValueError("Missing required parameter: query")
    #     if not isinstance(query, str):
    #         raise ValueError("Parameter 'query' must be a string")
        
    #     if not case_id:
    #         raise ValueError("Missing required parameter: case_id")
        
    #     # Cast case_id to int (may come as string from JSON)
    #     try:
    #         case_id = int(case_id)
    #     except (ValueError, TypeError):
    #         raise ValueError("Parameter 'case_id' must be an integer")
        
    #     # Extract optional parameters
    #     top_k = params.get("top_k", TOP_K_SEMANTIC_SEARCH)
    #     try:
    #         top_k = int(top_k)
    #     except (ValueError, TypeError):
    #         raise ValueError("Parameter 'top_k' must be an integer")
        
    #     # Call the search service
    #     results = await self.search_service.semantic_search(
    #         query=query,
    #         case_id=case_id,
    #         top_k=top_k
    #     )
        
    #     # Format response for Planner
    #     return self._format_search_results(
    #         results=results,
    #         tool_name="semantic_search",
    #         query=query
    #     )
    
    async def _handle_keyword_search(self, params: Dict[str, Any]) -> str:
        """
        Handle keyword_search_by_chunk tool call.
        
        Required params:
            - keywords: List[str]
            - case_id: int
        
        Optional params:
            - max_results: int (default: TOP_K_KEYWORD_SEARCH)
        """
        # Validate and extract required parameters
        keywords = params.get("keywords")
        case_id = params.get("case_id")
        
        if not keywords:
            raise ValueError("Missing required parameter: keywords")
        if not isinstance(keywords, list):
            raise ValueError("Parameter 'keywords' must be a list of strings")
        if len(keywords) == 0:
            raise ValueError("Parameter 'keywords' must contain at least one keyword")
        
        # Validate all keywords are strings
        for i, kw in enumerate(keywords):
            if not isinstance(kw, str):
                raise ValueError(f"Keyword at index {i} must be a string, got {type(kw).__name__}")
        
        if not case_id:
            raise ValueError("Missing required parameter: case_id")
        
        # Cast case_id to int (may come as string from JSON)
        try:
            case_id = int(case_id)
        except (ValueError, TypeError):
            raise ValueError("Parameter 'case_id' must be an integer")
        
        # Extract optional parameters
        max_results = params.get("max_results", TOP_K_KEYWORD_SEARCH)
        try:
            max_results = int(max_results)
        except (ValueError, TypeError):
            raise ValueError("Parameter 'max_results' must be an integer")
        
        # Call the search service
        results = await self.search_service.keyword_search_by_chunk(
            keywords=keywords,
            case_id=case_id,
            max_results=max_results
        )
        
        # Format response for Planner
        return self._format_search_results(
            results=results,
            tool_name="keyword_search_by_chunk",
            keywords=keywords
        )
    
    async def _handle_document_qa(self, params: Dict[str, Any], logger=None) -> str:
        """
        Handle ask_questions_on_document tool call.
        
        Required params:
            - doc_id: int
            - questions: List[str]
            - case_id: int
        
        Optional params:
            - planners_context: str (default: "The planner needs to ask questions")
        """
        # Validate and extract required parameters
        doc_id = params.get("doc_id")
        questions = params.get("questions")
        case_id = params.get("case_id")
        
        if not doc_id:
            raise ValueError("Missing required parameter: doc_id")
        
        # Cast doc_id to int (may come as string from JSON)
        try:
            doc_id = int(doc_id)
        except (ValueError, TypeError):
            raise ValueError("Parameter 'doc_id' must be an integer")
        
        if not questions:
            raise ValueError("Missing required parameter: questions")
        if not isinstance(questions, list):
            raise ValueError("Parameter 'questions' must be a list of strings")
        if len(questions) == 0:
            raise ValueError("Parameter 'questions' must contain at least one question")
        
        # Validate all questions are strings
        for i, q in enumerate(questions):
            if not isinstance(q, str):
                raise ValueError(f"Question at index {i} must be a string, got {type(q).__name__}")
        
        if not case_id:
            raise ValueError("Missing required parameter: case_id")
        
        # Cast case_id to int (may come as string from JSON)
        try:
            case_id = int(case_id)
        except (ValueError, TypeError):
            raise ValueError("Parameter 'case_id' must be an integer")
        
        # Extract optional parameters
        planners_context = params.get("planners_context", "The planner needs to ask questions")
        if not isinstance(planners_context, str):
            raise ValueError("Parameter 'planners_context' must be a string")
        
        # Call the document QA service
        result = await self.doc_qa_service.ask_questions_on_document(
            doc_id=doc_id,
            questions=questions,
            planners_context=planners_context,
            case_id=case_id,
            logger=logger
        )
        
        # Document QA service already formats its own response
        return result
    
    def _format_search_results(
        self,
        results: List[ChunkResult],
        tool_name: str,
        query: str = None,
        keywords: List[str] = None
    ) -> str:
        """
        Format search results into a string for the Planner.
        
        The format includes:
        - Tool name and search parameters
        - Number of results found
        - Each result with metadata and inline citations
        
        Args:
            results: List of ChunkResult objects
            tool_name: Name of the tool that produced these results
            query: For semantic search (optional)
            keywords: For keyword search (optional)
        
        Returns:
            Formatted string with inline citations
        """
        # Build the header
        lines = [f"[Tool: {tool_name}]"]
        
        if query:
            lines.append(f"[Query: \"{query}\"]")
        if keywords:
            lines.append(f"[Keywords: {', '.join(keywords)}]")
        
        lines.append(f"[Results: {len(results)} chunks found]\n")
        
        # If no results, return early
        if len(results) == 0:
            lines.append("No matching chunks found.")
            return "\n".join(lines)
        
        # Format each result
        for i, chunk in enumerate(results, 1):
            # Use the ChunkResult's built-in formatter
            formatted_chunk = chunk.format_for_planner()
            lines.append(f"--- Result {i} ---")
            lines.append(formatted_chunk)
            lines.append("")  # Blank line between results
        
        return "\n".join(lines)