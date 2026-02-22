"""
Tests for Stage 1: Fetch data from Clearinghouse API.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

from app.services.stages.fetch import FetchStage
from app.services.preprocessing_types import RawCaseData


# Output directory for test results
OUTPUT_DIR = Path(__file__).parent / "test_outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


class TestFetchStage:
    """Test the fetch stage."""
    
    @pytest.mark.asyncio
    async def test_fetch_case_data_success(self, mock_raw_case_data):
        """Test fetching case data successfully."""
        # Mock the Clearinghouse client
        with patch('app.services.stages.fetch.ClearinghouseClient') as MockClient:
            mock_client = MockClient.return_value
            mock_client.fetch_case_data = AsyncMock(return_value=mock_raw_case_data)
            
            # Create fetch stage and fetch data
            fetch_stage = FetchStage()
            result = await fetch_stage.fetch_case_data(99999)
            
            # Verify result
            assert isinstance(result, RawCaseData)
            assert result.case_id == 99999
            assert result.case_meta['name'] == 'Test Case v. Defendant'
            assert len(result.documents) == 2
            assert len(result.dockets) == 1
            
            # Save result to file for inspection
            output_file = OUTPUT_DIR / "01_fetch_result.json"
            with open(output_file, 'w') as f:
                json.dump({
                    'case_id': result.case_id,
                    'case_name': result.case_meta.get('name'),
                    'documents_count': len(result.documents),
                    'dockets_count': len(result.dockets),
                    'first_document': result.documents[0] if result.documents else None
                }, f, indent=2)
            
            print(f"\n✓ Fetch result saved to: {output_file}")
    
    @pytest.mark.asyncio
    async def test_fetch_case_not_found(self):
        """Test fetching a case that doesn't exist."""
        with patch('app.services.stages.fetch.ClearinghouseClient') as MockClient:
            mock_client = MockClient.return_value
            mock_client.fetch_case_data = AsyncMock(return_value={'documents': [], 'dockets': []})
            
            fetch_stage = FetchStage()
            
            with pytest.raises(ValueError, match="not found"):
                await fetch_stage.fetch_case_data(99999)
    
    @pytest.mark.asyncio
    async def test_fetch_handles_empty_documents(self):
        """Test fetching case with no documents."""
        mock_data = {
            'case': {'id': 99999, 'name': 'Empty Case'},
            'documents': [],
            'dockets': []
        }
        
        with patch('app.services.stages.fetch.ClearinghouseClient') as MockClient:
            mock_client = MockClient.return_value
            mock_client.fetch_case_data = AsyncMock(return_value=mock_data)
            
            fetch_stage = FetchStage()
            result = await fetch_stage.fetch_case_data(99999)
            
            assert result.case_id == 99999
            assert len(result.documents) == 0
            assert len(result.dockets) == 0
