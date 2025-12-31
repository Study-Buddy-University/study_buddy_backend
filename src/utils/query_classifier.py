"""
Query classification to determine when tools are mandatory vs optional.
"""
from enum import Enum
from typing import Tuple
import re


class QueryType(Enum):
    """Query classification types."""
    WEB_SEARCH_REQUIRED = "web_search_required"
    URL_LOOKUP = "url_lookup"
    CURRENT_EVENTS = "current_events"
    CALCULATION = "calculation"
    GENERAL_KNOWLEDGE = "general_knowledge"
    CREATIVE = "creative"


class ToolRequirement(Enum):
    """Tool usage enforcement levels."""
    REQUIRED = "required"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"
    NONE = "none"


def detect_url_patterns(message: str) -> bool:
    """
    Detect if message contains any URL or domain patterns.
    Only triggers on actual domains, not common words ending in TLDs.
    
    Args:
        message: User's query message
        
    Returns:
        True if URL/domain detected, False otherwise
    """
    # Full URLs with protocol
    if re.search(r'https?://', message, re.IGNORECASE):
        return True
    
    # www. prefix
    if re.search(r'\bwww\.', message, re.IGNORECASE):
        return True
    
    # Domain-like patterns: requires at least 2 parts before TLD
    # This prevents "already" (.ly) or "finally" (.ly) from matching
    # Matches: github.io, example.com, zapagi.com
    # Doesn't match: already, finally, really
    domain_pattern = r'\b[a-z0-9][-a-z0-9]{1,}\.[a-z0-9][-a-z0-9]{0,}\.(com|org|net|io|ai|dev|co|me|info|app|edu|gov|tech|xyz|site|online)\b'
    if re.search(domain_pattern, message, re.IGNORECASE):
        return True
    
    # Simple domain.tld but only if it looks like a domain (no spaces before/after dot)
    # Matches: zapagi.com, github.io
    # Doesn't match: "already" (has letters before .ly)
    simple_domain_pattern = r'\b[a-z0-9][-a-z0-9]{2,}\.(com|org|net|io|ai|dev|edu|gov)\b'
    if re.search(simple_domain_pattern, message, re.IGNORECASE):
        # Additional check: word before TLD should not be a common English word
        match = re.search(simple_domain_pattern, message, re.IGNORECASE)
        if match:
            word_before_tld = match.group(0).split('.')[0].lower()
            # Exclude common words that end in valid TLDs
            common_false_positives = [
                'already', 'finally', 'really', 'early', 'fairly', 'nearly', 'clearly',
                'actually', 'especially', 'family', 'barely', 'daily', 'easily'
            ]
            if word_before_tld not in common_false_positives:
                return True
    
    return False


def extract_url_or_domain(message: str) -> str:
    """
    Extract primary URL or domain from message for search query.
    
    Args:
        message: User's query message
        
    Returns:
        Extracted domain/URL or original message if no URL found
    """
    # Try to extract full URL first
    url_match = re.search(r'https?://([^\s]+)', message, re.IGNORECASE)
    if url_match:
        return url_match.group(1).rstrip('/')  # Remove trailing slash
    
    # Try www. prefix
    www_match = re.search(r'www\.([^\s]+)', message, re.IGNORECASE)
    if www_match:
        return www_match.group(1).rstrip('/')
    
    # Try domain pattern
    domain_match = re.search(
        r'\b([a-z0-9-]+\.(com|org|net|io|ai|dev|co|me|info|app|edu|gov|tech|xyz|site|online))\b',
        message,
        re.IGNORECASE
    )
    if domain_match:
        return domain_match.group(1)
    
    return message


def classify_query(message: str) -> Tuple[QueryType, ToolRequirement]:
    """
    Classify user query to determine tool requirements.
    
    Args:
        message: User's query message
        
    Returns:
        (QueryType, ToolRequirement) tuple
    """
    message_lower = message.lower()
    
    # URL/domain detection - HIGHEST PRIORITY
    if detect_url_patterns(message):
        return QueryType.URL_LOOKUP, ToolRequirement.REQUIRED
    
    # Explicit search phrases
    search_phrases = [
        "search for", "look up", "find information about",
        "what is the latest", "recent news", "current",
        "tell me about the website", "information about"
    ]
    if any(phrase in message_lower for phrase in search_phrases):
        return QueryType.WEB_SEARCH_REQUIRED, ToolRequirement.REQUIRED
    
    # Current events indicators
    current_indicators = [
        "latest", "recent", "current", "today", "this week",
        "this month", "2025", "2024", "now", "currently"
    ]
    if any(indicator in message_lower for indicator in current_indicators):
        return QueryType.CURRENT_EVENTS, ToolRequirement.RECOMMENDED
    
    # Calculation patterns
    calc_patterns = [
        r'\d+\s*[\+\-\*\/\^]\s*\d+',
        r'calculate', r'compute', r'solve'
    ]
    if any(re.search(pattern, message_lower) for pattern in calc_patterns):
        return QueryType.CALCULATION, ToolRequirement.REQUIRED
    
    # Creative requests (avoid tools)
    creative_indicators = [
        "write a story", "create a poem", "imagine",
        "make up", "brainstorm", "creative writing"
    ]
    if any(indicator in message_lower for indicator in creative_indicators):
        return QueryType.CREATIVE, ToolRequirement.NONE
    
    return QueryType.GENERAL_KNOWLEDGE, ToolRequirement.OPTIONAL


# Tool enforcement removed - tools are passed via bind_tools(), not prompt text
# The LLM will see tool definitions and decide when to use them
# See TOOL_CALLING_RESEARCH.md: "DON'T add tool descriptions to prompt text"
