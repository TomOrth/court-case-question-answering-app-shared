import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.planner_agent import PlannerAgentService
from app.core.config import get_settings

async def test_final_answer_mode():
    """Test that final answer mode works"""
    settings = get_settings()

    database_url = settings.DATABASE_URL
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)

    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        planner = PlannerAgentService(session)
        
        # Simulate having some gathered context
        context = """You are generating a final answer.

Previous Research:
- Found that Judge Smith presided [CITE:doc_123_chunk_00005]
- Ruling was issued on June 15, 2019 [CITE:doc_123_chunk_00012]

Let's output json. Be sure to cite in the same format [CITE:chunk_id] to signify where the detail came from.

User Question: Who was the judge and when did they rule?
"""
        
        # Call with is_final_answer=True
        response = await planner._call_planner_llm(context, is_final_answer=True)
        
        print(f"\n📋 Gathered Context:")
        print(f"   {response.gathered_context}\n")
        
        print(f"🤔 Reasoning Step:")
        print(f"   {response.reasoning_step}\n")
        
        print(f"🔧 Tool Calls: {len(response.tool_calls)}")
        print(f"   (Should be 0 for final answer!)\n")
        
        # Verify no tool calls
        assert len(response.tool_calls) == 0, "Final answer should have no tool calls!"
        
        print("✅ Final answer mode works correctly!")

asyncio.run(test_final_answer_mode())