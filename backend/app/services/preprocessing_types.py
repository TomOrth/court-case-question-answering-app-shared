"""
Data classes for preprocessing pipeline.

These are pure Python objects with no database dependencies.
They represent data as it flows through the pipeline stages.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import date


@dataclass
class RawCaseData:
    """Raw data fetched from Clearinghouse API"""
    case_id: int
    case_meta: Dict
    documents: List[Dict]
    dockets: List[Dict]


@dataclass
class ProcessedChunk:
    """A single processed chunk with its embedding"""
    chunk_id: str
    doc_id: int
    chunk_index: int
    chunk_text: str
    # embedding: List[float]


@dataclass
class ProcessedDocument:
    """A processed document with metadata and chunks"""
    doc_id: int
    case_id: int
    title: str
    doc_date: Optional[date]
    file_url: Optional[str]
    clearinghouse_link: Optional[str]
    summary: str  # AI-generated summary with citations
    chunks: List[ProcessedChunk]


@dataclass
class ProcessedDocketEntry:
    """A processed docket entry"""
    docket_entry_id: str
    case_id: int
    entry_number: Optional[int]
    date_filed: Optional[date]
    description: str
    url: Optional[str]
    recap_pdf_url: Optional[str]
    pacer_doc_id: Optional[str]


@dataclass
class ProcessedCaseData:
    """Complete processed case data ready for persistence"""
    case_id: int
    case_name: str
    court: Optional[str]
    filing_date: Optional[date]
    raw_json: Dict
    documents: List[ProcessedDocument]
    docket_entries: List[ProcessedDocketEntry]
    initial_context: str
