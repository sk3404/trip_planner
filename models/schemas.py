from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ItineraryRequest(BaseModel):
    """Request model for itinerary generation."""
    destination: str
    start_date: datetime
    end_date: datetime
    preferences: List[str]
    budget: Optional[float] = None


class Activity(BaseModel):
    """Model for a single activity in an itinerary."""
    name: str
    description: str
    start_time: datetime
    end_time: datetime
    location: str
    category: str


class DayPlan(BaseModel):
    """Model for a single day's activities."""
    date: str
    activities: List[Activity]


class ItineraryResponse(BaseModel):
    """Response model for itinerary generation."""
    days: List[DayPlan]


class EventRequest(BaseModel):
    """Request model for event recommendations."""
    location: str
    date: datetime
    preferences: List[str]
    budget: float


class Event(BaseModel):
    """Model for a single event."""
    name: str
    description: str
    date: str
    location: str
    price: float
    category: str


class EventResponse(BaseModel):
    """Response model for event recommendations."""
    events: List[Event]


class RestaurantRequest(BaseModel):
    """Request model for restaurant recommendations."""
    location: str
    date: datetime
    cuisine_preferences: List[str]
    price_range: str
    party_size: Optional[int] = 2


class Restaurant(BaseModel):
    """Model for a single restaurant."""
    name: str
    cuisine: str
    rating: float
    price_range: str
    address: str
    reservation_available: bool
    opening_hours: Optional[str] = None


class RestaurantResponse(BaseModel):
    """Response model for restaurant recommendations."""
    restaurants: List[Restaurant] 