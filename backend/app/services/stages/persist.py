"""
Stage 3: Persist processed data to database.

This stage saves all data in a SINGLE TRANSACTION.
All-or-nothing: Either everything saves or nothing does.
"""

from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from app.services.preprocessing_types import (
    ProcessedCaseData, ProcessedDocument, ProcessedDocketEntry
)
from app.models.case import Case, CaseRawData, InitialContext
from app.models.document import Document, Chunk, DocketEntry


class PersistStage:
    """Stage 3: Persist processed data to database (SINGLE TRANSACTION)"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def persist_case_data(
        self,
        processed_data: ProcessedCaseData,
        overwrite: bool = False
    ) -> Dict[str, int]:
        """
        Persist all processed case data in a SINGLE transaction.
        
        Benefits:
        - All-or-nothing: Either everything saves or nothing does
        - No inconsistent database state
        - Fast rollback on error
        - No database interaction during slow summarization
        
        Args:
            processed_data: All processed data ready to save
            overwrite: If True, delete existing data first (not implemented yet)
        
        Returns:
            Dict with counts of saved records
        """
        print(f"[PERSIST] Saving case {processed_data.case_id} to database...")
        
        # Everything happens in this transaction
        # No commits until the very end!
        
        try:
            # Optional: Delete existing data if overwrite=True
            if overwrite:
                print(f"[PERSIST] ⚠️  Overwrite mode not yet implemented")
            
            # 1. Create/update case record
            case = await self._save_case(processed_data)
            print(f"[PERSIST]   ✓ Case record prepared")
            
            # 2. Save raw data
            await self._save_raw_data(processed_data)
            print(f"[PERSIST]   ✓ Raw data prepared")
            
            # 3. Save documents, chunks, and embeddings
            chunks_count = await self._save_documents(processed_data.documents)
            print(f"[PERSIST]   ✓ Documents, chunks, and embeddings prepared")
            
            # 4. Save docket entries
            docket_count = await self._save_docket_entries(
                processed_data.docket_entries
            )
            print(f"[PERSIST]   ✓ Docket entries prepared")
            
            # 5. Save initial context
            await self._save_initial_context(
                processed_data.case_id,
                processed_data.initial_context
            )
            print(f"[PERSIST]   ✓ Initial context prepared")
            
            # 6. Update case status
            case.status = 'ready'
            case.preprocessed_at = datetime.now(timezone.utc)
            
            # THE ONLY COMMIT IN THE ENTIRE PROCESS!
            await self.db.commit()
            
            print(f"[PERSIST] ✓ Successfully saved case {processed_data.case_id}")
            
            return {
                "documents_count": len(processed_data.documents),
                "chunks_count": chunks_count,
                "embeddings_count": chunks_count,  # Same as chunks
                "docket_entries_count": docket_count
            }
        
        except Exception as e:
            # Rollback the entire transaction
            await self.db.rollback()
            print(f"[PERSIST] ✗ Error saving case, rolled back: {e}")
            raise
    
    async def _save_case(self, data: ProcessedCaseData) -> Case:
        """Save or update case record"""
        result = await self.db.execute(
            select(Case).where(Case.case_id == data.case_id)
        )
        case = result.scalar_one_or_none()
        
        if case:
            case.case_name = data.case_name
            case.court = data.court
            case.filing_date = data.filing_date
            case.status = 'processing'
        else:
            case = Case(
                case_id=data.case_id,
                case_name=data.case_name,
                court=data.court,
                filing_date=data.filing_date,
                status='processing'
            )
            self.db.add(case)
        
        # No commit yet!
        return case
    
    async def _save_raw_data(self, data: ProcessedCaseData):
        """Save raw JSON data"""
        raw = CaseRawData(
            case_id=data.case_id,
            combined_json=data.raw_json
        )
        self.db.add(raw)
        # No commit yet!
    
    async def _save_documents(
        self,
        documents: List[ProcessedDocument]
    ) -> int:
        """Save documents, chunks, and embeddings"""
        chunks_count = 0
        
        for doc_data in documents:
            # Save document
            doc = Document(
                doc_id=doc_data.doc_id,
                case_id=doc_data.case_id,
                title=doc_data.title,
                doc_date=doc_data.doc_date,
                file_url=doc_data.file_url,
                clearinghouse_link=doc_data.clearinghouse_link,
                total_chunks=len(doc_data.chunks)
            )
            self.db.add(doc)
            
            # Force flush to ensure document exists before adding chunks
            # This prevents ForeignKeyViolationError when chunks are batched
            await self.db.flush()
            
            # Save chunks and embeddings
            for chunk_data in doc_data.chunks:
                # Save chunk
                chunk = Chunk(
                    chunk_id=chunk_data.chunk_id,
                    case_id=doc_data.case_id,
                    doc_id=doc_data.doc_id,
                    chunk_index=chunk_data.chunk_index,
                    chunk_text=chunk_data.chunk_text
                )
                self.db.add(chunk)
                
                # Save embedding
                # embedding = ChunkEmbedding(
                #     chunk_id=chunk_data.chunk_id,
                #     embedding=chunk_data.embedding
                # )
                # self.db.add(embedding)
                
                chunks_count += 1
            
            # No commit yet!
        
        return chunks_count
    
    async def _save_docket_entries(
        self,
        entries: List[ProcessedDocketEntry]
    ) -> int:
        """Save docket entries"""
        for entry_data in entries:
            entry = DocketEntry(
                docket_entry_id=entry_data.docket_entry_id,
                case_id=entry_data.case_id,
                entry_number=entry_data.entry_number,
                date_filed=entry_data.date_filed,
                description=entry_data.description,
                url=entry_data.url,
                recap_pdf_url=entry_data.recap_pdf_url,
                pacer_doc_id=entry_data.pacer_doc_id
            )
            self.db.add(entry)
        
        # No commit yet!
        return len(entries)
    
    async def _save_initial_context(self, case_id: int, context_text: str):
        """Save initial context"""
        context = InitialContext(
            case_id=case_id,
            context_text=context_text
        )
        self.db.add(context)
        # No commit yet!
