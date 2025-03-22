from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any

from core.config import Config
from agents.itinerary_agent import ItineraryAgent
from agents.events_agent import EventsAgent
from agents.restaurant_agent import RestaurantAgent
from models.schemas import (
    ItineraryRequest,
    EventRequest,
    RestaurantRequest
)

# Initialize FastAPI app
app = FastAPI(
    title="AI Travel Planner",
    description="An intelligent travel planning system with specialized agents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize configuration
config = Config()

# Initialize agents
itinerary_agent = ItineraryAgent(config.get_agent_config())
events_agent = EventsAgent(config.get_agent_config())
restaurant_agent = RestaurantAgent(config.get_agent_config())


@app.post("/api/itinerary")
async def generate_itinerary(request: ItineraryRequest) -> Dict[str, Any]:
    """Generate a travel itinerary based on preferences."""
    response = await itinerary_agent.process(request.dict())
    if not response.success:
        raise HTTPException(status_code=400, detail=response.error)
    return response.data


@app.post("/api/events")
async def get_events(request: EventRequest) -> Dict[str, Any]:
    """Get event recommendations for a specific location and date."""
    response = await events_agent.process(request.dict())
    if not response.success:
        raise HTTPException(status_code=400, detail=response.error)
    return response.data


@app.post("/api/restaurants")
async def get_restaurants(request: RestaurantRequest) -> Dict[str, Any]:
    """Get restaurant recommendations for a specific location and date."""
    response = await restaurant_agent.process(request.dict())
    if not response.success:
        raise HTTPException(status_code=400, detail=response.error)
    return response.data


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 