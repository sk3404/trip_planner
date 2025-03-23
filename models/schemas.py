from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ItineraryRequest(BaseModel):
    """Request model for itinerary generation."""
    destination: str = Field(
        description="City or destination name",
        example="San Francisco"
    )
    start_date: datetime = Field(
        description="Start date and time of the trip",
        example="2024-04-01T00:00:00"
    )
    end_date: datetime = Field(
        description="End date and time of the trip",
        example="2024-04-02T23:59:59"
    )
    preferences: List[str] = Field(
        description="List of travel preferences/interests",
        example=["culture", "food", "nature", "shopping"]
    )
    budget: Optional[float] = Field(
        default=None,
        description="Optional budget for the trip in USD",
        example=500.0
    )

    class Config:
        json_schema_extra = {
            "example": {
                "destination": "San Francisco",
                "start_date": "2024-04-01T00:00:00",
                "end_date": "2024-04-02T23:59:59",
                "preferences": ["culture", "food", "nature", "shopping"],
                "budget": 500.0
            }
        }


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