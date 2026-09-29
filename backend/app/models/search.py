from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base


class SearchQuery(Base):
    __tablename__ = "search_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Search criteria
    origin = Column(String, nullable=True)
    check_in_date = Column(String, nullable=False)
    check_out_date = Column(String, nullable=False)
    location = Column(String, nullable=False)
    
    # Optional filters stored as JSON
    hotels = Column(JSON, nullable=True)
    airlines = Column(JSON, nullable=True)
    sources = Column(JSON, nullable=True)  # ["hotels", "flights", "packages", "all_inclusive"]
    
    # Search metadata
    status = Column(String, default="pending")
    progress = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    deals = relationship("Deal", back_populates="search_query", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "origin": self.origin,
            "check_in_date": self.check_in_date,
            "check_out_date": self.check_out_date,
            "location": self.location,
            "hotels": self.hotels,
            "airlines": self.airlines,
            "sources": self.sources,
            "status": self.status,
            "progress": self.progress,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
