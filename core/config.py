from typing import Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration management for the travel planner."""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.debug = os.getenv("DEBUG", "False").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # Agent configurations
        self.agent_config = {
            "model": "gpt-4",
            "temperature": float(os.getenv("TEMPERATURE", "0.7")),
            "max_tokens": int(os.getenv("MAX_TOKENS", "2000")),
        }
        
        # API keys for external services
        self.events_api_key = os.getenv("EVENTS_API_KEY")
        self.restaurant_api_key = os.getenv("RESTAURANT_API_KEY")
        
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate the configuration settings."""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required")
        
        if not self.events_api_key:
            raise ValueError("EVENTS_API_KEY is required")
        
        if not self.restaurant_api_key:
            raise ValueError("RESTAURANT_API_KEY is required")
    
    def get_agent_config(self) -> Dict[str, Any]:
        """Get the configuration for agents."""
        return self.agent_config.copy() 