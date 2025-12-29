"""
Base classes for tools.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """Result from a tool execution."""
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Tool(ABC):
    """Base class for all tools."""
    
    def __init__(self):
        self.name = self.get_name()
        self.description = self.get_description()
        self.parameters = self.get_parameters()
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the tool name."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Return a description of what the tool does."""
        pass
    
    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """Return JSON schema for tool parameters."""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        pass
    
    def to_openai_function(self) -> Dict[str, Any]:
        """Convert tool to OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
