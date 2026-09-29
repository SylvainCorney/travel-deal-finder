from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database.base import get_db, AsyncSessionLocal
from app.models.search import SearchQuery
from app.models.deal import Deal
from app.scrapers.hotel_scraper import HotelScraperFactory
from app.scrapers.flight_scraper import FlightScraperFactory
from app.scrapers.package_scraper import PackageScraperFactory
import asyncio

router = APIRouter()


class SearchRequest(BaseModel):
    origin: Optional[str] = None
    check_in_date: str
    check_out_date: str
    location: str
    hotels: List[str] = []
    airlines: List[str] = []
    sources: List[str] = ["hotels", "flights"]  # Can include "packages", "all_inclusive"


class SearchResponse(BaseModel):
    search_id: int
    status: str
    message: str


@router.post("/search", response_model=SearchResponse)
async def create_search(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new search query and start scraping"""
    search_query = SearchQuery(
        origin=request.origin,
        check_in_date=request.check_in_date,
        check_out_date=request.check_out_date,
        location=request.location,
        hotels=request.hotels if request.hotels else None,
        airlines=request.airlines if request.airlines else None,
        sources=request.sources,
        status="running",
        progress=0
    )
    
    db.add(search_query)
    await db.commit()
    await db.refresh(search_query)
    
    search_id = search_query.id
    
    # Start scraping in background
    asyncio.create_task(perform_search(search_id, request.dict()))
    
    return SearchResponse(
        search_id=search_id,
        status="running",
        message="Search started successfully"
    )


async def perform_search(search_id: int, search_params: dict):
    """Perform the actual scraping"""
    async with AsyncSessionLocal() as db:
        all_deals = []
        sources = search_params.get('sources', [])
        total_sources = len(sources)
        progress_per_source = 80 // max(total_sources, 1)
        current_progress = 10
        
        try:
            result = await db.execute(select(SearchQuery).where(SearchQuery.id == search_id))
            search_query = result.scalar_one()
            search_query.status = "running"
            search_query.progress = current_progress
            await db.commit()
            
            # Scrape hotels if requested
            if "hotels" in sources:
                hotel_scraper = HotelScraperFactory.create_scraper("booking")
                hotel_deals = await hotel_scraper.safe_scrape(search_params)
                all_deals.extend(hotel_deals)
                
                current_progress += progress_per_source
                result = await db.execute(select(SearchQuery).where(SearchQuery.id == search_id))
                search_query = result.scalar_one()
                search_query.progress = min(current_progress, 90)
                await db.commit()
            
            # Scrape flights if requested
            if "flights" in sources:
                flight_scraper = FlightScraperFactory.create_scraper("google")
                flight_deals = await flight_scraper.safe_scrape(search_params)
                all_deals.extend(flight_deals)
                
                current_progress += progress_per_source
                result = await db.execute(select(SearchQuery).where(SearchQuery.id == search_id))
                search_query = result.scalar_one()
                search_query.progress = min(current_progress, 90)
                await db.commit()
            
            # Scrape packages if requested - UPDATED TO USE "all" FOR MULTI-SITE
            if "packages" in sources or "all_inclusive" in sources:
                package_scraper = PackageScraperFactory.create_scraper("all")
                package_deals = await package_scraper.safe_scrape(search_params)
                all_deals.extend(package_deals)
                
                current_progress += progress_per_source
                result = await db.execute(select(SearchQuery).where(SearchQuery.id == search_id))
                search_query = result.scalar_one()
                search_query.progress = min(current_progress, 90)
                await db.commit()
            
            # Save deals to database
            for deal_data in all_deals:
                deal = Deal(
                    search_query_id=search_id,
                    **deal_data
                )
                db.add(deal)
            
            # Update search status
            result = await db.execute(select(SearchQuery).where(SearchQuery.id == search_id))
            search_query = result.scalar_one()
            search_query.status = "completed"
            search_query.progress = 100
            search_query.completed_at = datetime.utcnow()
            await db.commit()
            
        except Exception as e:
            result = await db.execute(select(SearchQuery).where(SearchQuery.id == search_id))
            search_query = result.scalar_one()
            search_query.status = "failed"
            search_query.error_message = str(e)
            await db.commit()
            print(f"Search failed: {e}")


@router.get("/search/{search_id}")
async def get_search_status(
    search_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get search query status and progress"""
    result = await db.execute(
        select(SearchQuery).where(SearchQuery.id == search_id)
    )
    search_query = result.scalar_one_or_none()
    
    if not search_query:
        raise HTTPException(status_code=404, detail="Search not found")
    
    return search_query.to_dict()


@router.get("/searches")
async def list_searches(
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """List recent searches"""
    result = await db.execute(
        select(SearchQuery)
        .order_by(SearchQuery.created_at.desc())
        .limit(limit)
    )
    searches = result.scalars().all()
    
    return [s.to_dict() for s in searches]
