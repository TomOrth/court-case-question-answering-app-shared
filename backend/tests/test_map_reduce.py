"""
Test Map-Reduce with a large document that gets split into parts.

This verifies the combining logic works correctly.
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func

from app.core.config import get_settings
from app.services.document_qa import DocumentQAService
from app.models.document import Document

async def test_map_reduce():
    """Find and test with the largest document in the database."""
    
    settings = get_settings()
    database_url = settings.DATABASE_URL
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Find the document with most chunks
        # stmt = (
        #     select(Document.doc_id, Document.case_id, Document.title, Document.total_chunks)
        #     .where(Document.total_chunks > 0)
        #     .order_by(Document.total_chunks.desc())
        #     .limit(1)
        # )
        
        # result = await session.execute(stmt)
        # row = result.fetchone()
        
        # if not row:
        #     print("❌ No documents found in database!")
        #     print("💡 Run preprocessing first to add documents.")
        #     return
        
        # doc_id, case_id, title, chunk_count = row
        doc_id = 78327
        case_id = 14919
        chunk_count = 0
        
        print("🔬 Testing Map-Reduce with Largest Document")
        print("=" * 80)
        print(f"\n📄 Selected Document:")
        print(f"  - ID: {doc_id}")
        # print(f"  - Title: {title}")
        print(f"  - Case ID: {case_id}")
        # print(f"  - Chunks: {chunk_count}")
        
        # Simple questions that should work on any document
        # questions = [
        #     "Which internal Boise Police Department documents are cited as evidence of increased enforcement success, and what specific metric or language do they use to characterize that success?",

        #     "What specific deficiencies are alleged in the Boise Police Department’s implementation of the Overnight Shelter Capacity Advisory Protocol, and how do those deficiencies undermine the Special Order’s practical effect?",

        #     "Which plaintiffs explicitly cite religious objections as a reason they could not access shelter, and how do those objections intersect with shelter duration or programming requirements?",

        #     "What temporal patterns of enforcement are alleged (time of day, season, or officer deployment), and which internal or external sources are cited to substantiate those patterns?",

        #     "How does the complaint distinguish between ordinances enacted by the City versus enforcement policies created solely by the Chief of Police, and why is that distinction legally significant for prospective relief?",
        # ]

        questions = [
            "According to the complaint, what precise number of homeless students were reported by the Meridian and Kuna school districts respectively for the 2012-13 school year, and how many homeless patients did the Terry Reilly clinic serve between April 2012 and March 2013?",

            "In internal communications on a BPD list serve, what three specific phrases did a Boise Police Officer use to describe his unsuccessful attempts to find violations, and what term did he use to describe camp sweeps in 2010?",

            "After Plaintiff Lawrence Lee Smith was arrested for camping in 'deep woods' areas, what three specific items of personal property does the complaint allege he lost—items he needed to sustain himself in the absence of shelter?",

            "How does Footnote 3 explicitly define the 'indicia of camping' regarding the use of fire and the preparation of bedding, and does the definition include the term 'sojourn'?",

            "What specific policy does the Boise Rescue Mission maintain regarding registered sex offenders residing in the shelter, and how does its policy regarding male children restrict mothers seeking to stay with their families?"
        ]
        
        print(f"\n📋 Questions:")
        for i, q in enumerate(questions, 1):
            print(f"  {i}. {q}")
        
        service = DocumentQAService(session)
        
        print(f"\n🤖 Processing (watch for part splitting)...\n")
        
        result = await service.ask_questions_on_document(
            doc_id=doc_id,
            questions=questions,
            planners_context="Trying to gather some info.",
            case_id=case_id
        )
        
        print("\n" + "=" * 80)
        print("\n📄 RESULT:")
        print("=" * 80)
        print(result)
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_map_reduce())