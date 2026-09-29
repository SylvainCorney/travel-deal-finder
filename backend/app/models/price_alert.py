"""
Price Alert Model

Stores user price alerts for specific hotels/resorts
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base


class PriceAlert(Base):
    """Price alert model for tracking desired prices on specific hotels"""
    
    __tablename__ = "price_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User Information
    email = Column(String, nullable=False, index=True)
    name = Column(String, nullable=True)  # Optional user name
    
    # Alert Criteria
    hotel_names = Column(JSON, nullable=False)  # List of hotel names to monitor
    destination = Column(String, nullable=False)  # e.g., "Cancun", "Punta Cana"
    origin = Column(String, nullable=True)  # Departure city (optional)
    
    # Price Criteria
    target_price = Column(Float, nullable=False)  # Alert when price drops below this
    currency = Column(String, default="CAD")
    
    # Date Preferences (optional - for specific date ranges)
    preferred_check_in_start = Column(String, nullable=True)  # e.g., "2026-02-01"
    preferred_check_in_end = Column(String, nullable=True)    # e.g., "2026-03-31"
    
    # Alert Settings
    is_active = Column(Boolean, default=True)
    notification_sent = Column(Boolean, default=False)
    last_checked_at = Column(DateTime, nullable=True)
    last_price_found = Column(Float, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    triggered_at = Column(DateTime, nullable=True)  # When alert was triggered
    
    # Additional preferences
    deal_type = Column(String, default="all_inclusive")  # "all_inclusive", "package", "hotel"
    notify_on_any_drop = Column(Boolean, default=False)  # Notify on ANY price drop, not just below target
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'hotel_names': self.hotel_names,
            'destination': self.destination,
            'origin': self.origin,
            'target_price': self.target_price,
            'currency': self.currency,
            'preferred_check_in_start': self.preferred_check_in_start,
            'preferred_check_in_end': self.preferred_check_in_end,
            'is_active': self.is_active,
            'notification_sent': self.notification_sent,
            'last_checked_at': self.last_checked_at.isoformat() if self.last_checked_at else None,
            'last_price_found': self.last_price_found,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
            'deal_type': self.deal_type,
            'notify_on_any_drop': self.notify_on_any_drop,
        }
    
    def __repr__(self):
        hotels = ', '.join(self.hotel_names) if self.hotel_names else 'Any'
        return f"<PriceAlert(id={self.id}, hotels={hotels}, target=${self.target_price}, active={self.is_active})>"
