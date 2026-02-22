"""
Models for document-related tables:
- documents: Document metadata
- chunks: Text chunks for retrieval
- chunk_embeddings: Vector embeddings for semantic search
- docket_entries: Docket entry records
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, Text, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from pgvector.sqlalchemy import Vector

from app.db.base import Base

class Document(Base):
    """
    Represents a document within a case.
    
    Stores metadata for citation display in sidebar.
    """
    __tablename__ = 'documents'

    doc_id = Column(Integer, primary_key=True, comment="Clearinghouse document ID")
    case_id = Column(Integer, ForeignKey('cases.case_id', ondelete='CASCADE'), nullable=False)
    title = Column(String(500), nullable=False, comment="Document title")
    doc_date = Column(Date, comment="Document date")
    document_type = Column(String(100), comment="Document type (e.g., Court Order)")
    file_url = Column(String(1000), comment="PDF download URL")
    clearinghouse_link = Column(String(1000), comment="Clearinghouse view URL")
    total_chunks = Column(Integer, nullable=False, default=0, comment="Total chunks for 'X of Y' display")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    chunks = relationship("Chunk", back_populates="document")
    
    __table_args__ = (
        Index('idx_documents_case_id', 'case_id'),
    )


class Chunk(Base):
    """
    Represents a chunk of document text.
    
    chunk_id format: doc_{doc_id}_chunk_{5-digit index}
    Example: doc_78643_chunk_00012
    
    """
    __tablename__ = 'chunks'
    chunk_id = Column(String(50), primary_key=True, comment="Citation ID")
    case_id = Column(Integer, ForeignKey('cases.case_id', ondelete='CASCADE'), nullable=False)
    doc_id = Column(Integer, ForeignKey('documents.doc_id', ondelete='CASCADE'), nullable=False)
    chunk_index = Column(Integer, nullable=False, comment="Position in document (0-indexed)")
    chunk_text = Column(Text, nullable=False, comment="Full chunk text")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="chunks")

    __table_args__ = (
        UniqueConstraint('doc_id', 'chunk_index', name='unique_doc_chunk'),
        Index('idx_chunks_case_id', 'case_id'),
        Index('idx_chunks_doc_id', 'doc_id'),
    )


class ChunkEmbedding(Base):
    """
    Stores vector embeddings for semantic search.
    
    Uses pgvector extension for effficient similarity search.
    Dimension: 1536 (OpenAI text-embedding-3-small)
    """
    __tablename__ = 'chunk_embeddings'

    chunk_id = Column(String(50), ForeignKey('chunks.chunk_id', ondelete='CASCADE'), primary_key=True)
    embedding = Column(Vector(1536), nullable=False, comment="OpenAI embedding vector")
    __table_args__ = (
        Index(
            'idx_chunk_embeddings_hnsw',
            'embedding',
            postgresql_using='hnsw',
            postgresql_with={
                'm': 16,
                'ef_construction': 64
            },
            postgresql_ops={
                'embedding': 'vector_cosine_ops'
            }
        ),
    )


class DocketEntry(Base):
    """
    Represents a docket entry within a case
    
    docket_entry_id format: case_{case_id}_docket_entry_{5-digit index}
    Example: case_46766_docket_entry_00175
    """    
    __tablename__ = 'docket_entries'
    docket_entry_id = Column(String(50), primary_key=True, comment="Citation ID")
    case_id = Column(Integer, ForeignKey('cases.case_id', ondelete='CASCADE'), nullable=False,)
    entry_number = Column(String(20), comment="Docket entry number")
    date_filed = Column(Date, comment="Filing date")
    description = Column(Text, nullable=False, comment="Full docket entry text")
    url = Column(String(1000), comment="CourtListener URL")
    recap_pdf_url = Column(String(1000), comment="RECAP PDF URL")
    pacer_doc_id = Column(String(50), comment="PACER document ID")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    __table_args__ = (
        Index('idx_docket_entries_case_id', 'case_id'),
        Index('idx_docket_entries_date', 'case_id', 'date_filed')
    )