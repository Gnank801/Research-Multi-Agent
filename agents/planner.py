"""Planner Agent - Analyzes queries and creates research plans."""

import json
from typing import Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from config import GROQ_API_KEY, MODEL_NAME, TEMPERATURE
from models.schemas import ResearchPlan


class PlannerAgent:
    """Agent that creates structured research plans from user queries."""
    
    def __init__(self):
        self.llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model_name=MODEL_NAME,
            temperature=TEMPERATURE,
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Research Planner Agent. Your job is to analyze research queries and create structured plans.

Given a user's research query, create a comprehensive plan that breaks down the research into manageable subtasks.

You MUST respond with a valid JSON object matching this exact schema:
{{
    "query_understanding": "Your understanding of what the user wants to learn",
    "complexity": "simple" | "moderate" | "complex",
    "subtasks": [
        {{
            "id": 1,
            "description": "What to research",
            "tools_needed": ["tavily", "arxiv", "wikipedia", "calculator", "python"],
            "priority": "high" | "medium" | "low"
        }}
    ],
    "expected_sections": ["Section 1", "Section 2", ...],
    "estimated_sources": 5
}}

Available tools:
- tavily: Web search for current information
- arxiv: Scientific papers and academic research  
- wikipedia: Background knowledge and definitions
- calculator: Mathematical calculations
- python: Code examples and demonstrations

Guidelines:
1. Break complex topics into 3-5 subtasks
2. For each subtask, specify which tools would be most helpful
3. Prioritize subtasks (high priority = core concepts, low = nice-to-have)
4. Suggest 4-6 sections for the final report
5. Estimate sources needed (typically 5-10 for good coverage)

Respond ONLY with the JSON object, no additional text."""),
            ("human", "Research Query: {query}")
        ])
    
    def plan(self, query: str) -> Dict[str, Any]:
        """
        Create a research plan for the given query.
        
        Args:
            query: User's research query
            
        Returns:
            Structured research plan
        """
        try:
            chain = self.prompt | self.llm
            response = chain.invoke({"query": query})
            
            # Parse the JSON response
            content = response.content.strip()
            
            # Handle potential markdown code blocks
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            plan_dict = json.loads(content)
            
            # Validate with Pydantic
            plan = ResearchPlan(**plan_dict)
            
            return {
                "success": True,
                "plan": plan.model_dump()
            }
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Failed to parse plan: {str(e)}",
                "raw_response": response.content if 'response' in dir() else None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Planning failed: {str(e)}"
            }
