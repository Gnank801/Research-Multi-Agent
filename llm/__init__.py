"""LLM Configuration and Utilities for DeepResearch Agent."""

from langchain_groq import ChatGroq
from config import GROQ_API_KEY, MODEL_NAME, TEMPERATURE


def get_llm(temperature: float = None, max_tokens: int = None):
    """
    Get a configured LLM instance.
    
    Args:
        temperature: Override default temperature
        max_tokens: Maximum tokens for response
        
    Returns:
        Configured ChatGroq instance
    """
    return ChatGroq(
        api_key=GROQ_API_KEY,
        model_name=MODEL_NAME,
        temperature=temperature or TEMPERATURE,
        max_tokens=max_tokens,
        max_retries=3,
    )


# Available models on Groq
AVAILABLE_MODELS = [
    "llama-3.1-8b-instant",      # Fast, good for simple tasks
    "llama-3.1-70b-versatile",   # Powerful, better reasoning
    "llama-3.3-70b-versatile",   # Latest, best quality
    "mixtral-8x7b-32768",        # Good for long context
]
