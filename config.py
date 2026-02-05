"""Configuration settings for DeepResearch Agent."""

import os
import time
from dotenv import load_dotenv

load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Model Configuration - Use faster model to avoid rate limits
MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.1-8b-instant")
TEMPERATURE = 0.1

# Search Configuration
MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "5"))
MAX_ARXIV_RESULTS = 3
MAX_WIKI_RESULTS = 2

# Agent Configuration
MAX_EXECUTOR_ITERATIONS = 10
MAX_VERIFICATION_RETRIES = 2

# Rate limiting - delay between LLM calls (seconds)
LLM_CALL_DELAY = 0.5


def rate_limit_delay():
    """Add a small delay to avoid rate limits."""
    time.sleep(LLM_CALL_DELAY)
