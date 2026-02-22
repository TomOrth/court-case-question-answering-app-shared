import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.services.search import SearchService

async def test_semantic_search():
    """Test semantic search with a real query."""
    
    # Setup database connection
    settings = get_settings()
    
    # Convert to async URL if needed (for create_async_engine)
    database_url = settings.DATABASE_URL
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Create search service
        search_service = SearchService(session)
        
        # Test query - adjust case_id to match your data!
        print("🧪 Testing Semantic Search")
        print("=" * 60)
        
        results = await search_service.semantic_search(
            query="What was the court's decision on the preliminary injunction?",
            case_id=14919,  # Change this to a case ID you have in your database
            top_k=3  # Just get top 3 for testing
        )
        
        print(f"\n📊 Results:")
        print("=" * 60)
        
        for i, chunk in enumerate(results, 1):
            print(f"\n--- Result {i} ---")
            print(f"Chunk ID: {chunk.chunk_id}")
            print(f"Doc ID: {chunk.doc_id}")
            print(f"Document: {chunk.doc_title}")
            print(f"Similarity: {chunk.similarity_score:.3f}")
            print(f"Text Preview: {chunk.chunk_text[:150]}...")
            print(f"\nFormatted for Planner:")
            print(chunk.format_for_planner())
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_semantic_search())    

