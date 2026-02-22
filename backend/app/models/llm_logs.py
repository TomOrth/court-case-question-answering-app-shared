"""
Models for LLM interaction logs.
These logs are an audit trail of Planner Agent reasoning and Executor Tool calls.
They are loosely coupled to sessions (no FK constraints) to ensure persistence.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from app.db.base import Base

class LLMLog(Base):
    """
    Represents a single interaction with an LLM (Planner or Tool).
    """
    __tablename__ = 'llm_logs'

    id = Column(Integer, primary_key=True, index=True)
    
    # Loose references (No ForeignKey constraint)
    # This ensures logs survive even if the session or message is deleted.
    session_id = Column(UUID(as_uuid=True), nullable=False)
    case_id = Column(Integer, nullable=True)
    parent_message_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Request Context
    question = Column(Text, nullable=True, comment="The user question being processed")
    step_number = Column(Integer, nullable=False, default=0)
    source = Column(String(255), nullable=False, comment="E.g. 'Planner - Step 1', 'Executor - Tool: search'")
    
    # LLM Data
    # 'prompt' is TEXT because it contains the massive context string
    prompt = Column(Text, nullable=True)
    response = Column(Text, nullable=True)
    
    metadata_ = Column("metadata", JSONB, nullable=True) # "metadata" is reserved in SQLAlchemy Base
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    __table_args__ = (
        Index('idx_llm_logs_session_id', 'session_id'),
        Index('idx_llm_logs_message_id', 'parent_message_id'),
        Index('idx_llm_logs_created_at', 'created_at'),
    )