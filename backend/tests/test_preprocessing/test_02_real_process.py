"""
Real integration test: Process actual case 14919 data.
"""

import pytest
import json
from pathlib import Path

from app.services.stages.fetch import FetchStage
from app.services.stages.process import ProcessStage
from app.services.preprocessing_types import ProcessedCaseData


# Output directory for test results
OUTPUT_DIR = Path(__file__).parent / "test_outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# Test with real case ID
REAL_CASE_ID = 14919


class TestRealProcess:
    """Test processing real case data."""
    
    @pytest.mark.asyncio
    async def test_process_real_case_14919(self):
        """Process actual case 14919 (chunking, embeddings, summarization)."""
        print(f"\n{'='*80}")
        print(f"PROCESSING REAL CASE {REAL_CASE_ID}")
        print(f"{'='*80}\n")
        
        # Stage 1: Fetch real data
        print("Stage 1: Fetching data...")
        fetch_stage = FetchStage()
        raw_data = await fetch_stage.fetch_case_data(REAL_CASE_ID)
        print(f"✓ Fetched: {raw_data.case_meta.get('name')}")
        print(f"✓ Documents: {len(raw_data.documents)}")
        
        # Stage 2: Process (this is the slow part!)
        print(f"\nStage 2: Processing (this may take several minutes)...")
        print("  - Chunking documents...")
        print("  - Generating embeddings...")
        print("  - Summarizing documents (SLOW - uses LLM)...")
        print("  - Building initial context...")
        
        process_stage = ProcessStage()
        result = await process_stage.process_case_data(raw_data)
        
        # Verify result
        assert isinstance(result, ProcessedCaseData)
        assert result.case_id == REAL_CASE_ID
        assert len(result.documents) > 0
        
        print(f"\n✓ Processed {len(result.documents)} documents")
        print(f"✓ Total chunks: {sum(len(doc.chunks) for doc in result.documents)}")
        print(f"✓ Docket entries: {len(result.docket_entries)}")
        
        # Save detailed results
        output_file = OUTPUT_DIR / f"02_real_process_case_{REAL_CASE_ID}.json"
        result_dict = {
            'case_id': result.case_id,
            'case_name': result.case_name,
            'court': result.court,
            'filing_date': str(result.filing_date) if result.filing_date else None,
            'documents': [
                {
                    'doc_id': doc.doc_id,
                    'title': doc.title,
                    'doc_date': str(doc.doc_date) if doc.doc_date else None,
                    'chunks_count': len(doc.chunks),
                    'summary_length': len(doc.summary),
                    'summary_preview': doc.summary[:300] + '...' if len(doc.summary) > 300 else doc.summary,
                    'sample_chunks': [
                        {
                            'chunk_id': chunk.chunk_id,
                            'chunk_index': chunk.chunk_index,
                            'text_preview': chunk.chunk_text[:150] + '...' if len(chunk.chunk_text) > 150 else chunk.chunk_text,
                            'has_embedding': len(chunk.embedding) > 0,
                            'embedding_dimensions': len(chunk.embedding)
                        }
                        for chunk in doc.chunks[:3]  # First 3 chunks
                    ]
                }
                for doc in result.documents
            ],
            'docket_entries_count': len(result.docket_entries),
            'initial_context_length': len(result.initial_context)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Process results saved to: {output_file}")
        
        # Save full initial context
        context_file = OUTPUT_DIR / f"02_initial_context_case_{REAL_CASE_ID}.txt"
        with open(context_file, 'w', encoding='utf-8') as f:
            f.write(result.initial_context)
        
        print(f"✓ Initial context saved to: {context_file}")
        
        # Save each document summary separately
        for i, doc in enumerate(result.documents, start=1):
            summary_file = OUTPUT_DIR / f"02_doc_{doc.doc_id}_summary.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"Document ID: {doc.doc_id}\n")
                f.write(f"Title: {doc.title}\n")
                f.write(f"Date: {doc.doc_date}\n")
                f.write(f"Chunks: {len(doc.chunks)}\n")
                f.write(f"\n{'='*80}\n\n")
                f.write(doc.summary)
            
            print(f"✓ Document {i} summary saved to: {summary_file}")
        
        print(f"\n{'='*80}")
        print(f"PROCESSING COMPLETE")
        print(f"{'='*80}\n")
