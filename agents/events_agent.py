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
from models.schemas import EventRequest, EventResponse, Event


class EventsAgent(BaseAgent):
    """Agent responsible for recommending and booking events and activities using web search and LangChain."""
    
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
                description="Useful for searching the internet for current events and activities in a specific location and date."
            )
        ]
        
        # Define the system prompt for event recommendations
        self.system_prompt = """You are an expert event planner and local guide.
        Your task is to find and recommend the best events and activities based on user preferences.
        Use the web search tool to find current events and then analyze them based on:
        1. Relevance to user interests
        2. Timing and availability
        3. Price within budget
        4. Location accessibility
        5. Overall value and uniqueness
        
        Format your response as a structured JSON with the following schema:
        {
            "events": [
                {
                    "name": "Event name",
                    "description": "Detailed description",
                    "date": "YYYY-MM-DD",
                    "location": "Specific location",
                    "price": price_in_float,
                    "category": "Category (e.g., music, sports, culture)"
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
            request = EventRequest(**input_data)
            
            # Create the human message with the request
            human_message = f"""
            Find the best events and activities in {request.location} on {request.date.strftime('%Y-%m-%d')}.
            The user's interests are: {', '.join(request.preferences)}
            Budget: ${request.budget}
            
            Please search for events and provide recommendations in the specified JSON format.
            """
            
            # Run the agent
            result = await self.agent_executor.arun(
                input=human_message
            )
            
            # Parse the response into our schema
            try:
                events_data = json.loads(result)
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
            return self.handle_error(e)
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate the input data for event recommendations."""
        required_fields = ["location", "date", "preferences", "budget"]
        return all(field in input_data for field in required_fields) 