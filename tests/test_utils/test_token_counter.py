"""Tests for token counter utility"""

import pytest
from src.utils.token_counter import (
    estimate_tokens,
    get_context_window_limit,
    calculate_context_usage
)


@pytest.mark.unit
class TestTokenCounter:
    """Test suite for token counting utilities"""
    
    def test_estimate_tokens_simple_text(self):
        """Test estimating tokens in simple text"""
        text = "Hello world"
        count = estimate_tokens(text)
        
        assert count > 0
        assert isinstance(count, int)
        # Should estimate some tokens
        assert count >= 2
    
    def test_estimate_tokens_longer_text(self):
        """Test estimating tokens in longer text"""
        text = "This is a longer piece of text that should have more tokens than just a few words."
        count = estimate_tokens(text)
        
        assert count > 10
        assert isinstance(count, int)
    
    def test_estimate_tokens_empty_string(self):
        """Test estimating tokens for empty string"""
        count = estimate_tokens("")
        
        assert count == 0
    
    def test_get_context_window_limit_known_models(self):
        """Test getting context window limits for known models"""
        assert get_context_window_limit("gpt-4") == 8192
        assert get_context_window_limit("gpt-3.5-turbo") == 4096
        assert get_context_window_limit("llama3") == 8192
    
    def test_get_context_window_limit_unknown_model(self):
        """Test getting context window limit for unknown model"""
        limit = get_context_window_limit("unknown-model")
        
        assert limit == 8192  # Should return default
    
    def test_calculate_context_usage_basic(self):
        """Test calculating context usage"""
        usage = calculate_context_usage(
            messages_tokens=1000,
            system_prompt_tokens=100,
            document_context_tokens=500
        )
        
        assert usage["total_tokens"] == 1600
        assert usage["max_tokens"] == 8192
        assert usage["remaining_tokens"] > 0
        assert "usage_percentage" in usage
        assert isinstance(usage["usage_percentage"], (int, float))
    
    def test_calculate_context_usage_near_limit(self):
        """Test detecting near limit usage"""
        usage = calculate_context_usage(
            messages_tokens=7000,
            system_prompt_tokens=500
        )
        
        assert usage["is_near_limit"] is True
    
    def test_calculate_context_usage_below_limit(self):
        """Test usage below limit"""
        usage = calculate_context_usage(
            messages_tokens=1000
        )
        
        assert usage["is_near_limit"] is False
