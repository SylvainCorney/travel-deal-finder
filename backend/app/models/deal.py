from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base


class Deal(Base):
    __tablename__ = "deals"
    
    id = Column(Integer, primary_key=True, index=True)
    search_query_id = Column(Integer, ForeignKey("search_queries.id"), nullable=False)
    
    # Deal details
    deal_type = Column(String, nullable=False)  # 'hotel', 'flight', 'package', 'all_inclusive'
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    
    # Hotel specific
    hotel_name = Column(String, nullable=True)
    hotel_rating = Column(Float, nullable=True)
    room_type = Column(String, nullable=True)
    
    # Flight specific
    airline = Column(String, nullable=True)
    departure_time = Column(String, nullable=True)
    arrival_time = Column(String, nullable=True)
    duration = Column(String, nullable=True)
    stops = Column(Integer, nullable=True)
    
    # Package specific
    includes_flight = Column(Boolean, default=False)
    includes_hotel = Column(Boolean, default=False)
    includes_transfer = Column(Boolean, default=False)
    includes_meals = Column(Boolean, default=False)
    meal_plan = Column(String, nullable=True)  # 'All-Inclusive', 'Half-Board', etc.
    
    # Common fields
    check_in_date = Column(String, nullable=True)
    check_out_date = Column(String, nullable=True)
    location = Column(String, nullable=False)
    url = Column(Text, nullable=True)
    source = Column(String, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    is_available = Column(Boolean, default=True)
    
    # Relationships
    search_query = relationship("SearchQuery", back_populates="deals")
    price_history = relationship("PriceHistory", back_populates="deal", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "deal_type": self.deal_type,
            "name": self.name,
            "price": self.price,
            "currency": self.currency,
            "hotel_name": self.hotel_name,
            "hotel_rating": self.hotel_rating,
            "room_type": self.room_type,
            "airline": self.airline,
            "departure_time": self.departure_time,
            "arrival_time": self.arrival_time,
            "duration": self.duration,
            "stops": self.stops,
            "includes_flight": self.includes_flight,
            "includes_hotel": self.includes_hotel,
            "includes_transfer": self.includes_transfer,
            "includes_meals": self.includes_meals,
            "meal_plan": self.meal_plan,
            "check_in_date": self.check_in_date,
            "check_out_date": self.check_out_date,
            "location": self.location,
            "url": self.url,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_available": self.is_available,
        }
