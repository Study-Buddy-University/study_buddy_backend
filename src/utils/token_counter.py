"""
Token counting utilities for tracking LLM usage
"""


def estimate_tokens(text: str) -> int:
    """
    Estimate token count using a simple heuristic.
    This is a rough approximation: ~4 characters per token for English text.
    For production, consider using tiktoken for accurate counting.
    """
    if not text:
        return 0
    
    # Average of 4 characters per token (conservative estimate)
    char_count = len(text)
    estimated_tokens = char_count // 4
    
    # Add some buffer for special tokens, formatting, etc.
    buffer = max(10, estimated_tokens // 10)
    
    return estimated_tokens + buffer


def get_context_window_limit(model_name: str = "default") -> int:
    """
    Get the context window limit for a given model.
    """
    model_limits = {
        "gpt-4": 8192,
        "gpt-4-32k": 32768,
        "gpt-3.5-turbo": 4096,
        "gpt-3.5-turbo-16k": 16384,
        "llama2": 4096,
        "llama3": 8192,
        "mistral": 8192,
        "default": 8192,  # Safe default
    }
    
    return model_limits.get(model_name.lower(), model_limits["default"])


def calculate_context_usage(
    messages_tokens: int,
    system_prompt_tokens: int = 0,
    document_context_tokens: int = 0,
    model_name: str = "default"
) -> dict:
    """
    Calculate context window usage statistics.
    
    Returns:
        dict with usage stats including percentage, remaining tokens, etc.
    """
    total_tokens = messages_tokens + system_prompt_tokens + document_context_tokens
    max_tokens = get_context_window_limit(model_name)
    
    usage_percentage = (total_tokens / max_tokens) * 100
    remaining_tokens = max_tokens - total_tokens
    
    return {
        "total_tokens": total_tokens,
        "max_tokens": max_tokens,
        "usage_percentage": round(usage_percentage, 2),
        "remaining_tokens": remaining_tokens,
        "messages_tokens": messages_tokens,
        "system_prompt_tokens": system_prompt_tokens,
        "document_context_tokens": document_context_tokens,
        "is_near_limit": usage_percentage > 80,
    }
