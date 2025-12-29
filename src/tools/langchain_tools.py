"""
LangChain-compatible tool wrappers for use with ChatOllama.bind_tools()
"""

from typing import List
from langchain_core.tools import tool
from .registry import get_tool_registry


@tool
async def web_search(query: str, num_results: int = 5) -> str:
    """Searches the web for information using multiple search engines.
    Returns relevant results with titles, snippets, and URLs.
    Use this when you need current information, facts, research, or want to find resources online.
    
    Args:
        query: Search query to look up on the web
        num_results: Number of results to return (default 5, max 10)
    
    Returns:
        Search results as formatted text
    """
    registry = get_tool_registry()
    result = await registry.execute_tool("web_search", query=query, num_results=num_results)
    
    if result.success:
        return result.result
    else:
        return f"Error: {result.error}"


@tool
async def calculator(expression: str) -> str:
    """Evaluates mathematical expressions safely.
    Supports basic operations (+, -, *, /, **) and functions (abs, round, min, max).
    Use this for any mathematical calculations.
    
    Args:
        expression: Mathematical expression to evaluate (e.g., "2 + 2", "sqrt(16)")
    
    Returns:
        Result of the calculation as a string
    """
    registry = get_tool_registry()
    result = await registry.execute_tool("calculator", expression=expression)
    
    if result.success:
        return str(result.result)
    else:
        return f"Error: {result.error}"


# Export all tools
ALL_LANGCHAIN_TOOLS = [web_search, calculator]

TOOL_MAP = {
    "web_search": web_search,
    "calculator": calculator
}


def get_langchain_tools(tool_names: List[str]) -> List:
    """Get LangChain tool objects by name."""
    return [TOOL_MAP[name] for name in tool_names if name in TOOL_MAP]
