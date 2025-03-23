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
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an expert travel planner with deep knowledge of destinations worldwide.
            Create a detailed 2-day itinerary that maximizes the traveler's experience based on their interests.
            Consider timing, location proximity, and local customs.
            Format the response as a structured JSON with the following schema:
            {
                "days": [
                    {
                        "date": "YYYY-MM-DD",
                        "activities": [
                            {
                                "name": "Activity name",
                                "description": "Detailed description",
                                "start_time": "HH:MM",
                                "end_time": "HH:MM",
                                "location": "Specific location",
                                "category": "Category (e.g., culture, food, nature)"
                            }
                        ]
                    }
                ]
            }"""),
            ("human", """Create a 2-day itinerary for {city} starting on {start_date}.
            The traveler is interested in: {interests}
            Please ensure activities are well-timed and logically ordered.
            Include a mix of activities based on the interests provided.""")
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
                city=request.destination,
                start_date=request.start_date.strftime("%Y-%m-%d"),
                interests=", ".join(request.preferences)
            )
            
            # Parse the response into our schema
            try:
                itinerary_data = json.loads(response)
                itinerary_response = ItineraryResponse(**itinerary_data)
                
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
            return self.handle_error(e)
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate the input data for itinerary generation."""
        required_fields = ["destination", "start_date", "end_date", "preferences"]
        return all(field in input_data for field in required_fields) 