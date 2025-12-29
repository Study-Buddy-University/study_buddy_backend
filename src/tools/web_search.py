"""
Web search tool using SearXNG self-hosted metasearch engine.
"""

from typing import Any, Dict, List
import re
import aiohttp
import tldextract
from .base import Tool, ToolResult


class WebSearchTool(Tool):
    """
    Web search tool that searches the internet using SearXNG metasearch engine.
    Aggregates results from multiple search engines (Google, Bing, DuckDuckGo, etc.)
    Returns relevant search results with titles, snippets, and URLs.
    """
    
    def __init__(self, searxng_url: str = "http://searxng:8080"):
        super().__init__()
        self.searxng_url = searxng_url.rstrip('/')
        self.tld_extractor = tldextract.TLDExtract(cache_dir=None)
    
    def get_name(self) -> str:
        return "web_search"
    
    def get_description(self) -> str:
        return (
            "Searches the web for information using multiple search engines. "
            "Returns relevant results with titles, snippets, and URLs. "
            "Use this when you need current information, facts, research, "
            "or want to find resources online."
        )
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query to look up on the web"
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5, max: 15)",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    
    def _extract_domain_from_query(self, query: str) -> tuple[bool, str]:
        """
        Check if query contains a domain/URL and extract it.
        
        Returns:
            (has_domain, domain) tuple
        """
        # Regex for domains/URLs
        url_pattern = r'(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?)'
        match = re.search(url_pattern, query)
        
        if match:
            extracted = self.tld_extractor(match.group(0))
            domain = extracted.registered_domain
            if domain:
                return True, domain
        
        return False, ""
    
    def _filter_by_domain(self, results: List[Dict], target_domain: str) -> List[Dict]:
        """
        Filter results to only include target domain.
        
        Args:
            results: List of search results
            target_domain: Domain to filter for (e.g., "zapagi.com")
            
        Returns:
            Filtered list of results
        """
        filtered = []
        for result in results:
            url = result.get('url', '')
            if url:
                extracted = self.tld_extractor(url)
                result_domain = extracted.registered_domain
                if result_domain == target_domain:
                    filtered.append(result)
        return filtered
    
    async def execute(self, query: str, num_results: int = 5, **kwargs) -> ToolResult:
        """
        Execute a web search query using SearXNG.
        
        Args:
            query: Search query string
            num_results: Number of results to return (default: 5, max: 15)
            
        Returns:
            ToolResult with search results or error
        """
        try:
            # Convert to int if string (LLM may pass as string)
            if isinstance(num_results, str):
                num_results = int(num_results)
            
            # Limit results
            num_results = min(num_results, 15)
            
            # Check if query contains a domain
            has_domain, target_domain = self._extract_domain_from_query(query)
            
            # Use SearXNG JSON API
            url = f"{self.searxng_url}/search"
            params = {
                "q": query,
                "format": "json",
                "language": "en",
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=15) as response:
                    if response.status != 200:
                        return ToolResult(
                            success=False,
                            error=f"Search service returned status {response.status}"
                        )
                    
                    data = await response.json()
                    
                    # Extract search results
                    search_results = data.get("results", [])
                    
                    if not search_results:
                        return ToolResult(
                            success=True,
                            result="No results found for this query. Try rephrasing your search.",
                            metadata={"query": query, "num_results": 0}
                        )
                    
                    # Process results
                    results = []
                    for item in search_results:
                        results.append({
                            "title": item.get("title", "No title"),
                            "snippet": item.get("content", item.get("snippet", "No description available")),
                            "url": item.get("url", ""),
                            "engine": item.get("engine", "unknown")
                        })
                    
                    # Apply domain filtering if query contains a domain
                    if has_domain and target_domain:
                        original_count = len(results)
                        results = self._filter_by_domain(results, target_domain)
                        
                        # If no results match the domain, return helpful message
                        if not results:
                            return ToolResult(
                                success=True,
                                result=f"No reliable information found for {target_domain}. The search returned {original_count} results but none were from the target domain.",
                                metadata={
                                    "query": query,
                                    "target_domain": target_domain,
                                    "num_results": 0,
                                    "filtered": True,
                                    "original_count": original_count
                                }
                            )
                    
                    # Take top N results
                    results = results[:num_results]
                    
                    # Format results as readable text
                    result_text = f"Search results for '{query}':\n\n"
                    for i, result in enumerate(results, 1):
                        result_text += f"{i}. {result['title']}\n"
                        result_text += f"   {result['snippet'][:200]}{'...' if len(result['snippet']) > 200 else ''}\n"
                        result_text += f"   URL: {result['url']}\n"
                        result_text += f"   Source: {result['engine']}\n\n"
                    
                    metadata = {
                        "query": query,
                        "num_results": len(results),
                        "results": results,
                        "search_engine": "SearXNG"
                    }
                    
                    # Add domain filtering metadata
                    if has_domain and target_domain:
                        metadata["filtered_by_domain"] = target_domain
                        metadata["domain_filtering_enabled"] = True
                    
                    return ToolResult(
                        success=True,
                        result=result_text.strip(),
                        metadata=metadata
                    )
                    
        except aiohttp.ClientError as e:
            return ToolResult(
                success=False,
                error=f"Network error during search: {str(e)}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Search error: {str(e)}"
            )
