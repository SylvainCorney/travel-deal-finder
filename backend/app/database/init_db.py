from app.database.base import Base, engine
from app.models.deal import Deal
from app.models.search import SearchQuery
from app.models.price_history import PriceHistory


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    print("Database tables created successfully!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())
