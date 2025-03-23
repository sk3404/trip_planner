from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field


class ItineraryRequest(BaseModel):
    """Request model for itinerary generation."""
    destination: str = Field(
        default="Seattle",
        description="City or destination name",
        example="Seattle"
    )
    start_date: date = Field(
        description="Start date of the trip",
        example="2024-04-01"
    )
    days: int = Field(
        description="Number of days for the itinerary",
        example=2
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
                "destination": "Seattle",
                "start_date": "2024-04-01",
                "days": 2,
                "preferences": ["culture", "food", "nature", "shopping"],
                "budget": 500.0
            }
        }


class Activity(BaseModel):
    """Model for a single activity in an itinerary."""
    name: str = Field(description="Name of the activity")
    description: str = Field(description="Detailed description of the activity")
    start_time: str = Field(description="Start time in ISO format (YYYY-MM-DDTHH:MM:SS)")
    end_time: str = Field(description="End time in ISO format (YYYY-MM-DDTHH:MM:SS)")
    location: str = Field(description="Location of the activity")
    category: str = Field(description="Category of the activity")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Visit Space Needle",
                "description": "Visit the iconic Space Needle observation deck",
                "start_time": "2024-04-01T09:00:00",
                "end_time": "2024-04-01T11:00:00",
                "location": "Space Needle, Seattle, WA",
                "category": "landmarks"
            }
        }


class DayPlan(BaseModel):
    """Model for a single day's activities."""
    date: str = Field(description="Date in YYYY-MM-DD format")
    activities: List[Activity]


class ItineraryResponse(BaseModel):
    """Response model for itinerary generation."""
    days: List[DayPlan]


class EventRequest(BaseModel):
    """Request model for event recommendations."""
    location: str = Field(
        default="Seattle",
        description="City or location name",
        example="Seattle"
    )
    event_date: date = Field(
        description="Date to find events for",
        example="2024-04-01"
    )
    preferences: List[str] = Field(
        description="List of event preferences/interests",
        example=["music", "sports", "culture"]
    )
    budget: float = Field(
        description="Budget for events in USD",
        example=100.0
    )


class Event(BaseModel):
    """Model for a single event."""
    name: str = Field(description="Name of the event")
    description: str = Field(description="Detailed description of the event")
    date: str = Field(description="Date in YYYY-MM-DD format")
    location: str = Field(description="Location of the event")
    price: float = Field(description="Price in USD")
    category: str = Field(description="Category of the event")


class EventResponse(BaseModel):
    """Response model for event recommendations."""
    events: List[Event]


class RestaurantRequest(BaseModel):
    """Request model for restaurant recommendations."""
    location: str = Field(
        default="Seattle",
        description="City or location name",
        example="Seattle"
    )
    date: date = Field(
        description="Date for restaurant recommendations",
        example="2024-04-01"
    )
    cuisine_preferences: List[str] = Field(
        default=["italian", "japanese", "american"],
        description="List of cuisine preferences",
        example=["italian", "japanese", "american"]
    )
    price_range: str = Field(
        default="$$",
        description="Price range ($, $$, $$$, $$$$)",
        example="$$"
    )
    party_size: Optional[int] = Field(
        default=2,
        description="Number of people in the party",
        example=2
    )

    class Config:
        json_schema_extra = {
            "example": {
                "location": "Seattle",
                "date": "2024-04-01",
                "cuisine_preferences": ["italian", "japanese", "american"],
                "price_range": "$$",
                "party_size": 2
            }
        }


class Restaurant(BaseModel):
    """Model for a single restaurant."""
    name: str = Field(description="Name of the restaurant")
    cuisine: str = Field(description="Primary cuisine type")
    rating: float = Field(description="Rating out of 5")
    price_range: str = Field(description="Price range ($, $$, $$$, $$$$)")
    address: str = Field(description="Full address")
    reservation_available: bool = Field(description="Whether reservations are available")
    opening_hours: Optional[str] = Field(
        default=None,
        description="Opening hours",
        example="11:00 AM - 10:00 PM"
    )


class RestaurantResponse(BaseModel):
    """Response model for restaurant recommendations."""
    restaurants: List[Restaurant] 