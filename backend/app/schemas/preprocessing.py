"""
Pydantic schemas for preprocessing API.
"""

from pydantic import BaseModel
from typing import Optional


class PreprocessCaseRequest(BaseModel):
    """Request to preprocess a case."""
    case_id: int


class PreprocessCaseResponse(BaseModel):
    """Response from preprocessing."""    
    case_id: int
    case_name: str
    status: str
    documents_count: int
    chunks_count: int
    # embeddings_count: int
    docket_entries_count: int
    message: str


class CaseStatusResponse(BaseModel):
    """Response showing case preprocessing status."""    
    case_id: int
    case_name: Optional[str]
    status: str  # queued, processing, ready, failed
    documents_count: int
    chunks_count: int
