"""
Preprocessing API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.core.auth import get_current_user
from app.models.case import Case
from app.schemas.preprocessing import (
    PreprocessCaseRequest,
    PreprocessCaseResponse,
    CaseStatusResponse,
)
from app.services.preprocessing import PreprocessingService

router = APIRouter(prefix="/api/preprocessing", tags=["preprocessing"])

@router.post("/case", response_model=PreprocessCaseResponse)
async def preprocess_case(
    request: PreprocessCaseRequest,
    # db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
):
    """
    Trigger preprocessing for a court case.
    
    This will:
    1. Fetch case data from Clearinghouse API
    2. Store documents and chunk them
    3. Generate embeddings for semantic search
    4. Store docket entries
    5. Build initial context for the Planner
    """
    service = PreprocessingService()
    try:
        result = await service.preprocess_case(
            case_id=request.case_id,
            # user_id=user.id
        )

        return PreprocessCaseResponse(
            case_id=result["case_id"],
            case_name=result.get("case_name", "Unknown"),
            status=result["status"],
            documents_count=result.get("documents_count", 0),
            chunks_count=result.get("chunks_count", 0),
            # embeddings_count=result.get("embeddings_count", 0), 
            docket_entries_count=result.get("docket_entries_count", 0),
            message=result["message"],
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/case/{case_id}/status", response_model=CaseStatusResponse)
async def get_case_status(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
):
    """
    Get preprocessing status for a case.
    
    Returns status: queued, processing, ready or failed.
    """
    result = await db.execute(
        select(Case).where(Case.case_id == case_id)
    )
    case = result.scalar_one_or_none()

    if not case:
        return CaseStatusResponse(
            case_id=case_id,
            case_name=None,
            status="not_found",
            documents_count=0,
            chunks_count=0
        )
    
    # Count documents and chunks
    from app.models.document import Document, Chunk

    docs_result = await db.execute(
        select(Document).where(Document.case_id == case.case_id)
    )    
    docs_count = len(docs_result.scalars().all())

    return CaseStatusResponse(
        case_id=case_id,
        case_name=case.case_name,
        status=case.status,
        documents_count=docs_count,
        chunks_count=0,  # TODO: Add chunk count query
    )

@router.get("/cases", response_model=list[CaseStatusResponse])
async def list_preprocessed_cases(
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
):
    """List all preprocessed cases."""
    result = await db.execute(select(Case))
    cases = result.scalars().all()

    return [
        CaseStatusResponse(
            case_id=case.case_id,
            case_name=case.case_name,
            status=case.status,
            documents_count=0,  # TODO: Add count
            chunks_count=0
        )
        for case in cases
    ]