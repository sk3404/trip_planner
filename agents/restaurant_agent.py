from typing import Dict, Any, List
from datetime import datetime
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import LLMChain
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
from langchain.schema import SystemMessage, HumanMessage, AIMessage

from core.base_agent import BaseAgent, AgentResponse
from models.schemas import RestaurantRequest, RestaurantResponse, Restaurant


class RestaurantAgent(BaseAgent):
    """Agent responsible for recommending restaurants using web search and LangChain."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            max_tokens=2000
        )
        
        # Initialize web search tool
        self.search = DuckDuckGoSearchRun()
        
        # Define tools for the agent
        self.tools = [
            Tool(
                name="web_search",
                func=self.search.run,
                description="Useful for searching the internet for restaurant reviews, ratings, and information in a specific location."
            )
        ]
        
        # Define the system prompt for restaurant recommendations
        self.system_prompt = """You are an expert food critic and local dining guide.
        Your task is to find and recommend the best restaurants based on user preferences.
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
        
        Format your response as a structured JSON with the following schema:
        {
            "restaurants": [
                {
                    "name": "Restaurant name",
                    "cuisine": "Primary cuisine type",
                    "rating": rating_in_float,
                    "price_range": "Price range ($, $$, $$$, $$$$)",
                    "address": "Full address",
                    "reservation_available": boolean,
                    "opening_hours": "Opening hours (optional)",
                    "specialties": ["List of signature dishes or specialties"],
                    "unique_features": ["List of unique features or experiences"]
                }
            ]
        }"""
        
        # Create the agent with tools
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        self.agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # Create the agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True
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
            request = RestaurantRequest(**input_data)
            
            # Create the human message with the request
            human_message = f"""
            Find the best restaurants in {request.location} for {request.date.strftime('%Y-%m-%d')}.
            Cuisine preferences: {', '.join(request.cuisine_preferences)}
            Price range: {request.price_range}
            Party size: {request.party_size}
            
            Please search for restaurants and provide recommendations in the specified JSON format.
            Consider both popular review sites and local recommendations.
            Include details about unique features, specialties, and reservation availability.
            """
            
            # Run the agent
            result = await self.agent_executor.arun(
                input=human_message
            )
            
            # Parse the response into our schema
            try:
                restaurants_data = json.loads(result)
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
            return self.handle_error(e)
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate the input data for restaurant recommendations."""
        required_fields = ["location", "date", "cuisine_preferences", "price_range"]
        return all(field in input_data for field in required_fields) 