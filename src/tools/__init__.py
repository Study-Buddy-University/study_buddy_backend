"""
Tool system for AI agents.
Provides calculator, web search, and other tools that agents can use.
"""

from .registry import ToolRegistry, get_tool_registry
from .base import Tool, ToolResult

__all__ = ["ToolRegistry", "get_tool_registry", "Tool", "ToolResult"]
