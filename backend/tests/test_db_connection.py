"""
Test database connection to Supabase PostgreSQL.
This script verifies:
1. .env file is loaded correctly
2. Database connection string is valid
3. We can connect to Supabase
4. pgvector extension is enabled
"""

import os
import asyncio
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Load environment variables
load_dotenv()

async def test_connection():
    """Test async connection to database."""

    # Get DATABASE_URL from .env
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("❌ ERROR: DATABASE_URL not found in .env file!")
        return
    
    print(f"📝 Connecting to: {database_url}")
    print()

    try:
        # Create async engine
        # Note: asyncpg requires 'postgresql+asyncpg://' instead of 'postgresql://'
        if database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)

        engine = create_async_engine(
            database_url,
            echo=False,  # Set to True to see SQL queries
            pool_size=5,
            max_overflow=10
        )

        # Test connection
        async with engine.connect() as conn:
            # Test 1: Basic query
            result = await conn.execute(text("SELECT version();"))
            version = result.scalar()
            print(f"✅ Connected to PostgreSQL!")
            print(f"    Version: {version}")
            print()

            # Test 2: Check pgvector extension
            result = await conn.execute(
                text("SELECT * FROM pg_extension WHERE extname = 'vector';")
            )
            vector_ext = result.fetchone()

            if vector_ext:
                print(f"✅ pgvector extension is enabled!")
                print(f"    Extension version: {vector_ext[1]}")
            else:
                print(f"⚠️ WARNING: pgvector extension not found!")
                print(f"    Run this in Supabase SQL Editor:")
                print(f"    CREATE EXTENSION IF NOT EXISTS vector;")
            print()

            # Test 3: Check current database and user
            result = await conn.execute(text("SELECT current_database(), current_user;"))
            db_info = result.fetchone()
            print(f"✅ Database info:")
            print(f"    Current database: {db_info[0]}")
            print(f"    Current user: {db_info[1]}")
            print()

        # Clean up
        await engine.dispose()
        print("✅ All tests passed! Database connection is working.")

    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print()
        

if __name__ == "__main__":
    asyncio.run(test_connection())        

        
