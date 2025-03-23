from typing import Dict, Any, List
from datetime import datetime, timedelta
import json

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.chains import LLMChain

from core.base_agent import BaseAgent, AgentResponse
from models.schemas import ItineraryRequest, ItineraryResponse, Activity, DayPlan


class ItineraryAgent(BaseAgent):
    """Agent responsible for creating travel itineraries using LangChain and OpenAI."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            max_tokens=2000
        )
        
        # Define the prompt template for itinerary generation
        template = """You are an expert travel planner. Create a detailed 2-day itinerary for the following trip:

Destination: {destination}
Start Date: {start_date}
Interests: {preferences}

Create a schedule with activities from 9 AM to 9 PM each day. Include meals and travel time between locations.
Each activity should be 1-3 hours long.

Format your response as a JSON object with this EXACT structure:
{
    "days": [
        {
            "date": "YYYY-MM-DD",
            "activities": [
                {
                    "name": "Activity Name",
                    "description": "Detailed description",
                    "start_time": "YYYY-MM-DDTHH:MM:SS",
                    "end_time": "YYYY-MM-DDTHH:MM:SS",
                    "location": "Specific location with address if possible",
                    "category": "One of: culture, food, nature, shopping, or landmarks"
                }
            ]
        }
    ]
}

Important:
1. Use ISO format for dates (YYYY-MM-DDTHH:MM:SS)
2. Include EXACTLY 2 days
3. Each day should have 4-6 activities
4. Activities should be in chronological order
5. Return ONLY the JSON object, no other text

Respond with ONLY the JSON object, no additional text."""

        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", template)
        ])
        
        # Create the LangChain chain
        self.chain = LLMChain(
            llm=self.llm,
            prompt=self.prompt_template
        )
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        try:
            if not self.validate_input(input_data):
                return AgentResponse(
                    success=False,
                    data={},
                    error="Invalid input data"
                )
            
            # Convert input to request model
            request = ItineraryRequest(**input_data)
            
            # Generate the itinerary using LangChain
            response = await self.chain.arun(
                destination=request.destination,
                start_date=request.start_date.strftime("%Y-%m-%d"),
                preferences=", ".join(request.preferences)
            )
            
            # Clean the response to ensure it's valid JSON
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            # Parse the response into our schema
            try:
                itinerary_data = json.loads(response)
                
                # Validate the response structure
                if "days" not in itinerary_data:
                    return AgentResponse(
                        success=False,
                        data={},
                        error="Response missing 'days' array"
                    )
                
                # Convert the response to our schema
                itinerary_response = ItineraryResponse(days=itinerary_data["days"])
                
                return AgentResponse(
                    success=True,
                    data=itinerary_response.dict()
                )
            except json.JSONDecodeError as e:
                return AgentResponse(
                    success=False,
                    data={},
                    error=f"Failed to parse itinerary response: {str(e)}"
                )
            except Exception as e:
                return AgentResponse(
                    success=False,
                    data={},
                    error=f"Failed to process itinerary: {str(e)}"
                )
            
        except Exception as e:
            return self.handle_error(e)
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate the input data for itinerary generation."""
        required_fields = ["destination", "start_date", "end_date", "preferences"]
        return all(field in input_data for field in required_fields) 