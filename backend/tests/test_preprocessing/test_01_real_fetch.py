"""
Real integration test: Fetch actual case 14919 from Clearinghouse API.
"""

import pytest
import json
from pathlib import Path

from app.services.stages.fetch import FetchStage
from app.services.preprocessing_types import RawCaseData


# Output directory for test results
OUTPUT_DIR = Path(__file__).parent / "test_outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# Test with real case ID
REAL_CASE_ID = 14919


class TestRealFetch:
    """Test fetching real case data from Clearinghouse API."""
    
    @pytest.mark.asyncio
    async def test_fetch_real_case_14919(self):
        """Fetch actual case 14919 from Clearinghouse API."""
        print(f"\n{'='*80}")
        print(f"FETCHING REAL CASE {REAL_CASE_ID}")
        print(f"{'='*80}\n")
        
        # Create fetch stage (uses real API)
        fetch_stage = FetchStage()
        
        # Fetch real data
        result = await fetch_stage.fetch_case_data(REAL_CASE_ID)
        
        # Verify result
        assert isinstance(result, RawCaseData)
        assert result.case_id == REAL_CASE_ID
        assert result.case_meta is not None
        assert 'name' in result.case_meta
        assert len(result.documents) > 0
        
        print(f"✓ Case Name: {result.case_meta.get('name')}")
        print(f"✓ Documents: {len(result.documents)}")
        print(f"✓ Dockets: {len(result.dockets)}")
        
        # Save full raw data to file
        output_file = OUTPUT_DIR / f"01_real_fetch_case_{REAL_CASE_ID}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'case_id': result.case_id,
                'case_meta': result.case_meta,
                'documents_count': len(result.documents),
                'documents_summary': [
                    {
                        'id': doc['id'],
                        'title': doc.get('title', 'Untitled'),
                        'date': doc.get('date', 'No date'),
                        'has_text': 'text' in doc and len(doc.get('text', '')) > 0,
                        'text_length': len(doc.get('text', ''))
                    }
                    for doc in result.documents
                ],
                'dockets_count': len(result.dockets),
                'dockets_summary': [
                    {
                        'is_main_docket': docket.get('is_main_docket'),
                        'entries_count': len(docket.get('docket_entries', []))
                    }
                    for docket in result.dockets
                ]
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Raw data saved to: {output_file}")
        
        # Save first document text as sample
        if result.documents and result.documents[0].get('text'):
            sample_file = OUTPUT_DIR / f"01_sample_document_text.txt"
            with open(sample_file, 'w', encoding='utf-8') as f:
                f.write(f"Document ID: {result.documents[0]['id']}\n")
                f.write(f"Title: {result.documents[0].get('title', 'Untitled')}\n")
                f.write(f"Date: {result.documents[0].get('date', 'No date')}\n")
                f.write(f"\n{'='*80}\n\n")
                f.write(result.documents[0]['text'][:2000])  # First 2000 chars
                f.write("\n\n[... truncated ...]")
            
            print(f"✓ Sample document text saved to: {sample_file}")
        
        print(f"\n{'='*80}")
        print(f"FETCH COMPLETE")
        print(f"{'='*80}\n")
