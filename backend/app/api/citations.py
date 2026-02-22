"""
Citations API - Fetch citation details for source viewer.

This endpoint handles both chunk citations (from documents) and 
docket entry citations, returning full metadata for display in 
the frontend source viewer sidebar.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from pydantic import BaseModel
from typing import Literal, Union, Optional
from datetime import date

from app.db.session import get_db
from app.models.document import Chunk, Document, DocketEntry

router = APIRouter(prefix="/api/citations", tags=["citations"])

# Response models
class ChunkData(BaseModel):
    chunk_id: str
    chunk_index: int
    chunk_text: str
    case_id: int

    class Config:
        from_attributes = True


class DocumentData(BaseModel):
    doc_id: int
    title: str
    doc_date: Optional[date]
    document_type: Optional[str]
    file_url: Optional[str]
    clearinghouse_link: Optional[str]
    total_chunks: int

    class Config:
        from_attributes = True


class ChunkCitationResponse(BaseModel):
    citation_id: str
    citation_type: Literal["chunk"]
    chunk: ChunkData
    document: DocumentData   


class DocketEntryData(BaseModel):
    docket_entry_id: str
    entry_number: Optional[str]
    date_filed: Optional[date]
    description: str
    url: Optional[str]
    recap_pdf_url: Optional[str]
    case_id: int

    class Config:
        from_attributes = True

class DocketEntryCitationResponse(BaseModel):
    citation_id: str
    citation_type: Literal["docket_entry"]                 
    docket_entry: DocketEntryData

# Endpoint
@router.get("/{citation_id}")
async def get_citation(
    citation_id: str,
    db: AsyncSession = Depends(get_db)
) -> Union[ChunkCitationResponse, DocketEntryCitationResponse]:
    """
    Get full details for a citation ID.
    
    Handles both chunk citations (doc_XXXXX_chunk_XXXXX) 
    and docket entry citations (docket_entry_XXXXX).
    
    Args:
        citation_id: Citation ID to fetch (e.g., "doc_78643_chunk_00001")
        db: Database session
        
    Returns:
        ChunkCitationResponse or DocketEntryCitationResponse
        
    Raises:
        HTTPException 404: Citation not found
        HTTPException 400: Invalid citation ID format
    """
    # Determine citation type based on ID pattern
    if citation_id.startswith("doc_") and "_chunk_" in citation_id:

        # Chunk citation
        result = await db.execute(
            select(Chunk)
            .options(joinedload(Chunk.document))
            .where(Chunk.chunk_id == citation_id)
        )
        chunk = result.scalar_one_or_none()

        if not chunk:
            raise HTTPException(
                status_code=404,
                detail=f"Citation not found: {citation_id}"
            )
        
        # Build response
        return ChunkCitationResponse(
            citation_id=citation_id,
            citation_type="chunk",
            chunk=ChunkData(
                chunk_id=chunk.chunk_id,
                chunk_index=chunk.chunk_index,
                chunk_text=chunk.chunk_text,
                case_id=chunk.case_id,
            ),
            document=DocumentData(
                doc_id=chunk.document.doc_id,
                title=chunk.document.title,
                doc_date=chunk.document.doc_date,
                document_type=chunk.document.document_type,
                file_url=chunk.document.file_url,
                clearinghouse_link=chunk.document.clearinghouse_link,
                total_chunks=chunk.document.total_chunks
            )
        )

    elif "docket_entry_" in citation_id:

        # Docket entry citation
        result = await db.execute(
            select(DocketEntry).where(DocketEntry.docket_entry_id == citation_id)
        )
        docket_entry = result.scalar_one_or_none()

        if not docket_entry:
            raise HTTPException(
                status_code=404,
                detail=f"Citation not found: {citation_id}"
            )        
        
        # Build response
        return DocketEntryCitationResponse(
            citation_id=citation_id,
            citation_type="docket_entry",
            docket_entry=DocketEntryData(
                docket_entry_id=docket_entry.docket_entry_id,
                entry_number=docket_entry.entry_number,
                date_filed=docket_entry.date_filed,
                description=docket_entry.description,
                url=docket_entry.url,
                recap_pdf_url=docket_entry.recap_pdf_url,
                case_id=docket_entry.case_id,
            )
        )

    else:
        # if invalid format
        raise HTTPException(
            status_code=400,
            detail=f"Invalid citation ID format: {citation_id}. "
            f"Expected 'doc_X_chunk_Y' or 'case_X_docket_entry_Y'"
        )
