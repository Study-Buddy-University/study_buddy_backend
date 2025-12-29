"""
Detect potential hallucinations and add warnings.
"""
import re
from typing import Optional, List


def detect_hallucination_risk(
    query: str,
    response: str,
    tools_used: List[str]
) -> Optional[str]:
    """
    Detect if response might contain hallucinated information.
    
    Args:
        query: User's query
        response: AI's response
        tools_used: List of tools that were called
        
    Returns:
        Warning message if hallucination detected, None otherwise
    """
    query_lower = query.lower()
    response_lower = response.lower()
    
    # Check if query mentioned URL but no web search was used
    url_pattern = r'(https?://|www\.)[^\s]+'
    domain_pattern = r'\b[a-z0-9-]+\.(com|org|net|io|ai|dev|co|app|tech|xyz)\b'
    
    if (re.search(url_pattern, query) or re.search(domain_pattern, query_lower)):
        if "web_search" not in tools_used:
            return (
                "⚠️ **Note:** This response was generated without researching "
                "the mentioned website. For accurate information, "
                "please ask me to search for it."
            )
    
    # Check if query asked about recent/current info but no search
    recent_keywords = ["latest", "recent", "current", "2025", "2024"]
    if any(kw in query_lower for kw in recent_keywords):
        if "web_search" not in tools_used:
            return (
                "⚠️ **Note:** This response is based on my training data from April 2024. "
                "For the most current information, please ask me to search the web."
            )
    
    # Check if response contains specific claims about unknown entities
    specific_claims = [
        r"is a (company|product|service|platform|website) (that|which)",
        r"offers the following (features|services|products)",
        r"was founded (in|by)",
        r"is based in",
        r"provides \d+ (features|services|tools)"
    ]
    
    if any(re.search(pattern, response_lower) for pattern in specific_claims):
        if "web_search" not in tools_used:
            return (
                "⚠️ **Accuracy Warning:** The details above are based on general patterns, "
                "not specific research. For verified information, "
                "please ask me to search for this topic."
            )
    
    return None


def prepend_warning(response: str, warning: str) -> str:
    """
    Prepend warning to response.
    
    Args:
        response: Original response text
        warning: Warning message to prepend
        
    Returns:
        Response with warning prepended
    """
    return f"{warning}\n\n{response}"
