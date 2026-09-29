from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base


class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=False)
    
    price = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    deal = relationship("Deal", back_populates="price_history")
    
    def to_dict(self):
        return {
            "id": self.id,
            "deal_id": self.deal_id,
            "price": self.price,
            "currency": self.currency,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }
