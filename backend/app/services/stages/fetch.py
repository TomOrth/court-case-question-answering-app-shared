"""
Stage 1: Fetch data from Clearinghouse API.

This stage has no database interaction.
"""

from app.services.clearinghouse_client import ClearinghouseClient
from app.services.preprocessing_types import RawCaseData


class FetchStage:
    """Stage 1: Fetch data from Clearinghouse API"""
    
    def __init__(self):
        self.clearinghouse = ClearinghouseClient()
    
    async def fetch_case_data(self, case_id: int) -> RawCaseData:
        """
        Fetch all case data from Clearinghouse API.
        
        Returns:
            RawCaseData object (no database interaction)
        
        Raises:
            ValueError if case not found
            Exception if Clearinghouse API fails
        """
        print(f"[FETCH] Fetching case {case_id} from Clearinghouse API...")
        
        raw_data = await self.clearinghouse.fetch_case_data(case_id)
        
        if not raw_data.get('case'):
            raise ValueError(f"Case {case_id} not found in Clearinghouse API")
        
        print(f"[FETCH] ✓ Fetched case: {raw_data['case'].get('name', 'Unknown')}")
        print(f"[FETCH] ✓ Documents: {len(raw_data.get('documents', []))}")
        print(f"[FETCH] ✓ Dockets: {len(raw_data.get('dockets', []))}")
        
        return RawCaseData(
            case_id=case_id,
            case_meta=raw_data['case'],
            documents=raw_data.get('documents', []),
            dockets=raw_data.get('dockets', [])
        )
