from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import logging
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from core.config import Config
from agents.itinerary_agent import ItineraryAgent
from agents.events_agent import EventsAgent
from agents.restaurant_agent import RestaurantAgent
from models.schemas import (
    ItineraryRequest,
    EventRequest,
    RestaurantRequest
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Travel Planner",
    description="An intelligent travel planning system using LangChain and specialized agents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:9000", "http://127.0.0.1:9000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Initialize configuration
config = Config()

# Initialize agents
try:
    itinerary_agent = ItineraryAgent(config.get_agent_config())
    events_agent = EventsAgent(config.get_agent_config())
    restaurant_agent = RestaurantAgent(config.get_agent_config())
    logger.info("Successfully initialized all agents")
except Exception as e:
    logger.error(f"Failed to initialize agents: {str(e)}")
    raise

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation errors."""
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)}
    )

@app.post("/api/itinerary")
async def generate_itinerary(request: ItineraryRequest) -> Dict[str, Any]:
    """Generate a travel itinerary based on preferences."""
    try:
        logger.info(f"Generating itinerary for {request.destination}")
        response = await itinerary_agent.process(request.dict())
        if not response.success:
            logger.error(f"Itinerary generation failed: {response.error}")
            raise HTTPException(status_code=400, detail=response.error)
        return response.data
    except Exception as e:
        logger.error(f"Error generating itinerary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/events")
async def get_events(request: EventRequest) -> Dict[str, Any]:
    """Get event recommendations for a specific location and date."""
    try:
        logger.info(f"Finding events in {request.location} for {request.event_date}")
        response = await events_agent.process(request.dict())
        if not response.success:
            logger.error(f"Event search failed: {response.error}")
            raise HTTPException(status_code=400, detail=response.error)
        return response.data
    except Exception as e:
        logger.error(f"Error finding events: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/restaurants")
async def get_restaurants(request: RestaurantRequest) -> Dict[str, Any]:
    """Get restaurant recommendations for a specific location and date."""
    try:
        # Convert the request to dict to ensure defaults are applied
        request_dict = request.dict()
        logger.info(f"Finding restaurants in {request_dict['location']} for {request_dict['date']}")
        response = await restaurant_agent.process(request_dict)
        if not response.success:
            logger.error(f"Restaurant search failed: {response.error}")
            raise HTTPException(status_code=400, detail=response.error)
        return response.data
    except Exception as e:
        logger.error(f"Error finding restaurants: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/debug-itinerary")
async def debug_itinerary(request: dict = Body(...)) -> Dict[str, Any]:
    """Debug endpoint to echo back the received request and test parsing."""
    try:
        # Try to parse as ItineraryRequest to validate
        itinerary_request = ItineraryRequest(**request)
        return {
            "received": request,
            "parsed": itinerary_request.dict(),
            "validation": "success"
        }
    except Exception as e:
        return {
            "received": request,
            "error": str(e),
            "validation": "failed"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 