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
        
        # LangChain and OpenAI configurations
        self.agent_config = {
            "model": "gpt-3.5-turbo",
            "temperature": float(os.getenv("TEMPERATURE", "0.7")),
            "max_tokens": int(os.getenv("MAX_TOKENS", "2000")),
            "verbose": self.debug,
            "search_tool": {
                "max_results": int(os.getenv("MAX_SEARCH_RESULTS", "5")),
                "timeout": int(os.getenv("SEARCH_TIMEOUT", "30"))
            }
        }
        
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate the configuration settings."""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required")
    
    def get_agent_config(self) -> Dict[str, Any]:
        """Get the configuration for agents."""
        return self.agent_config.copy() 