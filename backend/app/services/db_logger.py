import asyncio
import json
from typing import Optional, Dict, Any, Union, List
from uuid import UUID
from app.db.session import AsyncSessionLocal
from app.models.llm_logs import LLMLog

class DBLLMLogger:
    """
    Logger that persists LLM interaction logs to the database asynchronously.
    
    Design:
    - Maintains context state (session_id, question, etc.) for the current request.
    - Uses fire-and-forget `asyncio.create_task` so logging doesn't block the chat stream.
    - Handles formatting of complex prompt structures (lists/dicts) into text.
    """
    def __init__(self):
        self.session_id: Optional[UUID] = None
        self.question: Optional[str] = None
        self.case_id: Optional[int] = None
        self.parent_message_id: Optional[UUID] = None
        self.call_counter: int = 0

    def start_question_session(
        self,
        session_id: Union[str, UUID],
        question: str,
        parent_message_id: Optional[Union[str, UUID]] = None,
        case_id: Optional[int] = None
    ):
        """
        Initialize context for a new question/turn.

        Args:
            session_id: The chat session ID.
            question: The user's question (context).
            parent_message_id: The ID of the chat message that triggered this (audit link).
            case_id: The case context.
        """
        # Ensure UUIDs are UUID objects
        if isinstance(session_id, str):
            self.session_id = UUID(session_id)
        else:
            self.session_id = session_id

        if isinstance(parent_message_id, str):
            self.parent_message_id = UUID(parent_message_id)
        else:
            self.parent_message_id = parent_message_id

        self.question = question
        self.case_id = case_id
        self.call_counter = 0

    def _format_prompt(self, prompt: Union[str, List[Dict[str, Any]], Dict[str, Any]]) -> str:
        """
        Format prompt for readability, mimicking LLMCallLogger's file output.
        Renders list of messages as [ROLE]\nContent.
        """
        if isinstance(prompt, str):
            return prompt
        
        if isinstance(prompt, list):
            lines = []
            for msg in prompt:
                if isinstance(msg, dict):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    lines.append(f"[{str(role).upper()}]")
                    lines.append(str(content))
                    lines.append("")  # Add spacing between messages
                else:
                    lines.append(str(msg))
            return "\n".join(lines).strip()
            
        # Fallback for dict or other types -> pretty print JSON if possible
        try:
            return json.dumps(prompt, indent=2)
        except Exception:
            return str(prompt)

    async def log_call(
        self,
        source: str,
        prompt: Union[str, List[Dict[str, Any]]],
        response: str,
        metadata: Optional[Dict[str, Any]] = None,
        case_id: Optional[int] = None,
    ):
        """
        Log an LLM call. Fire-and-forget (runs in background)
        """
        if not self.session_id:
            # If logger wasn't started properly, print error but don't crash
            print(f"⚠️ DBLLMLogger not started. Dropping log from {source}")
            return

        # Increment counter immediately so we have the right order
        self.call_counter += 1
        current_step = self.call_counter
        
        # Use session state or override
        effective_case_id = case_id if case_id else self.case_id

        # Convert prompt to string with nice formatting
        prompt_str = self._format_prompt(prompt)

        # Fire and forget task            
        asyncio.create_task(
            self._save_to_db(
                session_id=self.session_id,
                case_id=effective_case_id,
                parent_message_id=self.parent_message_id,
                question=self.question,
                step_number=current_step,
                source=source,
                prompt=prompt_str,
                response=response,
                metadata=metadata
            )
        )

    async def _save_to_db(self, **kwargs):
        """Actual DB write execution."""
        try:
            # Create a dedicated session for this log write
            async with AsyncSessionLocal() as db:
                log_entry = LLMLog(
                    session_id=kwargs.get('session_id'),
                    case_id=kwargs.get('case_id'),
                    parent_message_id=kwargs.get('parent_message_id'),
                    question=kwargs.get('question'),
                    step_number=kwargs.get('step_number'),
                    source=kwargs.get('source'),
                    prompt=kwargs.get('prompt'),
                    response=kwargs.get('response'),
                    metadata_=kwargs.get('metadata') # Note mapped to 'metadata' column via alias
                )
                db.add(log_entry)
                await db.commit()
                # print(f"📝 Logged {kwargs.get('source')} to DB") 

        except Exception as e:
            # Fallback printing if DB log fails (don't crash the app)
            print(f"❌ Failed to write LLM log to DB: {e}")            


# Factory function
def get_db_logger() -> DBLLMLogger:
    return DBLLMLogger()