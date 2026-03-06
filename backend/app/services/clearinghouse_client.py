"""
Clearinghouse API v2 Client.

Fetches court case data from the Civil Rights Litigation Clearinghouse.
Documentation: https://clearinghouse.net/api/v2/

This module handles:
- Authentication with API token
- Fetching from all 4 endpoints (cases, documents, dockets, resources)
- Pagination handling (API returns max 100 results per page)
- Combining responses into a single data structure
"""

import httpx
from typing import Optional
import os

BASE_URL = "https://clearinghouse.net/api/v2p1"


class ClearinghouseClient:
    """
    Async client for Clearinghouse API v2.
    
    Usage:
        client = ClearinghouseClient()
        data = await client.fetch_case_data(14919)
    """
    def __init__(self):
        
        self.api_key = os.getenv("CLEARINGHOUSE_API_KEY")
        self.headers = {
            "Authorization": f"Token {self.api_key}",
            "Accept": "application/json",
            "User-Agent": "CourtCaseQA/1.0",
        }

    async def _fetch_endpoint(self, endpoint: str, params: dict) -> list:
        """
        Fetch data from an endpoint, handling both response formats.
        
        The API has TWO different response formats:
        
        1. Paginated (only /cases/ endpoint):
           {
               "count": 19,
               "next": "https://...?page=2",  # or null
               "previous": null,
               "results": [...]
           }
        
        2. Plain array (documents, dockets, resources):
           [{...}, {...}, ...]
        
        This function detects the format and handles pagination if needed.
        """
        all_results = []
        url = f"{BASE_URL}/{endpoint}/"

        async with httpx.AsyncClient(timeout=60.0) as client:
            # while url:
            response = await client.get(
                url, 
                params=params if url.startswith(BASE_URL) else None, # only send params on first request. Next URLs already have params embedded
                headers=self.headers
            )
            response.raise_for_status()

            # # ===== DEBUGGING: Write response to file =====
            # from pathlib import Path
            # import json
            # raw_text = response.text
            # debug_file = Path(f"debug_{endpoint.replace('/', '_')}_response.json")
            # debug_file.write_text(raw_text, encoding='utf-8')
            # print(f"📝 Debug: Wrote response to {debug_file}")
            # # ============================================
            
            data = response.json()
            
            # # ===== DEBUGGING: Check type =====
            # print(f"🔍 Debug: endpoint={endpoint}, data type={type(data)}")
            # if isinstance(data, dict):
            #     print(f"   Dict keys: {list(data.keys())}")
            # elif isinstance(data, list):
            #     print(f"   List length: {len(data)}")
            # # =================================

            if isinstance(data, list):
                # Plain array format (documents, dockets, resources)
                return data
            
            elif isinstance(data, dict) and "results" in data:
                # Paginated format (cases endpoint)

                all_results.extend(data.get('results', []))
                next_url = data.get('next')  # None if no more pages

                # Follow pagination links if they exist
                while next_url:
                    response = await client.get(next_url, headers=self.headers)                    
                    response.raise_for_status()
                    data = response.json()

                    all_results.extend(data.get("results", []))
                    next_url = data.get("next")

                return all_results

            else:
                
                # Unexpected format
                raise ValueError(f"Unexpected response format from {endpoint}: {type(data)}")
        # return all_results
    
    async def fetch_case_metadata(self, case_id: int) -> Optional[dict]:
        """
        Fetch case metadata from /api/v2/cases/?case_id={id}
        
        Returns case info like:
        - name, court, state
        - summary, summary_short
        - filing_date, case_types
        - defendants, plaintiffs
        
        Note: This endpoint returns paginated format.
        """

        results = await self._fetch_endpoint(
            f"cases",
            {"case_id": case_id}
        )

        return results[0] if results else None
    
    async def fetch_documents(self, case_id: int) -> list:
        """
        Fetch all documents from /api/v2/documents/?case={id}
        
        Returns list of documents, each containing:
        - id, title, date
        - text (FULL DOCUMENT TEXT - this is critical!)
        
        Note: This endpoint returns plain array format.
        """
        return await self._fetch_endpoint(
            f"cases/{case_id}/documents",
            None,
        )
    
    async def fetch_dockets(self, case_id: int) -> list:
        """
        Fetch docket data from /api/v2/dockets/?case={id}
        
        Returns docket objects containing:
        
        Note: This endpoint returns plain array format.
        """

        return await self._fetch_endpoint(
            f"cases/{case_id}/dockets",
            None,
        )
    
    async def fetch_resources(self, case_id: int) -> list:
        """
        Fetch external resources from /api/v2/resources/?case={id}
        
        Note: This endpoint returns plain array format.
        """

        return await self._fetch_endpoint(
           f"cases/{case_id}/resources",
           None,
        )
    
    async def fetch_case_data(self, case_id: int) -> dict:
        """
        Fetch ALL data for a case from all 4 endpoints.
        
        This is the main method you'll call from the preprocessing service.
        
        Returns combined structure:
        {
            "case": { ... metadata ... },
            "documents": [ ... ],
            "dockets": [ ... ],
            "resources": [ ... ]
        }
        """

        import asyncio

        case_metadata, documents, dockets, resources = await asyncio.gather(
            self.fetch_case_metadata(case_id),
            self.fetch_documents(case_id),
            self.fetch_dockets(case_id),
            self.fetch_resources(case_id),
        )
        text_urls = []
        for i in range(len(documents)):
            if "text_url" in documents[i]:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    # while url:
                    response = await client.get(
                        documents[i]["text_url"], 
                        params=None, # only send params on first request. Next URLs already have params embedded
                        headers=self.headers
                    )
                    response.raise_for_status()
                    documents[i]["text"] = response.json()["text"]
        return {
            "case": case_metadata,
            "documents": documents,
            "dockets": dockets,
            "resources": resources,
        }
