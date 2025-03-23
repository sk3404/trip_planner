from typing import Dict, Any, List
from datetime import datetime
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.tools import Tool
from langchain.schema import SystemMessage, HumanMessage, AIMessage

from core.base_agent import BaseAgent, AgentResponse
from models.schemas import EventRequest, EventResponse, Event


class EventsAgent(BaseAgent):
    """Agent responsible for recommending and booking events and activities using web search and LangChain."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=2000
        )
        
        # Initialize web search tool
        self.search = DuckDuckGoSearchRun()
        
        # Define the prompt template for event recommendations
        template = """You are an expert event planner and local guide.
        Your task is to find and recommend the best events and activities based on user preferences.

        Location: {location}
        Date: {date}
        Interests: {preferences}
        Budget: ${budget}

        Use the web search tool to find current events and then analyze them based on:
        1. Relevance to user interests
        2. Timing and availability
        3. Price within budget
        4. Location accessibility
        5. Overall value and uniqueness

        Format your response as a JSON object with this EXACT structure:
        {{
            "events": [
                {{
                    "name": "Event name",
                    "description": "Detailed description",
                    "date": "YYYY-MM-DD",
                    "location": "Specific location",
                    "price": price_in_float,
                    "category": "Category (e.g., music, sports, culture)"
                }}
            ]
        }}

        Important:
        1. Return ONLY the JSON object, no other text
        2. Ensure all prices are within the specified budget
        3. Include 3-5 events that best match the user's interests
        4. Use specific locations with addresses when possible
        5. Categories should be one of: music, sports, culture, food, entertainment, or education

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
            request = EventRequest(**input_data)
            
            # Prepare the input for the chain
            chain_input = {
                "location": request.location,
                "date": request.event_date.strftime("%Y-%m-%d"),
                "preferences": ", ".join(request.preferences),
                "budget": request.budget
            }
            
            # Generate the events using the chain
            try:
                response = await self.chain.ainvoke(chain_input)
                response_text = response.content.strip()
            except Exception as e:
                return AgentResponse(
                    success=False,
                    data={},
                    error=f"Failed to generate events: {str(e)}"
                )
            
            # Clean the response to ensure it's valid JSON
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse the response into our schema
            try:
                events_data = json.loads(response_text)
                
                # Validate the response structure
                if "events" not in events_data:
                    return AgentResponse(
                        success=False,
                        data={},
                        error="Response missing 'events' array"
                    )
                
                # Validate each event has the required fields
                for event in events_data["events"]:
                    required_fields = ["name", "description", "date", "location", "price", "category"]
                    if not all(field in event for field in required_fields):
                        return AgentResponse(
                            success=False,
                            data={},
                            error="Invalid event structure in response"
                        )
                
                # Convert the response to our schema
                events_response = EventResponse(**events_data)
                
                return AgentResponse(
                    success=True,
                    data=events_response.dict()
                )
            except json.JSONDecodeError as e:
                return AgentResponse(
                    success=False,
                    data={},
                    error=f"Failed to parse events response: {str(e)}"
                )
            except Exception as e:
                return AgentResponse(
                    success=False,
                    data={},
                    error=f"Failed to process events: {str(e)}"
                )
            
        except Exception as e:
            return self.handle_error(e)
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate the input data for event recommendations."""
        required_fields = ["location", "date", "preferences", "budget"]
        return all(field in input_data for field in required_fields) 