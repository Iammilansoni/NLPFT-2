"""Fix stuck datasets that are showing as 'processing' for too long"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

async def fix_stuck_datasets():
    database_url = 'postgresql+asyncpg://nlpforge:nlpforge_secure_password@localhost:5432/nlpforge'
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Find and update stuck processing datasets (older than 1 hour)
        result = await session.execute(
            text("""
                UPDATE datasets 
                SET embedding_status = 'failed', 
                    embedding_error = 'Generation timed out or server restarted'
                WHERE embedding_status = 'processing' 
                AND created_at < NOW() - INTERVAL '1 hour'
                RETURNING name
            """)
        )
        updated = result.fetchall()
        await session.commit()
        
        if updated:
            print(f'Fixed {len(updated)} stuck datasets:')
            for row in updated:
                print(f'  - {row[0]}')
        else:
            print('No stuck datasets found (processing for > 1 hour)')
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_stuck_datasets())
