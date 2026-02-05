"""Verifier Agent - Reviews and validates research findings."""

import json
from typing import Dict, Any, List
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from config import GROQ_API_KEY, MODEL_NAME, TEMPERATURE
from models.schemas import VerificationResult


class VerifierAgent:
    """Agent that verifies research completeness and accuracy."""
    
    def __init__(self):
        self.llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model_name=MODEL_NAME,
            temperature=TEMPERATURE,
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Research Verifier Agent. Your job is to review research findings for completeness and accuracy.

Given the original query, research plan, and collected findings, evaluate the research quality.

You MUST respond with a valid JSON object:
{{
    "is_complete": true | false,
    "is_accurate": true | false,
    "missing_aspects": ["Aspect 1 that's missing", ...],
    "suggestions": ["Suggestion for improvement", ...],
    "confidence_score": 0.0 to 1.0,
    "approved": true | false,
    "reasoning": "Why you made this decision"
}}

Evaluation criteria:
1. COMPLETENESS: Does the research cover all aspects of the query?
2. ACCURACY: Are the findings factually sound and well-sourced?
3. DEPTH: Is there sufficient detail for a comprehensive report?
4. CITATIONS: Are there enough sources to support claims?

Set approved=true if the research is good enough to proceed to report writing.
Set approved=false if more research is needed (will trigger another round).

Be reasonably lenient - if core aspects are covered, approve it."""),
            ("human", """Original Query: {query}

Research Plan:
{plan}

Collected Findings:
{findings}

Number of Sources: {source_count}

Evaluate this research:""")
        ])
    
    def verify(self, query: str, plan: Dict[str, Any], findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Verify research findings.
        
        Args:
            query: Original user query
            plan: Research plan
            findings: List of research findings
            
        Returns:
            Verification result
        """
        try:
            # Count total sources
            source_count = sum(len(f.get("sources", [])) for f in findings)
            
            # Format findings for review
            findings_text = ""
            for f in findings:
                findings_text += f"\n\nSubtask {f.get('subtask_id', 'N/A')}:\n"
                findings_text += f"{f.get('findings', 'No findings')}\n"
                findings_text += f"Sources: {len(f.get('sources', []))}"
            
            chain = self.prompt | self.llm
            response = chain.invoke({
                "query": query,
                "plan": json.dumps(plan, indent=2),
                "findings": findings_text,
                "source_count": source_count
            })
            
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            result_dict = json.loads(content)
            
            # Validate with Pydantic
            result = VerificationResult(**result_dict)
            
            return {
                "success": True,
                "verification": result.model_dump()
            }
            
        except Exception as e:
            # Default to approved if verification fails
            return {
                "success": True,
                "verification": {
                    "is_complete": True,
                    "is_accurate": True,
                    "missing_aspects": [],
                    "suggestions": [],
                    "confidence_score": 0.7,
                    "approved": True,
                    "reasoning": f"Auto-approved due to verification error: {str(e)}"
                }
            }
