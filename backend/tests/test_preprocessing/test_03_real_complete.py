"""
Real integration test: Complete preprocessing pipeline for case 14919.
"""

import pytest
import json
from pathlib import Path
from sqlalchemy import select

from app.services.preprocessing import PreprocessingService
from app.models.case import Case, CaseRawData, InitialContext
from app.models.document import Document, Chunk, ChunkEmbedding, DocketEntry


# Output directory for test results
OUTPUT_DIR = Path(__file__).parent / "test_outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# Test with real case ID
REAL_CASE_ID = 14919


class TestRealPreprocessingPipeline:
    """Test complete preprocessing pipeline with real case 14919."""
    
    @pytest.mark.asyncio
    async def test_complete_pipeline_case_14919(self, db_session):
        """
        Run complete preprocessing pipeline for case 14919.
        
        This test:
        1. Fetches real data from Clearinghouse API
        2. Processes (chunks, embeds, summarizes) using real services
        3. Saves to database in single transaction
        
        WARNING: This test takes several minutes to run!
        """
        print(f"\n{'='*80}")
        print(f"COMPLETE PREPROCESSING PIPELINE - CASE {REAL_CASE_ID}")
        print(f"{'='*80}")
        print(f"\nWARNING: This will take several minutes (summarization is slow)")
        print(f"\n")
        
        # Run complete preprocessing
        service = PreprocessingService(db_session)
        result = await service.preprocess_case(REAL_CASE_ID)
        
        # Verify result
        assert result['status'] == 'success'
        assert result['case_id'] == REAL_CASE_ID
        assert result['documents_count'] > 0
        assert result['chunks_count'] > 0
        
        print(f"\n{'='*80}")
        print(f"PIPELINE COMPLETE")
        print(f"{'='*80}")
        print(f"\nResults:")
        print(f"  Case: {result['case_name']}")
        print(f"  Documents: {result['documents_count']}")
        print(f"  Chunks: {result['chunks_count']}")
        print(f"  Embeddings: {result['embeddings_count']}")
        print(f"  Docket Entries: {result['docket_entries_count']}")
        
        # Verify database state
        print(f"\nVerifying database...")
        
        # Check case
        case_result = await db_session.execute(
            select(Case).where(Case.case_id == REAL_CASE_ID)
        )
        case = case_result.scalar_one_or_none()
        assert case is not None
        assert case.status == 'ready'
        print(f"  ✓ Case record: {case.case_name}")
        
        # Check raw data
        raw_result = await db_session.execute(
            select(CaseRawData).where(CaseRawData.case_id == REAL_CASE_ID)
        )
        raw_data = raw_result.scalar_one_or_none()
        assert raw_data is not None
        print(f"  ✓ Raw data saved")
        
        # Check documents
        docs_result = await db_session.execute(
            select(Document).where(Document.case_id == REAL_CASE_ID)
        )
        docs = docs_result.scalars().all()
        print(f"  ✓ Documents: {len(docs)}")
        
        # Check chunks
        chunks_result = await db_session.execute(
            select(Chunk).where(Chunk.case_id == REAL_CASE_ID)
        )
        chunks = chunks_result.scalars().all()
        print(f"  ✓ Chunks: {len(chunks)}")
        
        # Check embeddings
        embeddings_result = await db_session.execute(
            select(ChunkEmbedding)
        )
        all_embeddings = embeddings_result.scalars().all()
        case_embeddings = [e for e in all_embeddings if any(c.chunk_id == e.chunk_id for c in chunks)]
        print(f"  ✓ Embeddings: {len(case_embeddings)}")
        
        # Check docket entries
        docket_result = await db_session.execute(
            select(DocketEntry).where(DocketEntry.case_id == REAL_CASE_ID)
        )
        docket_entries = docket_result.scalars().all()
        print(f"  ✓ Docket entries: {len(docket_entries)}")
        
        # Check initial context
        context_result = await db_session.execute(
            select(InitialContext).where(InitialContext.case_id == REAL_CASE_ID)
        )
        context = context_result.scalar_one_or_none()
        assert context is not None
        print(f"  ✓ Initial context: {len(context.context_text)} chars")
        
        # Save comprehensive results
        output_file = OUTPUT_DIR / f"03_complete_pipeline_case_{REAL_CASE_ID}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'case_id': REAL_CASE_ID,
                'preprocessing_result': result,
                'database_verification': {
                    'case': {
                        'id': case.case_id,
                        'name': case.case_name,
                        'status': case.status,
                        'court': case.court,
                        'filing_date': str(case.filing_date) if case.filing_date else None,
                        'preprocessed_at': case.preprocessed_at.isoformat() if case.preprocessed_at else None
                    },
                    'raw_data_exists': raw_data is not None,
                    'documents': [
                        {
                            'doc_id': doc.doc_id,
                            'title': doc.title,
                            'total_chunks': doc.total_chunks,
                            'doc_date': str(doc.doc_date) if doc.doc_date else None
                        }
                        for doc in docs
                    ],
                    'chunks_count': len(chunks),
                    'embeddings_count': len(case_embeddings),
                    'docket_entries_count': len(docket_entries),
                    'initial_context_length': len(context.context_text)
                }
            }, f, indent=2, default=str)
        
        print(f"\n✓ Results saved to: {output_file}")
        
        # Save initial context
        context_file = OUTPUT_DIR / f"03_final_initial_context_case_{REAL_CASE_ID}.txt"
        with open(context_file, 'w', encoding='utf-8') as f:
            f.write(context.context_text)
        
        print(f"✓ Initial context saved to: {context_file}")
        
        # Save sample chunks
        chunks_file = OUTPUT_DIR / f"03_sample_chunks_case_{REAL_CASE_ID}.json"
        with open(chunks_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total_chunks': len(chunks),
                'sample_chunks': [
                    {
                        'chunk_id': chunk.chunk_id,
                        'doc_id': chunk.doc_id,
                        'chunk_index': chunk.chunk_index,
                        'text_preview': chunk.chunk_text[:200] + '...' if len(chunk.chunk_text) > 200 else chunk.chunk_text,
                        'text_length': len(chunk.chunk_text)
                    }
                    for chunk in chunks[:10]  # First 10 chunks
                ]
            }, f, indent=2)
        
        print(f"✓ Sample chunks saved to: {chunks_file}")
        
        print(f"\n{'='*80}")
        print(f"ALL DATA SAVED AND VERIFIED")
        print(f"{'='*80}\n")
