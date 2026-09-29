"""
Price Alert API Endpoints

Endpoints for creating, managing, and monitoring price alerts
"""
from app.services.email_service import email_service
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

from app.database.base import get_db
from app.models.price_alert import PriceAlert

router = APIRouter()


# Pydantic Models
class PriceAlertCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    hotel_names: List[str]  # List of hotel names to monitor
    destination: str
    origin: Optional[str] = None
    target_price: float
    currency: str = "CAD"
    preferred_check_in_start: Optional[str] = None
    preferred_check_in_end: Optional[str] = None
    deal_type: str = "all_inclusive"
    notify_on_any_drop: bool = False


class PriceAlertUpdate(BaseModel):
    hotel_names: Optional[List[str]] = None
    target_price: Optional[float] = None
    is_active: Optional[bool] = None
    preferred_check_in_start: Optional[str] = None
    preferred_check_in_end: Optional[str] = None


class PriceAlertResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    hotel_names: List[str]
    destination: str
    origin: Optional[str]
    target_price: float
    currency: str
    is_active: bool
    notification_sent: bool
    last_price_found: Optional[float]
    created_at: str
    deal_type: str


@router.post("/alerts", response_model=PriceAlertResponse)
async def create_price_alert(
    alert_data: PriceAlertCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new price alert"""
    
    # Validate hotel names list is not empty
    if not alert_data.hotel_names or len(alert_data.hotel_names) == 0:
        raise HTTPException(
            status_code=400, 
            detail="At least one hotel name must be provided"
        )
    
    # Create alert
    alert = PriceAlert(
        email=alert_data.email,
        name=alert_data.name,
        hotel_names=alert_data.hotel_names,
        destination=alert_data.destination,
        origin=alert_data.origin,
        target_price=alert_data.target_price,
        currency=alert_data.currency,
        preferred_check_in_start=alert_data.preferred_check_in_start,
        preferred_check_in_end=alert_data.preferred_check_in_end,
        deal_type=alert_data.deal_type,
        notify_on_any_drop=alert_data.notify_on_any_drop,
        is_active=True,
        notification_sent=False
    )
    
    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    email_service.send_confirmation_email(alert.to_dict())    
    return PriceAlertResponse(**alert.to_dict())


@router.get("/alerts", response_model=List[PriceAlertResponse])
async def get_alerts(
    email: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all price alerts, optionally filtered by email or active status"""
    
    query = select(PriceAlert)
    
    # Apply filters
    filters = []
    if email:
        filters.append(PriceAlert.email == email)
    if is_active is not None:
        filters.append(PriceAlert.is_active == is_active)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Order by creation date
    query = query.order_by(PriceAlert.created_at.desc())
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return [PriceAlertResponse(**alert.to_dict()) for alert in alerts]


@router.get("/alerts/{alert_id}", response_model=PriceAlertResponse)
async def get_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific price alert by ID"""
    
    result = await db.execute(
        select(PriceAlert).where(PriceAlert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Price alert not found")
    
    return PriceAlertResponse(**alert.to_dict())


@router.put("/alerts/{alert_id}", response_model=PriceAlertResponse)
async def update_alert(
    alert_id: int,
    update_data: PriceAlertUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a price alert"""
    
    result = await db.execute(
        select(PriceAlert).where(PriceAlert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Price alert not found")
    
    # Update fields
    if update_data.hotel_names is not None:
        if len(update_data.hotel_names) == 0:
            raise HTTPException(
                status_code=400,
                detail="At least one hotel name must be provided"
            )
        alert.hotel_names = update_data.hotel_names
    
    if update_data.target_price is not None:
        alert.target_price = update_data.target_price
    
    if update_data.is_active is not None:
        alert.is_active = update_data.is_active
    
    if update_data.preferred_check_in_start is not None:
        alert.preferred_check_in_start = update_data.preferred_check_in_start
    
    if update_data.preferred_check_in_end is not None:
        alert.preferred_check_in_end = update_data.preferred_check_in_end
    
    alert.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(alert)
    
    return PriceAlertResponse(**alert.to_dict())


@router.delete("/alerts/{alert_id}")
async def delete_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a price alert"""
    
    result = await db.execute(
        select(PriceAlert).where(PriceAlert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Price alert not found")
    
    await db.delete(alert)
    await db.commit()
    
    return {"message": "Price alert deleted successfully"}


@router.post("/alerts/{alert_id}/pause")
async def pause_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Pause (deactivate) a price alert"""
    
    result = await db.execute(
        select(PriceAlert).where(PriceAlert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Price alert not found")
    
    alert.is_active = False
    alert.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(alert)
    
    return PriceAlertResponse(**alert.to_dict())


@router.post("/alerts/{alert_id}/resume")
async def resume_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Resume (activate) a paused price alert"""
    
    result = await db.execute(
        select(PriceAlert).where(PriceAlert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Price alert not found")
    
    alert.is_active = True
    alert.notification_sent = False  # Reset notification flag
    alert.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(alert)
    
    return PriceAlertResponse(**alert.to_dict())


@router.get("/alerts/user/{email}")
async def get_user_alerts(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all alerts for a specific email address"""
    
    result = await db.execute(
        select(PriceAlert)
        .where(PriceAlert.email == email)
        .order_by(PriceAlert.created_at.desc())
    )
    alerts = result.scalars().all()
    
    return {
        "email": email,
        "total_alerts": len(alerts),
        "active_alerts": len([a for a in alerts if a.is_active]),
        "triggered_alerts": len([a for a in alerts if a.notification_sent]),
        "alerts": [PriceAlertResponse(**alert.to_dict()) for alert in alerts]
    }
