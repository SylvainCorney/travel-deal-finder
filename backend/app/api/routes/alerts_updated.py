# Add this import at the top of your existing alerts.py
from app.services.email_service import email_service

# Then update the create_price_alert function to include this at the end:

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
    
    # Send confirmation email
    email_service.send_confirmation_email(alert.to_dict())
    
    return PriceAlertResponse(**alert.to_dict())
