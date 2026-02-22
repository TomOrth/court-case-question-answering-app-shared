"""
Test docket summarization in isolation using real data.
"""

import pytest
from app.services.stages.fetch import FetchStage
from app.services.stages.process import ProcessStage
from app.services.summarization import SummarizationService

REAL_CASE_ID = 14919

@pytest.mark.asyncio
async def test_real_docket_summarization_isolation():
    """
    Test docket summarization using real data from Clearinghouse API.
    This tests ONLY the docket summarization flow, not the full pipeline.
    """
    print(f"\n{'='*80}")
    print(f"TESTING DOCKET SUMMARIZATION (ISOLATION)")
    print(f"{'='*80}")

    # 1. Fetch real data (no DB needed for this stage)
    fetcher = FetchStage()
    try:
        raw_data = await fetcher.fetch_case_data(REAL_CASE_ID)
    except Exception as e:
        pytest.fail(f"Test failed: Could not fetch data from API: {e}")
        return

    # 2. Process dockets into objects
    processor = ProcessStage()
    dockets = processor._process_docket_entries(raw_data.case_id, raw_data.dockets)
    
    print(f"\nPrepared {len(dockets)} docket entries for summarization.")
    
    # 3. Run Summarization
    summarizer = SummarizationService()
    summary = await summarizer.summarize_docket_entries(dockets)
    
    print(f"\n{'='*80}")
    print(f"GENERATED SUMMARY ({len(summary)} chars)")
    print(f"{'='*80}")
    print(summary)
    print(f"{'='*80}")

    # 4. Verify
    assert summary is not None
    assert len(summary) > 100
    assert "[CITE:docket_entry_" in summary, "Summary should contain docket citations"
    
    # Check for specific known events in this case (Bell v. Boise) if possible, 
    # or just ensure it looks like a procedural history.
    assert "filed" in summary.lower() or "court" in summary.lower()
