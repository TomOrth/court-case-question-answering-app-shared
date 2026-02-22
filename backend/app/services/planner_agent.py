"""
Planner Agent Service - The Brain.

This service implements the reasoning loop that:
1. Analyzes user questions
2. Decides which tools to use
3. Interprets tool results
4. Synthesizes final answers with citations

Architecture:
- Uses ExecutorService to run tools
- Uses LLMService to call LLM API
- Streams events to frontend in real-time
- Persists reasoning steps to database
"""


from typing import AsyncGenerator, List, Optional
# from uuid import UUID
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.planner_types import (
    ToolCall,
    PlannerResponse,
    ReasoningLoopState,
    StreamEvent
)
from app.services.executor import ExecutorService
from app.services.llm import get_llm_service
# from app.utils.llm_logger import get_llm_logger
from app.services.db_logger import get_db_logger

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.chat import ChatMessage, ChatSession
from app.models.case import InitialContext
import json

from pydantic import ValidationError 

# Constants
MAX_REASONING_STEPS = 20
CHAT_HISTORY_LIMIT_WORDS = 15000  # Summarize if exceeded
TOP_K_SEMANTIC_SEARCH = 10


class PlannerAgentService:
    """
    The Planner Agent - orchestrates the entire reasoning process.
    
    Usage:
        planner = PlannerAgentService(db)
        async for event in planner.process_question(question, case_id, session_id)
            yield event  # Stream to frontend
    """
    def __init__(self, db: AsyncSession):
        """
        Initialize with database session.

        Args:
            db: Async SQLAlchemy session for database operations
        """
        self.db = db
        self.executor = ExecutorService(db)
        self.llm_service = get_llm_service()
        self.current_case_id: Optional[int] = None
        self.llm_logger = None  # Created per request in process_question()


    async def process_question(
        self,
        question: str,
        case_id: int,
        session_id: str,
        parent_message_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Main entry point: Process a user question through the reasoning loop.
        
        This method will:
        1. Build initial context (chat history, case context, instructions)
        2. Run the reasoning loop (up to MAX_REASONING_STEPS times)
        3. Execute tools as needed
        4. Generate final answer
        5. Stream all events to frontend
        6. Save everything to database
        
        Args:
            question: User's question
            case_id: Which case to search in
            session_id: Chat session ID (for context and saving)
            
        Yields:
            NDJSON event string (one per line)

        Example:
            async for event in planner.process_question("Who was the judge?", 14919, "abc-123"):
                # event is a string like:
                # '{"type": "reasoning", "data": {"content": "I need to search..."}}\n'
                yield event            
        """
        # Create a new logger instance for THIS request to avoid race conditions
        # self.llm_logger = get_llm_logger()
        # self.llm_logger.start_question_session(
        #     session_id=session_id,
        #     question=question,
        #     case_id=case_id
        # )

        self.llm_logger = get_db_logger()
        self.llm_logger.start_question_session(
            session_id=session_id,
            question=question,
            parent_message_id=parent_message_id,
            case_id=case_id
        )

        self.current_case_id = case_id

        # Initialize reasoning loop state
        state = ReasoningLoopState()

        # ====================================
        # BUILD INITIAL CONTEXT
        # This includes: instructions, chat history, case context, tools, question
        initial_context = await self._build_initial_context(question, case_id, session_id)
        state.current_context = initial_context

        # ====================================
        # REASONING LOOP
        # Continue until we have enough information or hit max steps
        while state.step_number < MAX_REASONING_STEPS:
            # Call the Planner LLM
            try:
                planner_response = await self._call_planner_llm(
                    context=state.current_context,
                    is_final_answer=False,
                    step_number=state.step_number + 1
                )
            except Exception as e:
                # LLM call failed - yield error and stop
                print(f"❌ LLM call failed: {e}")
                yield StreamEvent(
                    type="content",
                    data=f"Error: Failed to process question. {str(e)}"
                ).to_ndjson()
                return

            # Extract components from response
            gathered_context = planner_response.gathered_context
            reasoning_step = planner_response.reasoning_step
            tool_calls = planner_response.tool_calls

            # Save to state
            state.gathered_contexts.append(gathered_context)
            state.reasoning_steps.append(reasoning_step)
            state.tool_calls_history.append(tool_calls)

            # Stream gathered_context to UI
            yield StreamEvent(
                type="gathered_context",
                data={
                    "id": str(uuid.uuid4()),
                    "step_number": state.step_number + 1,
                    "content": gathered_context
                }
            ).to_ndjson()

            # Stream reasoning_step to UI
            yield StreamEvent(
                type="reasoning",
                data={
                    "id": str(uuid.uuid4()),
                    "step_number": state.step_number + 1,
                    "content": reasoning_step
                }
            ).to_ndjson()

            # Check if Planner wants to call tools
            if len(tool_calls) == 0:
                # No tools means Planner has enough information
                break

            # ============================================
            # Assign IDs and stream all tools immediately
            # This shows the user the "plan" upfront
            # ============================================
            
            for tool_call in tool_calls:
                # Assign a unique ID to this tool call
                # This allows frontend to link the call with its result
                tool_call.id = str(uuid.uuid4())

                # Stream the tool call to frontend
                yield StreamEvent(
                    type="tool_call",
                    data={
                        "id": tool_call.id,
                        "step_number": state.step_number + 1,
                        "tool": tool_call.tool,
                        "parameters": tool_call.parameters,
                    }
                ).to_ndjson()

            # ============================================
            # Execute tools one-by-one and stream results ASP
            # This provides progressive feedback as each tool completes
            # ============================================            
            tool_results_for_this_step = []  # Collect results for state
            
            for tool_call in tool_calls:
                # Prepare parameters (add case_id)
                params = dict(tool_call.parameters)
                params["case_id"] = case_id

                # Execute the tool (this takes time)
                try:
                    result = await self.executor.execute_tool(
                        tool_name=tool_call.tool,
                        params=params,
                        logger=self.llm_logger
                    )
                except Exception as e:
                    # If tool fails, return error message as result
                    result = f"[ERROR] Tool {tool_call.tool} failed: {str(e)}"
                    print(f"  ❌ {result}")

                # Stream the result IMMEDIATELY (don't wait for other tools)
                yield StreamEvent(
                    type="tool_result",
                    data={
                        "id": tool_call.id,  # SAME ID as the tool call
                        "step_number": state.step_number + 1,
                        "tool": tool_call.tool,
                        "result": result,
                    }
                ).to_ndjson()  # Convert to NDJSON string!

                # Save result for context evolution (needed for next LLM call)
                tool_results_for_this_step.append(result)


            # Save tool results to state
            state.tool_results_history.append(tool_results_for_this_step)

            # Update context for next iteration
            # This is where context evolution happens
            state.current_context = self._evolve_context(
                initial_context=initial_context,
                state=state
            )

            # Increment step counter
            state.step_number += 1

        # ====================================
        # GENERATE FINAL ANSWER
        # Either we have enough info, or we hit max steps
                
        try:

            state.current_context = self._evolve_context(
                initial_context=initial_context,
                state=state
            )            
            final_response = await self._call_planner_llm(
                context=state.current_context,
                is_final_answer=True,
                step_number=0  # Final answer, not a reasoning step
            )
        except Exception as e:
            print(f"❌ Failed to generate final answer: {e}")
            yield StreamEvent(
                type="content",
                data=f"Error: Failed to generate answer. {str(e)}"
            ).to_ndjson()
            return            

        # Extract final answer from gathered_context
        # When is_final_answer=True, the LLM puts the answer in gathered_context
        final_answer = final_response.gathered_context

        # Stream final answer to UI
        # For now, stream the whole answer at once
        yield StreamEvent(
            type="content",
            data=final_answer
        ).to_ndjson()


    def _evolve_context(
        self,
        initial_context: str,
        state: ReasoningLoopState
    ) -> str:
        """
        Evolve the context for the next iteration.

        This implements the key context management pattern from the design:
        - Keep: instructions, chat history, case context, tools, question
        - Keep: ALL gathered_contexts (distilled information)
        - Keep: ALL reasoning_steps (Planner's thoughts)
        - Keep: ONLY THE MOST RECENT tool_results (they're bulky)
        - Remove: Old tool_results (they were distilled into gathered_context)

        Args:
            initial_context: The original context (never changes)
            state: Current reasoning loop state

        Returns:
            Updated context string for next LLM call
        """
        # Start with initial context (instructions, history, case info, tools, question)
        evolved_context = initial_context

        # Add a section for the reasoning history
        evolved_context += "\n\n" + "="*70
        evolved_context += "\n" + "REASONING HISTORY"
        evolved_context += "\n" + "="*70 + "\n"

        # Add each reasoning step with its gathered context
        for i in range(len(state.reasoning_steps)):
            step_num = i + 1

            # Add gathered context from this step
            if i < len(state.gathered_contexts):
                evolved_context += f"\n--- Step {step_num}: Gathered Context ---\n"
                evolved_context += state.gathered_contexts[i]

            # Add reasoning step
            evolved_context += f"\n\n--- Step {step_num}: Reasoning ---\n"
            evolved_context += state.reasoning_steps[i]

            # Add tool calls (if any)
            if i < len(state.tool_calls_history) and len(state.tool_calls_history[i]) > 0:
                evolved_context += f"\n\n--- Step {step_num}: Tool Calls ---\n"
                for j, tool_call in enumerate(state.tool_calls_history[i], 1):
                    evolved_context += f"{j}.{tool_call.tool}("
                    params = ", ".join(f"{k}={v}" for k, v in tool_call.parameters.items() if k != "case_id")
                    evolved_context += params + ")\n"
                
                evolved_context += "\n"

        # Add ONLY the most recent tool results (if any)
        if len(state.tool_results_history) > 0:
            most_recent_results = state.tool_results_history[-1]

            evolved_context += "\n" + "="*70
            evolved_context += "\n" + "MOST RECENT TOOL RESULTS"
            evolved_context += "\n" + "="*70 + "\n"

            for i, result in enumerate(most_recent_results, 1):
                evolved_context += f"\n--- Tool Result {i} ---\n"
                evolved_context += result
                evolved_context += "\n"

        return evolved_context

    async def _build_initial_context(
        self,
        question: str,
        case_id: int,
        session_id: str
    ) -> str:
        """
        Build the initial context for the first LLM call.
        
        This includes:
        - System instructions
        - Chat history (if any)
        - Initial case context
        - Available tools specification
        - The user's question
        
        Returns:
            Complete context string for the LLM
        """
        # System Instructions
        system_instructions = self._build_system_instructions()

        # Chat history
        chat_history = await self._fetch_chat_history(session_id)

        # Initial case context
        initial_context = await self._fetch_initial_context(case_id)

        # Tool specifications
        tool_specs = self._build_tool_specifications()

        # Combine everything
        full_context = f"""
{system_instructions}

======================
CHAT HISTORY
======================
{chat_history}

======================
CASE CONTEXT
======================
{initial_context}

======================
AVAILABLE_TOOLS
======================
{tool_specs}

======================
USER QUESTION
======================
{question}

======================
YOUR TASK
======================
Analyze the question and available context. Then respond with valid JSON in this format (this is only an example! The string "No tool results yet. Starting investigation." is just an example and should only be used when outputing the very first reasoning iteration!):
{{
    "gathered_context": "No tool results yet. Starting investigation.",
    "reasoning_step": "Explain your thinking and what you need to do next.",
    "tool_calls": [
        {{
            "tool": "tool_name",
            "parameters": {{
                "param": "value"
            }}
        }}
    ]
}}

Remember: 
- If you need more information, specify tool_calls. Please try multiple iterations and multiple directions based on the results of previous tool calls and the context you gathered.
- If you have enough information, return empty tool_calls: []
- Preserve [CITE:id] markers from tool results if you incorporate or reference a detail from a previous text or tool results that did include those citations
        """

        return full_context
    
    def _build_system_instructions(self) -> str:
        """
        Build the system instructions that tell the Planner how to behave.
        
        Returns:
            System instructions string
        """
        return """
You are an expert legal research assistant analyzing court case documents.

Your task is to answer user questions by:
1. Analyzinng the question and available context
2. Deciding which tools to use to gather information
3. Interpreting tool results and extracting relevant information
4. Repeating until you have sufficient information

IMPORTANT RULES:
- You must respond with valid JSON (not markdown, not text, just JSON)
- In "gathered_context": Extract relevant information from tool results that is useful for answering user's questions
- Preserve [CITE:id] markers if you choose to include or reference information from a specific chunk
- In "reasoning_step": Explain your thinking - what you know, what you need
- In "tool_calls": List tools to call next (if you leave this array empty, that means you have sufficient information and signals that you're ready to formulate a final answer and do not need further tool calls)


Approach:

- Please note that all available documents are listed in the context, and the summaries for all documents are provided. Do not try to "search" for additional documents or motions even if you see a reference to them (like "Dkt. 77-3" or something) and even if you think they might contain useful details.
- The keyword search will only return chunks from the available documents (all of which are provided as summaries in the context). Keyword search WILL NOT yield additional documents, so please do not hope to find or "fish" for documents not listed in the context.
- Thus, please rely first on the document summaries (as well as the document ID and document title, of course) and docket summary (which provides procedural history of the case) provided in the context as the first go-to place to look for useful and relevant details to answer the user's questions. Plus, the summaries already have citations attached.
- Relying on document summaries is a good start, but feel free to use tools to query documents to gather additional details in order to provide user with well-rounded answers and useful details.
- Please strongly consider using the `ask_questions_on_document` tool to query additional and more specific details in promising documents. When you use that tool, an executor agent will be provided with the full text of the document (and not just the summary) and will be able to answer your questions in greater details.
- The `ask_questions_on_document` tool is great for extracting specific textual details (like specific names, addresses, references) that might be paraphrased or omitted in a high-level summary. While the document summary might contain some vague wordings relevant to the question, it might be wise to double-check and verify the exact text by querying the document specifically, rather than just relying on the summary's phrasing. Please use the tools as many times as you would like.
- Only when you cannot find the right details that way should you attempt a keyword search, but a keyword search tends to be hit-and-miss, and will usually waste many reasoning cycles and may not yield the necessary chunks. (That would be a failure loop, where you "hope" to find a new document, refuse to accept that it's not in the data, and keep generating identical searches - different keyword order - and failing. Please avoid that!).
- The keyword_search_by_chunk tool, therefore, should be used sparingly when you're sure that specific keywords are needed, and attempts to query documents was not instructive.

Be grounded:

- Please note that all document summaries in the context have document IDs and dates explicitly noted. Please rely on the dates to reason about which documents need to be queried.
- When formulating a final answer and when gathering contexts and forming your reasoning, please be honest about what you know and do not know based on the current context so far. Please acknowledge if certain documents are not provided in the data.
- Please cite each chunk separately in each [CITE:chunk_id], especially when there are multiple chunks being referenced. For example, this citation is WRONG: "[CITE:doc_78277_chunk_00007; doc_78281_chunk_00005; doc_78340_chunk_00001]". The correct format should be "[CITE:doc_78277_chunk_00007][CITE:doc_78281_chunk_00005][CITE:doc_78340_chunk_00001]" so that the frontend can parse and convert into links correctly; but in general, please try to put citations directly after their corresponding details, so they don't get clustered together like that - which would make it confusing for the user to know a citation pertains to which detail.
- Please do not hallucinate details to satisfy the user's request. Please stick strictly to our available, explicitly listed documents in the context. In other words, please prioritize GROUNDING over compliance, when the user gives you an impossible instruction. 
- The user might mention or hint at legal details or documents or motions that are non-existent, so please be very careful not to hallucinate and do not assume that the premise of user's questions is always valid and factual. 
- The answers to the user's questions might not be in our data, and it's okay to honestly acknowledge that. Please avoid the trap of guessing a common answers based on your own internal knowledge. Everything needs to be backed by evidence from our contexts and documents.
- If you're unsure about certain details or only partially understand an aspect of the case, please feel free to double-check or do additional research, because critical clues might be found in later context-gathering efforts. But at the same time, please be flexible and change your research directions if you feel that the current research direction is not providing you additional useful clues.

Safety:

- Please only discuss the details of this case that are backed by actual evidence that you could gather from the context and from your tool calls. Do not engage in any discussion with the user on topics beyond this court case. Please refuse to answer any user questions that attempt to trick you into discussing unrelated subjects.

Please note that the information might be contained in multiple documents, so please be thorough in your research in order to retrieve as many relevant details as possible.

RESPONSE FORMAT:
{
    "gathered_context": "string (extract key info from tool results)",
    "reasoning_step": "string (your current thinking)",
    "tool_calls": [
        {"tool": "tool_name", "parameters": {"key": "value"}}
    ]
}

Note: Please do not deviate from this response format. Do not generate additional keys besides "gathered_context", "reasoning_step" and "tool_calls"

CONTEXT EVOLUTION:
- Old tool results are removed after you extract information, because tool results can be bulky
- Your gathered_context entries accumulate across steps and will be laid out after previous tool results
- You can see your previous reasoning and gathered contexts
"""
    
    async def _fetch_chat_history(self, session_id: str) -> str:
        """
        Fetch previous messages from this chat session.
        
        Returns:
            Formatted chat history string (or "No previous messages")
        """
        # Query the database for messages in this session
        # We want messages in chronological order
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
            # Don't load reasoning_steps (would be too much data)
            .limit(40)
        )

        result = await self.db.execute(stmt)
        messages = result.scalars().all()
        
        if not messages:
            return "No previous messages in this session."
        
        # Format messages for the LLM
        formatted_messages = []
        for msg in messages:
            role = "User" if msg.role == "user" else "Assistant"
            formatted_messages.append(f"{role}: {msg.content}")

        history = "\n\n".join(formatted_messages)

        # Keep only the last 20k characters if it's too long
        max_history_chars = 20000
        if len(history) > max_history_chars:
            history = "...[history truncated]...\n" + history[-max_history_chars:]
            
        return history

    async def _fetch_initial_context(self, case_id: int) -> str:
        """
        Fetch the initial context for this case.
        - Generated during preprocessing
        - Case summary and document summaries
        - Includes key information
        - Helps the Planner decide what to search for
        
        Returns
            Initial context strinng (or placeholder if not found
        """        
        # Query the initial_contexts table
        stmt = select(InitialContext).where(InitialContext.case_id == case_id)
        result = await self.db.execute(stmt)
        context = result.scalar_one_or_none()

        if not context:
            print(f"  ⚠️  No initial context found (case might not be preprocessed)")
            return f"Case ID {case_id} (no initial context available)"

        return context.context_text                

    def _build_tool_specifications(self) -> str:
        """
        Build the tool specifications that tell the Planner what tools are available.
        
        This is like giving someone an instruction manual for tools in a toolbox.
        
        Format:
        - Tool name
        - Parameters (what inputs it needs)
        - Use case (when to use it)
        
        Returns:
            Tool specifications strinng
        """
# TOOL 1: semantic_search
# -----------------------
# Purpose: Find chunks using semantic similarity (meaning, not just keywords)
# Parameters:
#   - query: str (1-2 sentence query describing what you're looking for)
#   - case_id: int (automatically provided)

# Returns: Top {TOP_K_SEMANTIC_SEARCH} most relevant chunks with citations
# Use cautiously when you have a very specific queries with which you're sure that the relevant chunks will have particularly high semantic similarity score. Don't use when you only have generic queries, such as "injunction" or "settlement" or "allegations", because they all sound legal-y and a lot of irrelevant chunks would match. If you have generic queries, please look closely at individual document summaries (provided in the initial context) instead.        
        return f"""
TOOL 1: ask_questions_on_document
----------------------------------
Purpose: Invoke a executor LLM agent to answer detailed questions based on a specific document (and only a document among those that have their summaries provided in the context) that you predict will hold the detailed answers to the questions.

Remember:
- Only use the document ID that's specifically listed next to a document summary. Do not use any other form of document ID even if you see other forms of number in the context (for example, Dkt. 77 is not a document ID that this tool can be called on).

Parameters:
  - doc_id: int (specific document to analyze)
  - questions: list[str] (list of questions to answer about the document)
  - planners_context: str (explain why you're asking these questions to help the executor LLM agent have more context)
  - case_id: int (automatically provided)

Returns: Detailed Q&A with citations from the document

Use when: You've identified a relevant document (based on all the document summaries provided in the initial context) and need specific information from it beyond its current summary

Example: ask_questions_on_document(
    doc_id=78342,
    questions=[
        "What was the date of this ruling?",
        "Who was the judge?",
        ... # as many questions as you need - the more the better, because it costs nothing to ask additional questions. It takes the same number of Executor LLM calls anyway.
    ],
    planners_context="User asked about the preliminary injunction timeline"
)
        
        
TOOL 2: keyword_search_by_chunk
-------------------------------
Purpose: Find chunks where ALL specified keywords appear
Parameters:
  - keywords: list[str] (list of specific terms that must ALL appear)
  - case_id: int (automatically provided)
Returns: Chunks containing ALL keywords (max 10)

- Use cautiously only when user asks about very very specific terms, names, dates or phrases. If you search for generic words like "defendents" or "motions", then a lot of irrelevant chunks that contain all of these terms will be returned, and they will be useless to you. Please try to search for at least 4-8 words that should be simultaneously present in the chunk and adjust based on how the search results come back.
- Because keyword search doesn't cost LLM calls, please try to generate multiple keyword searches. All of their results will be returned to you, so you can examine the results immediately in the next reasoning cycle.


NOTE: case_id is automatically added to all tool calls. You don't need to specify it.
"""
            

    async def _call_planner_llm(
        self,
        context: str,
        is_final_answer: bool = False,
        step_number: int = 0
    ) -> PlannerResponse:
        """
        Call the LLM and parse its response into structured format.

        This is the "thinking" step where the Planner:
        1. Analyzes all available context
        2. Decides what information it needs
        3. Chooses which tools to call

        The LLM must output valid JSON matching PlannerResponse structure.
        
        Args:
            context: Full context to send to LLM
            is_final_answer: If True, tell LLM to generate final answer (no tools)
            step_number: Current reasoning step number (for logging)

        Returns:
            Parsed PlannerResponse object

        Raises:
            ValueError: If LLM returns invalid JSON or doesn't match schema
        """
        # Format context as messages
        # OpenAI expects a list of message objects
        messages = [
            {
                "role": "system",
                "content": context
            }
        ]

        # Add special instruction if generating final answer
        if is_final_answer:
            messages.append(
                {
                "role": "user",
                "content": """
You have completed your research. Now generate the FINAL ANSWER.

Do NOT generate tool_calls. Instead:
1. Synthesize all gathered_context from your research
2. Formulate a comprehensive answer to the user's question
3. Include relevant citations in format [CITE:id]
4. Return:
{
    "gathered_context": "Summary of all research findings (with proper citations)",
    "reasoning_step": "I have enough information to answer",
    "tool_calls": []
}
                
"""
                }
            )

        # Determine log source name
        if is_final_answer:
            log_source = "Planner - Final Answer"
        else:
            log_source = f"Planner - Reasoning Step {step_number}"

        # Call LLM API with logging
        try:
            raw_response = await self.llm_service.complete(
                messages=messages,
                model="gpt-5-mini",
                # temperature=0.1,  # Not supported by gpt-5-mini
                # max_tokens=10000,  # Not supported by gpt-5-mini
                response_format={"type": "json_object"},  # Force JSON output (OpenAI feature)
                log_source=log_source,
                case_id=self.current_case_id,
                logger=self.llm_logger
            )
            
        except Exception as e:
            print(f"  ❌ LLM call failed: {e}")
            raise ValueError(f"Failed to call LLM: {e}")

        # Parse and validate response
        try:
            parsed_response = self._parse_planner_response(raw_response)
            return parsed_response
        
        except Exception as e:
            print(f"  ❌ Failed to parse response: {e}")
            print(f"  Raw response: {raw_response[:500]}...")
            raise ValueError(f"Failed to parse LLM response: {e}")     

    def _parse_planner_response(self, raw_response: str) -> PlannerResponse:
        """
        Parse and validate the LLM's JSON response.
        
        This method:
        1. Parses the JSON string
        2. Validates against PlannerResponse schema
        3. Returns typed object (not just a dict)
        
        Why validate?
        - LLM might output invalid JSON
        - LLM might miss required fields
        - We want to fail fast with clear errors
        
        Args:
            raw_response: Raw JSON string from LLM
        
        Returns:
            Validated PlannerResponse object
        
        Raises:
            ValueError: If JSON is invalid or doesn't match schema
        
        Example:
            raw = '{"gathered_context": "...", "reasoning_step": "...", "tool_calls": []}'
            response = self._parse_planner_response(raw)
            # response is now a PlannerResponse object
            print(response.reasoning_step)  # Type-safe access!
        """
        # Parse JSON strinng to Python dict
        try:
            response_dict = json.loads(raw_response)
        except json.JSONDecodeError as e:
            # JSON is malformed (missing comma, bracket, etc.)
            raise ValueError(f"Invalid JSON from LLM: {e}")
         
        # Validate with Pydantic
        try:
            planner_response = PlannerResponse(**response_dict)
        except ValidationError as e:
            # Schema mismatch (missing field, wrong type, etc.)
            raise ValueError(f"LLM response doesn't match schema: {e}")
         
        # Log what we got               
        num_tools = len(planner_response.tool_calls)
        print(f"  📊 Parsed response:")
        print(f"     - Gathered context: {len(planner_response.gathered_context)} chars")
        print(f"     - Reasoning step: {len(planner_response.reasoning_step)} chars")
        print(f"     - Tool calls: {num_tools}")
        
        if num_tools > 0:
            for i, tool_call in enumerate(planner_response.tool_calls, 1):
                print(f"       {i}. {tool_call.tool}")
        
        return planner_response
            

    async def _execute_tools(
        self,
        tool_calls: List[ToolCall],
        case_id: int
    ) -> List[str]:
        """
        Execute a list of tool calls via ExecutorService.

        For each tool call:
        1. Add case_id to parameters (tools need this)
        2. Call ExecutorService.execute_tool()
        3. Collect the result

        Args:
            tool_calls: List of tools to execute
            case_id: Case ID to pass to tools
            
        Returns:
            List of tool results (one per tool call)
        """
        results = []
        for i, tool_call in enumerate(tool_calls, 1):
            # print(f"    Tool {i}/{len(tool_calls)}: {tool_call.tool}")

            # Add case_id to parameters (all tools need this)
            params = dict(tool_call.parameters)
            params["case_id"] = case_id

            try:
                # Call the ExecutorService
                result = await self.executor.execute_tool(
                    tool_name=tool_call.tool,
                    params=params,
                    logger=self.llm_logger
                )            
                results.append(result)
                # Log result size
                # print(f"      ✅ Result: {len(result)} characters")
                
            except Exception as e:
                # Tool execution failed - return error message
                error_msg = f"[ERROR] Tool {tool_call.tool} failed: {str(e)}"
                print(f"      ❌ {error_msg}")
                results.append(error_msg)
        
        return results                
        

    async def _save_to_database(
        self,
        sesion_id: str,
        question: str,
        answer: str,
        state: ReasoningLoopState
    ) -> None:
        """
        Save the complete reasonnig history to database.
        
        This creates:
        - ChatMessage for assistant's response
        - ReasoningStep entries for each step
        
        Args:
            session_id: Which chat session
            question: User's question (already saved)
            answer: Final answer
            state: Complete reasoning loop state
        """
        # TODO: Implement in iteration 6
        pass
