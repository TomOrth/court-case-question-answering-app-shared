"""
Models for case-related tables:
- cases: Preprocessed case metadata
- case_raw_data: Raw JSON from Clearinghouse API
- initial_contexts: Generated context for Planner agent
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, Text, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.base import Base  # ??? why are we allowed to import "from app.db.base" like this? Shouldn't all imports come from the virtual environment or something

class Case(Base):
    """
    Represents a court case that has been preprocessed.
    
    Fields map to Clearinghouse API case metadata.
    Status tracks preprocessing pipeline stages.
    """

    __tablename__ = 'cases'

    case_id = Column(
        Integer,
        primary_key=True,
        comment="Clearinghouse case ID",
    )

    case_name = Column(
        String(500),
        nullable=False,
        comment="Case name for display"
    )

    court = Column(
        String(255),
        comment="Court name"
    )

    state = Column(
        String(100),
        comment="State"
    )

    filing_date = Column(
        Date,
        comment="Case filing date"
    )

    status = Column(
        String(50),
        nullable=False,
        default='queued',
        comment="Preprocessing status: queued, processing, ready, failed"
    )

    preprocessed_at = Column(
        DateTime(timezone=True),
        comment="When preprocessing completed"
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'processing', 'ready', 'failed')",
            name='valid_status'
        ),
        Index('idx_cases_status', 'status')
    )


class CaseRawData(Base):
    """
    Stores combined JSON from Clearinghouse API v2.
    
    Structure:
    {
        "case": {...},   # GET /api/v2/cases/{id}/
        "documents": {...},   # GET /api/v2/documents/?case={id}
        "dockets": [...],  # GET /api/v2/dockets/?case={id}   
        "resources": [...]  # GET /api/v2/resources/?case={id}
    }
    """
    __tablename__ = 'case_raw_data'

    case_id = Column(Integer, primary_key=True, comment="Links to cases.case_id")
    combined_json = Column(JSONB, nullable=False, comment="Combined API responses")
    fetched_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    __table_args__ = (
        Index(
            'idx_case_raw_data_documents',
            'combined_json',
            postgresql_using='gin',
            postgresql_ops={'combined_json': 'jsonb_path_ops'},
        ),
    )


class InitialContext(Base):
    """
    Stores generated initial context for Planner agent.
    
    This is the starting context that includes:
    - Case metadata summary
    - Document summaries
    - Docket entry summary
    """
    __tablename__ = 'initial_contexts'

    case_id = Column(Integer, primary_key=True, comment="Links to cases.case_id")
    context_text = Column(Text, nullable=False, comment="Full initial context")
    generated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
