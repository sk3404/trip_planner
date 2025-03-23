from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pydantic import BaseModel


class AgentResponse(BaseModel):
    """Base response model for all agent outputs."""
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None


class BaseAgent(ABC):
    """Base class for all specialized agents in the travel planner."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get("model", "gpt-3.5-turbo")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 2000)

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Process the input data and return a response."""
        pass

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate the input data before processing."""
        return True

    def handle_error(self, error: Exception) -> AgentResponse:
        """Handle any errors that occur during processing."""
        return AgentResponse(
            success=False,
            data={},
            error=str(error)
        ) 