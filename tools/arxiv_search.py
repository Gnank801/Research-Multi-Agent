"""ArXiv scientific paper search tool."""

from typing import List, Dict, Any
import arxiv
from config import MAX_ARXIV_RESULTS


def arxiv_search(query: str, max_results: int = None) -> List[Dict[str, Any]]:
    """
    Search ArXiv for scientific papers.
    
    Args:
        query: Search query for papers
        max_results: Maximum number of papers to return
        
    Returns:
        List of papers with title, authors, abstract, and URL
    """
    max_results = max_results or MAX_ARXIV_RESULTS
    
    try:
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        results = []
        for paper in client.results(search):
            # Format authors
            authors = ", ".join([author.name for author in paper.authors[:3]])
            if len(paper.authors) > 3:
                authors += " et al."
            
            results.append({
                "title": paper.title,
                "authors": authors,
                "abstract": paper.summary[:600] + "..." if len(paper.summary) > 600 else paper.summary,
                "url": paper.entry_id,
                "pdf_url": paper.pdf_url,
                "published": paper.published.strftime("%Y-%m-%d") if paper.published else None,
                "source_type": "arxiv"
            })
            
        return results
        
    except Exception as e:
        return [{"error": f"ArXiv search failed: {str(e)}"}]
