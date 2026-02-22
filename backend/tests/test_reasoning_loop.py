# test_reasoning_loop.py
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.planner_agent import PlannerAgentService
from app.core.config import get_settings

async def test_reasoning_loop():
    """Test the complete reasoning loop"""
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
        
        # Test question
        question = "Who was the judge and what did they rule on the motion to dismiss?"
        
        print(f"\n{'='*70}")
        print(f"TESTING REASONING LOOP")
        print(f"{'='*70}")
        print(f"Question: {question}\n")
        
        # Process question and collect events
        events = []
        async for event_str in planner.process_question(
            question=question,
            case_id=14919,  # Use a real case ID
            session_id="445cb451-8d90-45e3-a8cc-b7e810839644"
        ):
            # Parse the NDJSON event
            import json
            event = json.loads(event_str)
            events.append(event)
            
            # Print event summary
            if event["type"] == "gathered_context":
                print(f"\n📋 Step {event['data']['step_number']}: Gathered Context")
                print(f"   {event['data']['content'][:]}")
            
            elif event["type"] == "reasoning":
                print(f"\n🤔 Step {event['data']['step_number']}: Reasoning")
                print(f"   {event['data']['content'][:]}")
            
            elif event["type"] == "tool_call":
                print(f"\n🔧 Step {event['data']['step_number']}: Tool Call")
                print(f"   {event['data']['tool']}")
            
            elif event["type"] == "tool_result":
                print(f"\n✅ Step {event['data']['step_number']}: Tool Result")
                print(f"   {len(event['data']['result'])} characters")
            
            elif event["type"] == "content":
                print(f"\n📝 Final Answer:")
                print(f"   {event['data'][:]}")
        
        # Analyze results
        print(f"\n\n{'='*70}")
        print(f"RESULTS ANALYSIS")
        print(f"{'='*70}")
        
        reasoning_steps = [e for e in events if e["type"] == "reasoning"]
        tool_calls = [e for e in events if e["type"] == "tool_call"]
        final_answer = [e for e in events if e["type"] == "content"]
        
        print(f"✅ Reasoning steps: {len(reasoning_steps)}")
        print(f"✅ Tool calls: {len(tool_calls)}")
        print(f"✅ Final answer: {'Yes' if final_answer else 'No'}")
        
        if final_answer:
            answer_text = final_answer[0]["data"]
            citations = answer_text.count("[CITE:")
            print(f"✅ Citations in answer: {citations}")
        
        print(f"\n🎉 Test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_reasoning_loop())