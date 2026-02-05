"""Tavily web search tool."""

from typing import List, Dict, Any
from tavily import TavilyClient
from config import TAVILY_API_KEY, MAX_SEARCH_RESULTS


def tavily_search(query: str, max_results: int = None) -> List[Dict[str, Any]]:
    """
    Search the web using Tavily API.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        
    Returns:
        List of search results with title, url, and content
    """
    if not TAVILY_API_KEY:
        return [{"error": "TAVILY_API_KEY not configured"}]
    
    max_results = max_results or MAX_SEARCH_RESULTS
    
    try:
        client = TavilyClient(api_key=TAVILY_API_KEY)
        response = client.search(
            query=query,
            max_results=max_results,
            include_answer=True,
            include_raw_content=False,
        )
        
        results = []
        
        # Include the AI-generated answer if available
        if response.get("answer"):
            results.append({
                "title": "AI Summary",
                "url": None,
                "content": response["answer"],
                "source_type": "web"
            })
        
        # Add search results
        for result in response.get("results", []):
            results.append({
                "title": result.get("title", "Untitled"),
                "url": result.get("url", ""),
                "content": result.get("content", "")[:500],  # Limit content length
                "source_type": "web"
            })
            
        return results
        
    except Exception as e:
        return [{"error": f"Tavily search failed: {str(e)}"}]
