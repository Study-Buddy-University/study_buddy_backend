"""Tests for WebSearchTool with domain filtering"""

import pytest
from src.tools.web_search import WebSearchTool


@pytest.mark.unit
class TestWebSearchTool:
    """Test suite for WebSearchTool domain filtering"""
    
    @pytest.fixture
    def web_search(self):
        """Create WebSearchTool instance"""
        return WebSearchTool()
    
    def test_extract_domain_from_url_query(self, web_search):
        """Test extracting domain from URL in query"""
        has_domain, domain = web_search._extract_domain_from_query("tell me about zapagi.com")
        
        assert has_domain is True
        assert domain == "zapagi.com"
    
    def test_extract_domain_from_full_url(self, web_search):
        """Test extracting domain from full URL"""
        has_domain, domain = web_search._extract_domain_from_query("https://www.zapagi.com/services")
        
        assert has_domain is True
        assert domain == "zapagi.com"
    
    def test_extract_domain_with_subdomain(self, web_search):
        """Test extracting registered domain ignoring subdomain"""
        has_domain, domain = web_search._extract_domain_from_query("blog.zapagi.com")
        
        assert has_domain is True
        assert domain == "zapagi.com"
    
    def test_no_domain_in_query(self, web_search):
        """Test query without domain"""
        has_domain, domain = web_search._extract_domain_from_query("what is artificial intelligence")
        
        assert has_domain is False
        assert domain == ""
    
    def test_filter_by_domain_exact_match(self, web_search):
        """Test filtering results by exact domain match"""
        results = [
            {"url": "https://zapagi.com/about", "title": "About ZapAGI"},
            {"url": "https://example.com/zapagi", "title": "Example"},
            {"url": "https://www.zapagi.com/services", "title": "Services"},
        ]
        
        filtered = web_search._filter_by_domain(results, "zapagi.com")
        
        assert len(filtered) == 2
        assert all("zapagi.com" in r["url"] for r in filtered)
    
    def test_filter_by_domain_no_matches(self, web_search):
        """Test filtering when no results match domain"""
        results = [
            {"url": "https://example.com/page1", "title": "Example 1"},
            {"url": "https://test.com/page2", "title": "Test 2"},
        ]
        
        filtered = web_search._filter_by_domain(results, "zapagi.com")
        
        assert len(filtered) == 0
    
    def test_filter_handles_empty_urls(self, web_search):
        """Test filtering handles results with no URL"""
        results = [
            {"url": "", "title": "No URL"},
            {"url": "https://zapagi.com", "title": "ZapAGI"},
        ]
        
        filtered = web_search._filter_by_domain(results, "zapagi.com")
        
        assert len(filtered) == 1
        assert filtered[0]["url"] == "https://zapagi.com"
    
    def test_extract_domain_uk_tld(self, web_search):
        """Test extracting domain with .co.uk TLD"""
        has_domain, domain = web_search._extract_domain_from_query("bbc.co.uk news")
        
        assert has_domain is True
        assert domain == "bbc.co.uk"
    
    def test_extract_domain_various_formats(self, web_search):
        """Test various domain formats"""
        test_cases = [
            ("check out openai.com", "openai.com"),
            ("visit https://github.com/repo", "github.com"),
            ("www.google.com search", "google.com"),
            ("info on microsoft.com", "microsoft.com"),
        ]
        
        for query, expected_domain in test_cases:
            has_domain, domain = web_search._extract_domain_from_query(query)
            assert has_domain is True
            assert domain == expected_domain, f"Failed for query: {query}"
