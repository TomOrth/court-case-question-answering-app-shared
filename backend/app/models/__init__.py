"""
Import all models to ensure they're registered with Base.metadata.

This file is crucial for Alembic autogenerate to detect all tables.

How it works:
1. Python only loads modules when explicitly imported
2. Without this file, models exist but aren't "registered"
3. Alembic scans Base.metadata to find tables
4. Base.metadata only knows about imported models
5. This file imports everything, making models visible to Alembic
"""

# Import all models from their respective files
# Case-related models (from case.py)
from app.models.case import Case, CaseRawData, InitialContext

# Document-related models (from document.py)
from app.models.document import Document, Chunk, DocketEntry

# Chat-related models (from chat.py)
from app.models.chat import ChatSession, ChatMessage, ReasoningStep

# Logging model (from logs.py)
from app.models.http_logs import HTTPRequestLog
from app.models.llm_logs import LLMLog

__all__ = [
    'Case',
    'CaseRawData',
    'InitialContext',
    'Document',
    'Chunk',
    # 'ChunkEmbedding',
    'DocketEntry',
    'ChatSession',
    'ChatMessage',
    'ReasoningStep',
    'HTTPRequestLog',
    'LLMLog',
]