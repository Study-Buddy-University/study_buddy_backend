"""
Tool registry for managing available tools.
"""

from typing import Dict, List, Optional
from .base import Tool, ToolResult
from .calculator import CalculatorTool
from .web_search import WebSearchTool


class ToolRegistry:
    """Registry for all available tools."""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register all default tools."""
        self.register_tool(CalculatorTool())
        self.register_tool(WebSearchTool())
    
    def register_tool(self, tool: Tool):
        """Register a new tool."""
        self._tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def get_all_tools(self) -> Dict[str, Tool]:
        """Get all registered tools."""
        return self._tools.copy()
    
    def get_tool_names(self) -> List[str]:
        """Get list of all tool names."""
        return list(self._tools.keys())
    
    def get_tools_by_names(self, names: List[str]) -> List[Tool]:
        """Get multiple tools by their names."""
        return [self._tools[name] for name in names if name in self._tools]
    
    def get_openai_functions(self, tool_names: Optional[List[str]] = None) -> List[Dict]:
        """
        Get tools in OpenAI function calling format.
        
        Args:
            tool_names: Optional list of tool names to include. If None, returns all tools.
            
        Returns:
            List of tool definitions in OpenAI format
        """
        if tool_names is None:
            tools = self._tools.values()
        else:
            tools = self.get_tools_by_names(tool_names)
        
        return [tool.to_openai_function() for tool in tools]
    
    async def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """
        Execute a tool by name with given parameters.
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool-specific parameters
            
        Returns:
            ToolResult with execution result or error
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' not found"
            )
        
        return await tool.execute(**kwargs)


# Global tool registry instance
_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry
