"""
Preprocessing Service.

Orchestrates the entire preprocessing pipeline using a 3-stage approach:
1. Fetch - Get data from Clearinghouse API (no DB interaction)
2. Process - Heavy computation: chunking, embeddings, summarization (no DB interaction)
3. Persist - Save everything to database in ONE TRANSACTION

This is the main service that ties everything together.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.case import Case
from app.services.stages.fetch import FetchStage
from app.services.stages.process import ProcessStage
from app.services.stages.persist import PersistStage


class PreprocessingService:
    """
    Main preprocessing orchestrator.
    
    Now uses a 3-stage pipeline:
    1. Fetch - Get data from API
    2. Process - Heavy computation (chunking, embeddings, summarization)
    3. Persist - Save everything in one transaction
    
    Usage:
        service = PreprocessingService(db_session)
        result = await service.preprocess_case(14919)
    """
    
    def __init__(self):
        # self.db = db
        self.fetch_stage = FetchStage()
        self.process_stage = ProcessStage()
        # self.persist_stage = PersistStage(db)
    
    async def preprocess_case(
        self,
        case_id: int,
        overwrite: bool = False
    ) -> dict:
        """
        Run complete preprocessing pipeline using 3-stage approach.
        
        Benefits of this approach:
        - Can test each stage independently
        - Can save intermediate results for debugging
        - Database only touched once at the end
        - All-or-nothing transaction semantics
        - Can resume from failed stage
        
        Args:
            case_id: Clearinghouse case ID (Integer - this is the primary key)
            overwrite: If True, replace existing case data (not yet implemented)
        
        Returns:
            Dict with preprocessing results
        """
        try:
            # Check if case already exists
            async with AsyncSessionLocal() as session:
                existing = await self._get_existing_case(session, case_id)
                if existing and existing.status == 'ready' and not overwrite:
                    return {
                        "case_id": case_id,
                        "case_name": existing.case_name,
                        "status": "already_exists",
                        "message": f"Case {case_id} already preprocessed",
                    }
            
            # Stage 1: Fetch
            print("\n" + "="*80)
            print("STAGE 1: FETCH")
            print("="*80)
            raw_data = await self.fetch_stage.fetch_case_data(case_id)
            
            # Stage 2: Process (THE SLOW PART - no database interaction!)
            print("\n" + "="*80)
            print("STAGE 2: PROCESS")
            print("="*80)
            processed_data = await self.process_stage.process_case_data(raw_data)
            
            # Optional: Save intermediate results for debugging
            # await self._save_intermediate_results(processed_data)
            
            # Stage 3: Persist (SINGLE TRANSACTION!)
            print("\n" + "="*80)
            print("STAGE 3: PERSIST")
            print("="*80)

            async with AsyncSessionLocal() as session:
                persist_stage = PersistStage(session)
                counts = await persist_stage.persist_case_data(
                    processed_data,
                    overwrite=overwrite
                )
            
            print("\n" + "="*80)
            print("✓ PREPROCESSING COMPLETE")
            print("="*80)
            
            return {
                "case_id": case_id,
                "case_name": processed_data.case_name,
                "status": "success",
                **counts,
                "message": f"Successfully preprocessed case {case_id}"
            }
            
        except Exception as e:
            # In the new architecture, we don't need to update case status
            # because the database was never touched if processing failed
            print(f"\n✗ PREPROCESSING FAILED: {e}")
            raise
    
    async def _get_existing_case(self, session: AsyncSession, case_id: int) -> Optional[Case]:
        """Check if case already exists in database."""
        result = await session.execute(
            select(Case).where(Case.case_id == case_id)
        )
        return result.scalar_one_or_none()
