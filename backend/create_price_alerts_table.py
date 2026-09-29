import asyncio
from app.database.base import AsyncSessionLocal, Base, engine
from app.models.price_alert import PriceAlert

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('✅ Price alerts table created!')

if __name__ == "__main__":
    asyncio.run(create_tables())
