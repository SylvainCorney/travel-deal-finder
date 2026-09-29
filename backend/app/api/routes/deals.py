from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional

from app.database.base import get_db
from app.models.deal import Deal
from app.models.search import SearchQuery

router = APIRouter()


@router.get("/deals")
async def get_deals(
    search_id: Optional[int] = None,
    deal_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get deals with optional filtering"""
    query = select(Deal)
    
    filters = []
    if search_id:
        filters.append(Deal.search_query_id == search_id)
    if deal_type:
        filters.append(Deal.deal_type == deal_type)
    if min_price is not None:
        filters.append(Deal.price >= min_price)
    if max_price is not None:
        filters.append(Deal.price <= max_price)
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.order_by(Deal.price.asc()).limit(limit)
    
    result = await db.execute(query)
    deals = result.scalars().all()
    
    return [deal.to_dict() for deal in deals]


@router.get("/deals/{deal_id}")
async def get_deal(
    deal_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get specific deal by ID"""
    result = await db.execute(
        select(Deal).where(Deal.id == deal_id)
    )
    deal = result.scalar_one_or_none()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    return deal.to_dict()


@router.get("/deals/search/{search_id}")
async def get_deals_by_search(
    search_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all deals for a specific search"""
    result = await db.execute(
        select(SearchQuery).where(SearchQuery.id == search_id)
    )
    search = result.scalar_one_or_none()
    
    if not search:
        raise HTTPException(status_code=404, detail="Search not found")
    
    result = await db.execute(
        select(Deal)
        .where(Deal.search_query_id == search_id)
        .order_by(Deal.price.asc())
    )
    deals = result.scalars().all()
    
    return {
        "search": search.to_dict(),
        "deals": [deal.to_dict() for deal in deals],
        "summary": {
            "total_deals": len(deals),
            "hotels": len([d for d in deals if d.deal_type == "hotel"]),
            "flights": len([d for d in deals if d.deal_type == "flight"]),
            "min_price": min([d.price for d in deals]) if deals else 0,
            "max_price": max([d.price for d in deals]) if deals else 0,
            "avg_price": sum([d.price for d in deals]) / len(deals) if deals else 0,
        }
    }


@router.delete("/deals/{deal_id}")
async def delete_deal(
    deal_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a deal"""
    result = await db.execute(
        select(Deal).where(Deal.id == deal_id)
    )
    deal = result.scalar_one_or_none()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    await db.delete(deal)
    await db.commit()
    
    return {"message": "Deal deleted successfully"}
