from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


DATABASE_URL = "postgresql+asyncpg://jxt-eli@localhost/quantevo_db"

engine = create_async_engine(DATABASE_URL)

AsyncSessionLocal = sessionmaker(
    engine, 
    class_ = AsyncSession, 
    expire_on_commit = False
)
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session