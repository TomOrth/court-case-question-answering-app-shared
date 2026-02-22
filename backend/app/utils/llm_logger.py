"""
LLM Call Logger - Centralized logging for all LLM interactions.

Logs every LLM call (Planner, Executor) to structured text files with:
- Sequential numbering for chronological ordering
- Full prompt and response content
- Metadata (timestamp, model, duration, etc.)
- Organized by session ID and question

Directory structure:
    llm_call_logs/
        {session_id}/
            {timestamp}_{sanitized_question}/
                001_{timestamp}_planner_initial_context.txt
                002_{timestamp}_planner_step_1_call.txt
                003_{timestamp}_executor_semantic_search.txt
                ...
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import json


class LLMCallLogger:
    """
    Handles all LLM call logging with automatic directory management and sequential numbering.
    
    Usage:
        logger = LLMCallLogger(base_dir="llm_call_logs")
        
        # Start a new question session
        logger.start_question_session(
            session_id="abc-123",
            question="What was the ruling?"
        )
        
        # Log individual calls
        await logger.log_call(
            source="Planner - Reasoning Step 1",
            prompt="...",
            response="...",
            metadata={"model": "gpt-4o-mini", "duration": 2.3}
        )
    """
    
    def __init__(self, base_dir: str = "llm_call_logs"):
        """
        Initialize the logger.
        
        Args:
            base_dir: Base directory for all logs (relative to backend root)
        """
        self.base_dir = Path(base_dir)
        self.current_session_id: Optional[str] = None
        self.current_question_dir: Optional[Path] = None
        self.call_counter: int = 0
        
    def start_question_session(
        self,
        session_id: str,
        question: str,
        case_id: Optional[int] = None
    ):
        """
        Start a new question logging session.
        
        Creates a new directory for this question with timestamp and sanitized question name.
        Resets the call counter.
        
        Args:
            session_id: Chat session ID
            question: User's question (will be sanitized for filename)
            case_id: Optional case ID for reference
        """
        self.current_session_id = session_id
        self.call_counter = 0
        
        # Create session directory
        session_dir = self.base_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create question directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sanitized_question = self._sanitize_filename(question)
        question_dir_name = f"{timestamp}_{sanitized_question}"
        
        self.current_question_dir = session_dir / question_dir_name
        self.current_question_dir.mkdir(parents=True, exist_ok=True)
        
        # Write a README with the full question
        readme_path = self.current_question_dir / "README.txt"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("QUESTION SESSION LOG\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Session ID: {session_id}\n")
            if case_id:
                f.write(f"Case ID: {case_id}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"\nQuestion:\n{question}\n")
            f.write("\n" + "=" * 80 + "\n")
            f.write("This folder contains sequential logs of all LLM calls\n")
            f.write("Files are numbered chronologically: 001_, 002_, 003_...\n")
            f.write("=" * 80 + "\n")
    
    async def log_call(
        self,
        source: str,
        prompt: str,
        response: str,
        metadata: Optional[Dict[str, Any]] = None,
        case_id: Optional[int] = None
    ):
        """
        Log a single LLM call to file.
        
        Args:
            source: Description of the call source (e.g., "Planner - Step 1", "Executor - Semantic Search")
            prompt: Full prompt sent to LLM (can be string or list of messages)
            response: Response from LLM
            metadata: Optional metadata (model, temperature, duration, etc.)
            case_id: Optional case ID
        """
        if not self.current_question_dir:
            raise RuntimeError("Must call start_question_session() before logging calls")
        
        # Increment counter
        self.call_counter += 1
        
        # Format filename
        timestamp = datetime.now().strftime("%H%M%S")
        sanitized_source = self._sanitize_filename(source)
        filename = f"{self.call_counter:03d}_{timestamp}_{sanitized_source}.txt"
        
        filepath = self.current_question_dir / filename
        
        # Format and write content
        content = self._format_log_content(
            source=source,
            prompt=prompt,
            response=response,
            metadata=metadata,
            case_id=case_id
        )
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _format_log_content(
        self,
        source: str,
        prompt: str,
        response: str,
        metadata: Optional[Dict[str, Any]],
        case_id: Optional[int]
    ) -> str:
        """
        Format the log file content in a readable structure.
        
        Returns:
            Formatted string ready to write to file
        """
        lines = []
        
        # Header
        lines.append("=" * 80)
        lines.append("LLM CALL LOG")
        lines.append("=" * 80)
        lines.append(f"Timestamp: {datetime.now().isoformat()}")
        lines.append(f"Session ID: {self.current_session_id}")
        if case_id:
            lines.append(f"Case ID: {case_id}")
        lines.append(f"Source: {source}")
        lines.append(f"Call Number: {self.call_counter}")
        
        # Metadata
        if metadata:
            lines.append("")
            lines.append("-" * 80)
            lines.append("METADATA")
            lines.append("-" * 80)
            for key, value in metadata.items():
                lines.append(f"{key}: {value}")
        
        # Prompt section
        lines.append("")
        lines.append("=" * 80)
        lines.append("PROMPT")
        lines.append("=" * 80)
        lines.append("")
        
        # Handle prompt - could be string or list of messages
        if isinstance(prompt, str):
            lines.append(prompt)
        elif isinstance(prompt, list):
            # Format as messages
            for msg in prompt:
                if isinstance(msg, dict):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    lines.append(f"[{role.upper()}]")
                    lines.append(content)
                    lines.append("")
                else:
                    lines.append(str(msg))
        else:
            lines.append(str(prompt))
        
        # Response section
        lines.append("")
        lines.append("=" * 80)
        lines.append("RESPONSE")
        lines.append("=" * 80)
        lines.append("")
        lines.append(response)
        
        # Footer
        lines.append("")
        lines.append("=" * 80)
        lines.append("END OF LOG")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def _sanitize_filename(self, text: str, max_length: int = 50) -> str:
        """
        Sanitize text for use in filename.
        
        - Converts to lowercase
        - Replaces spaces with underscores
        - Removes special characters
        - Truncates to max_length
        
        Args:
            text: Text to sanitize
            max_length: Maximum length of resulting filename part
            
        Returns:
            Sanitized string safe for filename
        """
        # Convert to lowercase
        text = text.lower()
        
        # Replace spaces and common punctuation with underscores
        text = re.sub(r'[\s\-\.]+', '_', text)
        
        # Remove any characters that aren't alphanumeric or underscore
        text = re.sub(r'[^\w]', '', text)
        
        # Remove multiple consecutive underscores
        text = re.sub(r'_+', '_', text)
        
        # Strip leading/trailing underscores
        text = text.strip('_')
        
        # Truncate to max length
        if len(text) > max_length:
            text = text[:max_length]
        
        # Ensure we have something (fallback)
        if not text:
            text = "unnamed"
        
        return text
    
    def get_current_question_dir(self) -> Optional[Path]:
        """Get the current question directory path."""
        return self.current_question_dir
    
    def get_call_count(self) -> int:
        """Get the current call counter value."""
        return self.call_counter


def get_llm_logger(base_dir: str = "llm_call_logs") -> LLMCallLogger:
    """
    Create a new logger instance for a question session.
    
    Each call returns a NEW instance to avoid race conditions
    when multiple requests are processed concurrently.
    
    Args:
        base_dir: Base directory for logs
        
    Returns:
        New LLMCallLogger instance
    """
    return LLMCallLogger(base_dir)
