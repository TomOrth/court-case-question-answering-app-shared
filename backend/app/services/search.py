"""
Search Service - Semantic and Keyword Search.

This service provides two search capabilities:
1. Semantic search: Find chunks by meaning (uses embeddings + pgvector)
2. Keyword search: Find chunks containing ALL specified keywords

Both methods return chunk with inline citation markers for the Planner.
"""

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload

from app.models.document import Chunk, ChunkEmbedding, Document
from app.schemas.tools import ChunkResult
# from app.services.embeddings import EmbeddingService


TOP_K_SEMANTIC_SEARCH = 10
TOP_K_KEYWORD_SEARCH = 10


class SearchService:
    """
    Service for searching document chunks.
    
    This service is used by the ExecutorService to fulfill search requests from the Planner agent during its reasoning loop.
    """
    def __init__(self, db: AsyncSession):
        """
        Initialize with database session.
        
        Args:
            db: Async SQLAlchemy session for database queries
        """
        self.db = db
        # self.embedding_service = EmbeddingService()

    # async def semantic_search(
    #     self,
    #     query: str,
    #     case_id: int,
    #     top_k: int = TOP_K_SEMANTIC_SEARCH
    # ) -> List[ChunkResult]:
    #     """
    #     Search for chunks using semantic similarity (embeddings + pgvector).

    #     This method:
    #     1. Generates an embedding for the query text
    #     2. Uses pgvector's cosine distance operator (<=>) to find similar chunks
    #     3. Leverages the HNSW index for fast approximate nearest neighbor search
    #     4. Returns chunks with full metadata for the Planner
        
    #     Args:
    #         query: Natural language search query (1-2 sentences work best)
    #         case_id: Limit search to this case only
    #         top_k: Number of results to return (default: 10)
        
    #     Returns:
    #         List of ChunkResult objects, ordered by similarity (highest first)
        
    #     Example:
    #         results = await search_service.semantic_search(
    #             query="What was the court's ruling on the motion to dismiss?",
    #             case_id=14919,
    #             top_k=10
    #         )
    #     """
    #     print(f"  🔍 Semantic search for case {case_id}: '{query[:50]}...'")
        
    #     # STEP 1: Generate embedding for the query
    #     # This converts the text into a 1536-dimensional vector
    #     query_embedding = await self.embedding_service.embed_text(query)
    #     print(f"  📊 Generated embedding: {len(query_embedding)} dimensions")

    #     # STEP 2: Build the SQL query
        
    #     stmt = (
    #         select(
    #             Chunk.chunk_id,
    #             Chunk.chunk_text,
    #             Chunk.doc_id,
    #             Document.title.label('doc_title'),
    #             Document.doc_date,
    #             # Calculate cosine distance and convert to similarity score
    #             (1 - ChunkEmbedding.embedding.cosine_distance(query_embedding)).label('similarity')
    #         )
    #         .join(ChunkEmbedding, Chunk.chunk_id == ChunkEmbedding.chunk_id)
    #         .join(Document, Chunk.doc_id == Document.doc_id)
    #         .where(Chunk.case_id == case_id)
    #         .order_by(ChunkEmbedding.embedding.cosine_distance(query_embedding))
    #         .limit(top_k)
    #     )
        
    #     # STEP 3: Execute the query
    #     result = await self.db.execute(stmt)
    #     rows = result.fetchall()
        
    #     print(f"  ✅ Found {len(rows)} chunks")

    #     # STEP 4: Convert database rows to ChunkResult objects
    #     chunk_results = []
    #     for row in rows:
    #         chunk_results.append(
    #             ChunkResult(
    #                 chunk_id=row.chunk_id,
    #                 chunk_text=row.chunk_text,
    #                 doc_id=row.doc_id,
    #                 doc_title=row.doc_title,
    #                 doc_date=row.doc_date,
    #                 similarity_score=float(row.similarity)
    #             )
    #         )

    #     return chunk_results

    async def keyword_search_by_chunk(
        self,
        keywords: List[str],
        case_id: int,
        max_results: int = TOP_K_KEYWORD_SEARCH
    ) -> List[ChunkResult]:
        """
        Search for chunks containing ALL specified keywords.
        
        This method uses SQL ILIKE pattern matching to find chunks where
        every keyword appears somewhere in the text. The search is:
        - Case-insensitive (ILIKE vs LIKE)
        - AND logic (must match ALL keywords)
        - Ordered by document and chunk position (not by relevance score)
        
        Use this when the Planner needs to find specific terms, names, dates,
        or phrases that must appear together in the text.
        
        Args:
            keywords: List of terms that must ALL appear in the chunk
            case_id: Limit search to this case only
            max_results: Maximum chunks to return (default: 10)
        
        Returns:
            List of ChunkResult objects (no similarity scores)
        
        Example:
            results = await search_service.keyword_search_by_chunk(
                keywords=["Judge Winmill", "2011", "preliminary injunction"],
                case_id=14919,
                max_results=10
            )
        """
        print(f"  🔍 Keyword search for case {case_id}: {keywords}")
        
        # STEP 1: Build the base query
        # We join Chunk with Document to get metadata
        stmt = (
            select(
                Chunk.chunk_id,
                Chunk.chunk_text,
                Chunk.doc_id,
                Document.title.label('doc_title'),
                Document.doc_date
            )
            .join(Document, Chunk.doc_id == Document.doc_id)
            .where(Chunk.case_id == case_id)
        )
        
        # STEP 2: Add a WHERE condition for each keyword
        
        for keyword in keywords:
            # Build the pattern: %keyword%
            pattern = f"%{keyword}%"
            stmt = stmt.where(Chunk.chunk_text.ilike(pattern))
        
        # STEP 3: Order and limit results
        # Order by doc_id and chunk_index to keep chunks from the same
        # document together and in reading order
        stmt = stmt.order_by(Chunk.doc_id, Chunk.chunk_index).limit(max_results)
        
        # STEP 4: Execute the query
        result = await self.db.execute(stmt)
        rows = result.fetchall()
        
        print(f"  ✅ Found {len(rows)} chunks matching ALL keywords")
        
        # STEP 5: Convert to ChunkResult objects
        chunk_results = []
        for row in rows:
            chunk_results.append(ChunkResult(
                chunk_id=row.chunk_id,
                chunk_text=row.chunk_text,
                doc_id=row.doc_id,
                doc_title=row.doc_title,
                doc_date=row.doc_date,
                similarity_score=None  # Keyword search doesn't have similarity
            ))
        
        return chunk_results