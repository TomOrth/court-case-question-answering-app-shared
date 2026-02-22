"""
Real integration test configuration for preprocessing pipeline.

These tests use REAL data from the Clearinghouse API and REAL services.
"""

import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.db.base import Base
from app.core.config import get_settings
import pytest_asyncio


# Test database URL - using real database
settings = get_settings()
# Ensure we use the async driver
TEST_DATABASE_URL = settings.DATABASE_URL.replace("court_qa_db", "court_qa_test_db")
if "postgresql://" in TEST_DATABASE_URL and "postgresql+asyncpg://" not in TEST_DATABASE_URL:
    TEST_DATABASE_URL = TEST_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup - comment out if you want to inspect the database after tests
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope='function')
async def db_session(engine):
    """Create a fresh database session for each test."""
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session
        # Don't rollback - we want to keep the data for inspection
        # await session.rollback()


@pytest.fixture
def mock_raw_case_data():
    """Mock raw case data from Clearinghouse API."""
    return {
        'case': {
            'id': 99999,
            'name': 'Test Case v. Defendant',
            'court': 'U.S. District Court for the Test District',
            'state': 'CA',
            'filing_date': '2023-01-15',
            'case_ongoing': True,
            'summary': 'This is a test case summary.'
        },
        'documents': [
            {
                'id': 88888,
                'title': 'Test Complaint',
                'date': '2023-01-15',
                'file': 'http://example.com/complaint.pdf',
                'clearinghouse_link': 'http://example.com/doc/88888',
                'text': """
                UNITED STATES DISTRICT COURT
                TEST DISTRICT
                
                TEST CASE, Plaintiff
                v.
                DEFENDANT, Defendant
                
                COMPLAINT
                
                1. This is a test complaint for civil rights violations.
                2. Plaintiff alleges violations of constitutional rights.
                3. Plaintiff seeks damages and injunctive relief.
                
                WHEREFORE, Plaintiff requests judgment in their favor.
                """
            },
            {
                'id': 88889,
                'title': 'Test Order',
                'date': '2023-02-20',
                'file': 'http://example.com/order.pdf',
                'clearinghouse_link': 'http://example.com/doc/88889',
                'text': """
                ORDER GRANTING MOTION TO PROCEED
                
                The Court has reviewed the motion to proceed in forma pauperis.
                The motion is GRANTED.
                The case may proceed.
                
                SO ORDERED.
                """
            }
        ],
        'dockets': [
            {
                'is_main_docket': True,
                'docket_entries': [
                    {
                        'entry_number': 1,
                        'date_filed': '2023-01-15',
                        'description': 'COMPLAINT filed',
                        'url': 'http://example.com/entry/1',
                        'recap_pdf_url': None,
                        'pacer_doc_id': 'pacer-1'
                    },
                    {
                        'entry_number': 2,
                        'date_filed': '2023-02-20',
                        'description': 'ORDER granting motion',
                        'url': 'http://example.com/entry/2',
                        'recap_pdf_url': None,
                        'pacer_doc_id': 'pacer-2'
                    }
                ]
            }
        ]
    }
