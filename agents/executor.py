"""Executor Agent - Executes research plan using tools."""

import json
import re
import time
from typing import Dict, Any, List, Callable
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from config import GROQ_API_KEY, MODEL_NAME, TEMPERATURE, rate_limit_delay
from models.schemas import ResearchFindings, SourceInfo
from tools import tavily_search, arxiv_search, wikipedia_search, calculator, python_executor


class ExecutorAgent:
    """Agent that executes research using available tools."""
    
    def __init__(self):
        self.llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model_name=MODEL_NAME,
            temperature=TEMPERATURE,
            max_retries=3,
        )
        
        # Available tools
        self.tools: Dict[str, Callable] = {
            "tavily": tavily_search,
            "arxiv": arxiv_search,
            "wikipedia": wikipedia_search,
            "calculator": calculator,
            "python": python_executor,
        }
    
    def _sanitize_json(self, text: str) -> str:
        """Remove invalid control characters from JSON string."""
        # Remove control characters except valid JSON ones (\n, \r, \t)
        import re
        # Replace actual newlines/tabs with escaped versions first
        text = text.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        # Remove other control characters (0x00-0x1F except already handled)
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
        return text
    
    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from text with sanitization."""
        text = text.strip()
        
        # Remove markdown code blocks
        if "```" in text:
            matches = re.findall(r'```(?:json)?\s*([\s\S]*?)```', text)
            if matches:
                text = matches[0].strip()
        
        # Try to find JSON object
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            json_str = match.group()
            # Sanitize before parsing
            json_str = self._sanitize_json(json_str)
            try:
                return json.loads(json_str)
            except:
                # Try with strict=False
                return json.loads(json_str, strict=False)
        
        # Sanitize and parse
        text = self._sanitize_json(text)
        return json.loads(text, strict=False)
    
    def execute_subtask(self, subtask: Dict[str, Any], previous_findings: str = "") -> Dict[str, Any]:
        """Execute a single research subtask by calling tools directly."""
        all_results = []
        sources = []
        
        tools_to_try = subtask.get("tools_needed", ["tavily", "wikipedia"])
        query = subtask.get("description", "")
        
        # Execute each tool directly without LLM decision (faster, no rate limits)
        for tool_name in tools_to_try[:2]:  # Limit to 2 tools per subtask
            try:
                tool_func = self.tools.get(tool_name)
                if not tool_func:
                    continue
                    
                # Create appropriate query for each tool
                if tool_name == "calculator":
                    continue  # Skip calculator unless specifically needed
                elif tool_name == "python":
                    continue  # Skip python executor for now
                
                result = tool_func(query)
                
                if isinstance(result, list):
                    for r in result:
                        if isinstance(r, dict) and "error" not in r:
                            all_results.append(r)
                            sources.append(SourceInfo(
                                title=r.get("title", "Source"),
                                url=r.get("url"),
                                source_type=r.get("source_type", "web"),
                                snippet=str(r.get("content", r.get("abstract", r.get("summary", ""))))[:400]
                            ))
                elif isinstance(result, dict) and "error" not in result:
                    all_results.append(result)
                    
            except Exception as e:
                print(f"Tool {tool_name} error: {e}")
                continue
        
        # Synthesize findings using LLM
        rate_limit_delay()
        
        try:
            synthesis_prompt = ChatPromptTemplate.from_messages([
                ("system", """Summarize the research findings into 2-3 detailed paragraphs.
Be specific and informative. Include facts, definitions, and key insights.
Respond with ONLY a JSON object:
{{"findings": "Your detailed summary here...", "key_points": ["point1", "point2"]}}"""),
                ("human", "Task: {task}\n\nResearch Data:\n{data}")
            ])
            
            # Prepare data text
            data_text = ""
            for r in all_results[:5]:
                if isinstance(r, dict):
                    title = r.get("title", "")
                    content = r.get("content", r.get("abstract", r.get("summary", "")))
                    if content:
                        data_text += f"\n[{title}]: {str(content)[:500]}\n"
            
            if not data_text.strip():
                data_text = f"Topic: {query}. Provide general knowledge about this topic."
            
            chain = synthesis_prompt | self.llm
            response = chain.invoke({"task": query, "data": data_text})
            
            synthesis = self._extract_json(response.content)
            findings_text = synthesis.get("findings", "")
            
            if not findings_text or len(findings_text) < 50:
                # Use raw data if synthesis failed
                findings_text = f"Research on {query}:\n\n"
                for r in all_results[:3]:
                    if isinstance(r, dict):
                        content = r.get("content", r.get("abstract", r.get("summary", "")))
                        if content:
                            findings_text += f"{str(content)[:400]}\n\n"
            
            return {
                "subtask_id": subtask.get("id", 1),
                "findings": findings_text,
                "sources": [s.model_dump() for s in sources],
                "code_examples": None,
                "needs_more_research": False
            }
            
        except Exception as e:
            print(f"Synthesis error: {e}")
            # Fallback: Return raw findings
            findings_text = f"Research on {query}:\n\n"
            for r in all_results[:3]:
                if isinstance(r, dict):
                    content = r.get("content", r.get("abstract", r.get("summary", "")))
                    if content:
                        findings_text += f"{str(content)[:400]}\n\n"
            
            if len(findings_text) < 50:
                findings_text = f"Explored {query}. Found {len(sources)} relevant sources."
            
            return {
                "subtask_id": subtask.get("id", 1),
                "findings": findings_text,
                "sources": [s.model_dump() for s in sources],
                "code_examples": None,
                "needs_more_research": False
            }
    
    def execute_plan(self, plan: Dict[str, Any], callback: Callable = None) -> List[Dict[str, Any]]:
        """Execute all subtasks in a research plan."""
        all_findings = []
        previous_summary = ""
        
        subtasks = plan.get("subtasks", [])
        
        for i, subtask in enumerate(subtasks):
            if callback:
                callback(f"Executing subtask {i+1}/{len(subtasks)}: {subtask.get('description', '')[:50]}...")
            
            findings = self.execute_subtask(subtask, previous_summary)
            all_findings.append(findings)
            
            # Update previous summary for context
            if findings.get("findings"):
                previous_summary += f"\n- {findings['findings'][:200]}"
            
            # Small delay between subtasks
            time.sleep(0.3)
        
        return all_findings
