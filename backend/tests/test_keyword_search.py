"""
Test script for keyword search.

This demonstrates how keyword search differs from semantic search.
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.services.search import SearchService

async def test_keyword_search():
    """Test keyword search with specific terms."""
    
    # Setup database connection
    settings = get_settings()
    
    # Convert to async URL if needed
    database_url = settings.DATABASE_URL
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        search_service = SearchService(session)
        
        print("🧪 Testing Keyword Search")
        print("=" * 60)
        
        # Test 1: Search for specific judge and date
        print("\n📋 Test 1: Multiple keywords (AND logic)")
        print("Keywords: 'preliminary injunction', '2011'")
        
        results1 = await search_service.keyword_search_by_chunk(
            keywords=["preliminary injunction", "2011"],
            case_id=14919,
            max_results=5
        )
        
        print(f"Found {len(results1)} chunks")
        for i, chunk in enumerate(results1, 1):
            print(f"\n  Result {i}:")
            print(f"  - Chunk: {chunk.chunk_id}")
            print(f"  - Doc: {chunk.doc_title}")
            print(f"  - Text: {chunk.chunk_text[:]}...")
        
        # Test 2: Search for a specific person
        print("\n" + "=" * 60)
        print("\n📋 Test 2: Specific name")
        print("Keywords: 'Winmill'")
        
        results2 = await search_service.keyword_search_by_chunk(
            keywords=["Winmill"],
            case_id=14919,
            max_results=5
        )
        
        print(f"Found {len(results2)} chunks")
        for i, chunk in enumerate(results2, 1):
            print(f"\n  Result {i}:")
            print(f"  - Chunk: {chunk.chunk_id}")
            print(f"  - Doc: {chunk.doc_title}")
            print(f"  - Full text: {chunk.chunk_text[:]}...")
        
        # Test 3: Too many keywords (might get zero results)
        print("\n" + "=" * 60)
        print("\n📋 Test 3: Very specific search")
        print("Keywords: 'preliminary injunction', 'Eighth Amendment', 'homeless'")
        
        results3 = await search_service.keyword_search_by_chunk(
            keywords=["preliminary injunction", "Eighth Amendment", "homeless"],
            case_id=14919,
            max_results=5
        )
        
        print(f"Found {len(results3)} chunks")
        if len(results3) == 0:
            print("  ⚠️  No results! All three keywords must appear in the SAME chunk.")
            print("  💡 The Planner would need to try fewer keywords or use semantic search.")
        else:
            for i, chunk in enumerate(results3, 1):
                print(f"\n  Result {i}:")
                print(f"  - Chunk: {chunk.chunk_id}")
                print(f"  - Text: {chunk.chunk_text[:]}...")
        
        # Show formatted output
        if len(results3) > 0:
            print("\n" + "=" * 60)
            print("\n📄 Formatted for Planner (third result):")
            print(results3[0].format_for_planner())
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_keyword_search())