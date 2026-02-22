# test_context_builder.py
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.planner_agent import PlannerAgentService
from app.core.config import get_settings

async def test_context_builder():
    """Test building initial context"""
    settings = get_settings()
    
    # Create database session
    database_url = settings.DATABASE_URL
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Create planner service
        planner = PlannerAgentService(session)
        
        # Test building context (use a real case_id and session_id from your DB)
        context = await planner._build_initial_context(
            question="Who was the judge?",
            case_id=14919,  # Use a real case ID
            session_id="445cb451-8d90-45e3-a8cc-b7e810839644"  # Use a real session ID
        )
        
        print("✅ Context built successfully!")
        print(f"📊 Context length: {len(context)} characters")
        # print("\n--- First 500 characters ---")
        print(context[:])
        print("\n✅ Test passed!")

if __name__ == "__main__":
    asyncio.run(test_context_builder())