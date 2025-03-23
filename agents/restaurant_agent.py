from typing import Dict, Any, List
from datetime import datetime
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.tools import Tool
from langchain.schema import SystemMessage, HumanMessage, AIMessage

from core.base_agent import BaseAgent, AgentResponse
from models.schemas import RestaurantRequest, RestaurantResponse, Restaurant


class RestaurantAgent(BaseAgent):
    """Agent responsible for recommending restaurants using web search and LangChain."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=2000
        )
        
        # Initialize web search tool
        self.search = DuckDuckGoSearchRun()
        
        # Define the prompt template for restaurant recommendations
        template = """You are an expert food critic and local dining guide.
        Your task is to find and recommend the best restaurants based on user preferences.

        Location: {location}
        Date: {date}
        Cuisine Preferences: {cuisine_preferences}
        Price Range: {price_range}
        Party Size: {party_size}

        Use the web search tool to find restaurant information and reviews, then analyze them based on:
        1. Cuisine type and authenticity
        2. Overall ratings and reviews
        3. Price range and value
        4. Location and accessibility
        5. Unique features or specialties
        6. Local popularity and hidden gems
        7. Reservation availability

        Consider both popular review sites and local recommendations.
        Prioritize restaurants that offer unique experiences or are particularly well-regarded in their category.

        Format your response as a JSON object with this EXACT structure:
        {{
            "restaurants": [
                {{
                    "name": "Restaurant name",
                    "cuisine": "Primary cuisine type",
                    "rating": rating_in_float,
                    "price_range": "Price range ($, $$, $$$, $$$$)",
                    "address": "Full address",
                    "reservation_available": boolean,
                    "opening_hours": "Opening hours (optional)",
                    "specialties": ["List of signature dishes or specialties"],
                    "unique_features": ["List of unique features or experiences"]
                }}
            ]
        }}

        Important:
        1. Return ONLY the JSON object, no other text
        2. Include 3-5 restaurants that best match the user's preferences
        3. Ensure price ranges match the user's specified range
        4. Use specific addresses when possible
        5. Include opening hours if available
        6. Categories should be one of: italian, japanese, chinese, mexican, indian, american, french, german, or other

        Respond with ONLY the JSON object, no additional text."""

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", template)
        ])
        
        # Create the chain using the newer pattern
        self.chain = self.prompt | self.llm
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        try:
            if not self.validate_input(input_data):
                return AgentResponse(
                    success=False,
                    data={},
                    error="Invalid input data"
                )
            
            # Convert input to request model
            request = RestaurantRequest(**input_data)
            
            # Prepare the input for the chain
            chain_input = {
                "location": request.location,
                "date": request.date.strftime("%Y-%m-%d"),
                "cuisine_preferences": ", ".join(request.cuisine_preferences),
                "price_range": request.price_range,
                "party_size": request.party_size
            }
            
            # Generate the restaurants using the chain
            try:
                response = await self.chain.ainvoke(chain_input)
                response_text = response.content.strip()
            except Exception as e:
                return AgentResponse(
                    success=False,
                    data={},
                    error=f"Failed to generate restaurants: {str(e)}"
                )
            
            # Clean the response to ensure it's valid JSON
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse the response into our schema
            try:
                restaurants_data = json.loads(response_text)
                
                # Validate the response structure
                if "restaurants" not in restaurants_data:
                    return AgentResponse(
                        success=False,
                        data={},
                        error="Response missing 'restaurants' array"
                    )
                
                # Validate each restaurant has the required fields
                for restaurant in restaurants_data["restaurants"]:
                    required_fields = ["name", "cuisine", "rating", "price_range", "address", "reservation_available"]
                    if not all(field in restaurant for field in required_fields):
                        return AgentResponse(
                            success=False,
                            data={},
                            error="Invalid restaurant structure in response"
                        )
                
                # Convert the response to our schema
                restaurants_response = RestaurantResponse(**restaurants_data)
                
                return AgentResponse(
                    success=True,
                    data=restaurants_response.dict()
                )
            except json.JSONDecodeError as e:
                return AgentResponse(
                    success=False,
                    data={},
                    error=f"Failed to parse restaurants response: {str(e)}"
                )
            except Exception as e:
                return AgentResponse(
                    success=False,
                    data={},
                    error=f"Failed to process restaurants: {str(e)}"
                )
            
        except Exception as e:
            return self.handle_error(e)
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate the input data for restaurant recommendations."""
        # Only date is required, other fields have defaults
        return "date" in input_data 