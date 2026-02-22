"""
Test ExecutorService - End-to-End Tool Testing.

This tests all three executor tools through the unified router.
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.services.executor import ExecutorService


async def test_executor_all_tools():
    """Test all three tools through the executor."""
    
    settings = get_settings()
    database_url = settings.DATABASE_URL
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        executor = ExecutorService(session)
        
        print("🧪 Testing ExecutorService - All Tools")
        print("=" * 80)
        
        # You'll need to adjust case_id and doc_id to match your data
        case_id = 14919  # CHANGE THIS
        doc_id = 78327   # CHANGE THIS
        
        # ========================================
        # Test 1: Semantic Search
        # ========================================
        print("\n" + "=" * 80)
        print("TEST 1: Semantic Search")
        print("=" * 80)
        
        result1 = await executor.execute_tool(
            tool_name="semantic_search",
            params={
                "query": "What was the court's ruling on the preliminary injunction?",
                "case_id": case_id,
                "top_k": 5
            }
        )
        
        print("\n📄 RESULT:")
        print(result1)
        
        # ========================================
        # Test 2: Keyword Search
        # ========================================
        print("\n" + "=" * 80)
        print("TEST 2: Keyword Search")
        print("=" * 80)
        
        result2 = await executor.execute_tool(
            tool_name="keyword_search_by_chunk",
            params={
                "keywords": ["Judge", "Winmill", "2011"],
                "case_id": case_id,
                "max_results": 5
            }
        )
        
        print("\n📄 RESULT:")
        print(result2)
        
        # ========================================
        # Test 3: Document QA
        # ========================================
        print("\n" + "=" * 80)
        print("TEST 3: Document QA")
        print("=" * 80)
        
        result3 = await executor.execute_tool(
            tool_name="ask_questions_on_document",
            params={
                "doc_id": doc_id,
                "questions": [
                    "What was the date of this document?",
                    "Who authored or issued it?",
                    "What was the main subject?"
                ],
                "planners_context": "Testing document QA through executor",
                "case_id": case_id
            }
        )
        
        print("\n📄 RESULT:")
        print(result3)
        
        # ========================================
        # Test 4: Error Handling - Invalid Tool
        # ========================================
        print("\n" + "=" * 80)
        print("TEST 4: Error Handling - Invalid Tool")
        print("=" * 80)
        
        result4 = await executor.execute_tool(
            tool_name="nonexistent_tool",
            params={}
        )
        
        print("\n📄 RESULT:")
        print(result4)
        
        # ========================================
        # Test 5: Error Handling - Missing Parameters
        # ========================================
        print("\n" + "=" * 80)
        print("TEST 5: Error Handling - Missing Parameters")
        print("=" * 80)
        
        result5 = await executor.execute_tool(
            tool_name="semantic_search",
            params={"case_id": case_id}  # Missing 'query'
        )
        
        print("\n📄 RESULT:")
        print(result5)
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_executor_all_tools())