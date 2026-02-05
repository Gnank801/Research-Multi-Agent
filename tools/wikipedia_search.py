"""Wikipedia search and lookup tool."""

from typing import List, Dict, Any
import wikipedia
from config import MAX_WIKI_RESULTS


def wikipedia_search(query: str, max_results: int = None) -> List[Dict[str, Any]]:
    """
    Search Wikipedia for articles.
    
    Args:
        query: Search query
        max_results: Maximum number of results
        
    Returns:
        List of Wikipedia articles with title, summary, and URL
    """
    max_results = max_results or MAX_WIKI_RESULTS
    
    try:
        # Search for page titles
        search_results = wikipedia.search(query, results=max_results)
        
        results = []
        for title in search_results:
            try:
                page = wikipedia.page(title, auto_suggest=False)
                results.append({
                    "title": page.title,
                    "summary": page.summary[:800] + "..." if len(page.summary) > 800 else page.summary,
                    "url": page.url,
                    "source_type": "wikipedia"
                })
            except wikipedia.exceptions.DisambiguationError as e:
                # If disambiguation, try first option
                if e.options:
                    try:
                        page = wikipedia.page(e.options[0], auto_suggest=False)
                        results.append({
                            "title": page.title,
                            "summary": page.summary[:800] + "..." if len(page.summary) > 800 else page.summary,
                            "url": page.url,
                            "source_type": "wikipedia"
                        })
                    except:
                        pass
            except wikipedia.exceptions.PageError:
                continue
            except Exception:
                continue
                
        return results
        
    except Exception as e:
        return [{"error": f"Wikipedia search failed: {str(e)}"}]
