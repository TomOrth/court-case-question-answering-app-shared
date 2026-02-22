"""
Test script for Clearinghouse API client. """

import asyncio
from app.services.clearinghouse_client import ClearinghouseClient


async def main():
    client = ClearinghouseClient()

    # Test with case ID 14919 (Bell v. City of Boise)
    case_id = 14919

    print(f"Fetching data for case {case_id}")

    try:
        data = await client.fetch_case_data(case_id)

        print(f"\n✅ Case: {data['case']['name']}")
        print(f"    Court: {data['case']['court']}")
        print(f"    Filing Date: {data['case']['filing_date']}")

        print(f"\n📃 Documents: {len(data['documents'])} found")
        for doc in data['documents'][:3]:
            text_preview = doc.get('text', '')[:100] + '...' if doc.get('text') else 'No text'
            print(f"    - {doc['title'][:50]}...")
            print(f"    Text preview: {text_preview}")

        print(f"\n📋 Dockets: {len(data['dockets'])} found")
        for docket in data['dockets']:
            entries = docket.get('docket_entries', [])
            print(f"    - {len(entries)} docket entries")

        print(f"\n🔗 Resources: {len(data['resources'])} found")

        print("\n✅ API client working correctly!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())