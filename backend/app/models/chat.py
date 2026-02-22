"""
Models for chat-related tables:
- chat_sessions: User chat sessions
- qa_pairs: Question-answer pairs
- reasoning_steps: Detailed reasoning logs
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from app.db.base import Base
import enum

# Define Enum for Message Roles
class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatSession(Base):
    """
    Represents a chat session between a suser and the system.
    
    Sessions are publicly sharable via URL but only owner can ask questions.
    """
    __tablename__ = 'chat_sessions'
    session_id = Column(UUID(as_uuid=True),
                        primary_key=True,
                        default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        comment="References auth.users.id (Supabase Auth)"
    )
    case_id = Column(
        Integer,
        ForeignKey('cases.case_id', ondelete='RESTRICT'),
        nullable=False
    )
    session_title = Column(
        String(255),
        nullable=False,
        comment="Display in sidebar"
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    from sqlalchemy.orm import relationship
    case = relationship("Case")

    messages = relationship("ChatMessage", back_populates="session", order_by="ChatMessage.created_at", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_chat_sessions_user_id', 'user_id'),
        Index('idx_chat_sessions_case_id', 'case_id'),
        Index('idx_chat_sessions_updated', 'user_id', 'updated_at')
    )


# class QAPair(Base):
#     """
#     Represents a question-answer pair within a chat session.
    
#     Answer contains embedded citations in format [CITE:citation_id]

#     Example:
#     Question: "What did the court decide about the motion?"
#     Answer: "The court granted the motion [CITE:doc_123_chunk_00045] based on 
#              precedent [CITE:doc_124_chunk_00012]."
    
#     The frontend will replace [CITE:...] with clickable citation buttons.

#     """    
#     __tablename__ = 'qa_pairs'
#     qa_id = Column(
#         UUID(as_uuid=True),
#         primary_key=True,
#         default=uuid.uuid4
#     )
#     session_id = Column(
#         UUID(as_uuid=True),
#         ForeignKey('chat_sessions.session_id', ondelete='CASCADE'),
#         nullable=False
#     )
#     question = Column(
#         Text,
#         nullable=False,
#         comment="User's question"
#     )
#     answer = Column(
#         Text,
#         nullable=False,
#         comment="Final answer with [CITE:...] markers"
#     )
#     created_at = Column(
#         DateTime(timezone=True),
#         nullable=False,
#         server_default=func.now()
#     )

#     __table_args__ = (
#         Index('idx_qa_pairs_session_id', 'session_id'),
#         Index('idx_qa_pairs_session_created', 'session_id', 'created_at'),
#     )

class ChatMessage(Base):
    """
    Represents a single message in the chat history.
    """
    __tablename__ = 'chat_messages'

    message_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey('chat_sessions.session_id', ondelete='CASCADE'),
        nullable=False
    )
    role = Column(
        String(50),  # 'user', 'assistant', 'system'
        nullable=False,
    )
    content = Column(
        Text,
        nullable=False,
        default=""  # Assistant messages might start empty while streaming
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # Relationships
    from sqlalchemy.orm import relationship
    session = relationship("ChatSession", back_populates="messages")
    reasoning_steps = relationship("ReasoningStep", back_populates="message", cascade="all, delete-orphan", order_by="ReasoningStep.step_order")

    __table_args__ = (
        Index('idx_chat_messages_session_id', 'session_id'),
        Index('idx_chat_messages_created', 'session_id', 'created_at'),
        CheckConstraint("role IN ('user', 'assistant', 'system')", name='valid_role')
    )


class ReasoningStep(Base):
    """
    Stores detailed reasoning steps for expandable UI.

    This enables "show reasoning" feature where user can see:
    - What context was gathered
    - What tools were called
    - What the AI was thinking step-by-step
    
    step_type determines step_data structure:
    - gathered_context: {"content": "Initial case summary: ..."}
    - reasoning_step: {"step_number": 1, "content": "First, I need to find..."}
    - tool_call: {"id": "tc_001", "tool": "semantic_search", "parameters": {"query": "..."}}
    - tool_result: {"tool_id": "tc_001", "content": "Found 5 chunks..."}
    
    Example flow:
    1. gathered_context: "Here's what I know about the case..."
    2. reasoning_step: "To answer this, I need to search for motions..."
    3. tool_call: semantic_search(query="motion to dismiss")
    4. tool_result: [list of relevant chunks]
    5. reasoning_step: "Based on the results, the answer is..."    
    
    """
    __tablename__ = 'reasoning_steps'
    step_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    # qa_id = Column(
    #     UUID(as_uuid=True),
    #     ForeignKey(
    #         'qa_pairs.qa_id',
    #         ondelete='CASCADE'
    #     ),
    #     nullable=False
    # )
    message_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            'chat_messages.message_id',
            ondelete='CASCADE'
        ),
        nullable=False
    )
    step_order = Column(
        Integer,
        nullable=False,
        comment="Order within Q&A"
    )
    step_type = Column(
        String(50),
        nullable=False
        # One of 'gathered_context', 'reasoning_step', 'tool_call', 'tool_result'
    )
    step_data = Column(
        JSONB,
        nullable=False,
        comment="Step-specific data"
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # Relationships
    from sqlalchemy.orm import relationship
    message = relationship("ChatMessage", back_populates="reasoning_steps")

    __table_args__ = (
        CheckConstraint(
            "step_type IN ('gathered_context', 'reasoning', 'tool_call', 'tool_result')",
            name='valid_step_type'
        ),
        Index('idx_reasoning_steps_message_id', 'message_id'),
        Index('idx_reasoning_steps_order', 'message_id', 'step_order')
    )