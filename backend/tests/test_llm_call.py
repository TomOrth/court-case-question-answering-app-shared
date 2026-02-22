# test_llm_call.py
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.planner_agent import PlannerAgentService
from app.core.config import get_settings

async def test_llm_call():
    """Test calling the LLM and parsing response"""
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
        
        # Build initial context
        context = await planner._build_initial_context(
            question="What temporal patterns of enforcement are alleged (time of day, season, or officer deployment), and which internal or external sources are cited to substantiate those patterns?",
            case_id=14919,  # Use a real case ID
            session_id="445cb451-8d90-45e3-a8cc-b7e810839644"
        )
        
        print("\n" + "="*60)
        print("CALLING LLM")
        print("="*60)
        
        # Call the LLM!
        response = await planner._call_planner_llm(context, is_final_answer=False)
        
        print("\n" + "="*60)
        print("RESPONSE RECEIVED")
        print("="*60)
        
        print(f"\n📋 Gathered Context:")
        print(f"   {response.gathered_context}\n")
        
        print(f"🤔 Reasoning Step:")
        print(f"   {response.reasoning_step}\n")
        
        print(f"🔧 Tool Calls ({len(response.tool_calls)}):")
        for i, tool_call in enumerate(response.tool_calls, 1):
            print(f"   {i}. {tool_call.tool}")
            print(f"      Parameters: {tool_call.parameters}")
        
        print("\n✅ Test passed! Planner is thinking!")

if __name__ == "__main__":
    asyncio.run(test_llm_call())