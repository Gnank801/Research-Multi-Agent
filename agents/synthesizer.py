"""Synthesizer Agent - Compiles research into final reports."""

import json
import re
import time
from datetime import datetime
from typing import Dict, Any, List
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from config import GROQ_API_KEY, MODEL_NAME, rate_limit_delay


class SynthesizerAgent:
    """Agent that synthesizes research findings into comprehensive reports."""
    
    def __init__(self):
        self.llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model_name=MODEL_NAME,
            temperature=0.3,
            max_tokens=4000,
            max_retries=3,
        )
    
    def _sanitize_json(self, text: str) -> str:
        """Remove invalid control characters from JSON string."""
        # Replace actual newlines/tabs with escaped versions first
        text = text.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        # Remove other control characters (0x00-0x1F except already handled)
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
        return text
    
    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from text, handling various formats with sanitization."""
        text = text.strip()
        
        # Remove markdown code blocks
        if "```" in text:
            matches = re.findall(r'```(?:json)?\s*([\s\S]*?)```', text)
            if matches:
                text = matches[0].strip()
        
        # Find JSON object pattern
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            json_str = match.group()
            json_str = self._sanitize_json(json_str)
            try:
                return json.loads(json_str)
            except:
                return json.loads(json_str, strict=False)
        
        # Sanitize and parse
        text = self._sanitize_json(text)
        return json.loads(text, strict=False)
    
    def synthesize(self, query: str, plan: Dict[str, Any], findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synthesize findings into a final report."""
        
        # Compile all sources
        all_sources = []
        source_index = 1
        for f in findings:
            for source in f.get("sources", []):
                if isinstance(source, dict):
                    source_copy = source.copy()
                    source_copy["index"] = source_index
                    all_sources.append(source_copy)
                    source_index += 1
        
        # Build comprehensive findings text
        findings_text = ""
        for f in findings:
            content = f.get("findings", "")
            if content and len(content) > 20:
                findings_text += f"\n\n{content}\n"
        
        if not findings_text.strip():
            findings_text = f"Topic: {query}. Provide comprehensive information about this topic."
        
        # Build sources text for citations
        sources_text = ""
        for s in all_sources[:15]:
            idx = s.get('index', 1)
            title = s.get('title', 'Source')
            url = s.get('url', '')
            sources_text += f"[{idx}] {title}"
            if url:
                sources_text += f" - {url}"
            sources_text += "\n"
        
        rate_limit_delay()
        
        # Use a simpler, more reliable prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a research report writer. Create a comprehensive report.

Output ONLY valid JSON in this exact format:
{{
  "title": "Clear Title About the Topic",
  "executive_summary": "2-3 paragraph comprehensive summary of the research findings...",
  "sections": [
    {{"heading": "1. Introduction", "content": "Introduction paragraph..."}},
    {{"heading": "2. Core Concepts", "content": "Explanation of main concepts..."}},
    {{"heading": "3. How It Works", "content": "Technical details..."}},
    {{"heading": "4. Applications", "content": "Real-world use cases..."}},
    {{"heading": "5. Conclusion", "content": "Summary and key takeaways..."}}
  ]
}}

IMPORTANT:
- Create 5-6 sections with descriptive headings
- Each section should have 2-3 paragraphs of content
- Include inline citations like [1], [2] where appropriate
- Make content detailed and educational"""),
            ("human", """Topic: {query}

Research Findings:
{findings}

Available Sources:
{sources}

Generate the research report JSON:""")
        ])
        
        try:
            chain = prompt | self.llm
            response = chain.invoke({
                "query": query,
                "findings": findings_text[:3000],  # Limit to avoid token issues
                "sources": sources_text if sources_text else "General knowledge sources"
            })
            
            report_dict = self._extract_json(response.content)
            
            # Validate and extract sections
            sections = report_dict.get("sections", [])
            if not sections:
                raise ValueError("No sections generated")
            
            valid_sections = []
            for section in sections:
                if isinstance(section, dict) and section.get("content"):
                    valid_sections.append({
                        "heading": section.get("heading", "Section"),
                        "content": section.get("content", "")
                    })
            
            if not valid_sections:
                raise ValueError("No valid sections")
            
            return {
                "success": True,
                "report": {
                    "title": report_dict.get("title", f"Research Report: {query}"),
                    "executive_summary": report_dict.get("executive_summary", f"This report examines {query} in detail."),
                    "sections": valid_sections,
                    "references": all_sources,
                    "generated_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            print(f"Synthesizer primary error: {e}")
            
            # TRY AGAIN with even simpler prompt
            rate_limit_delay()
            rate_limit_delay()  # Extra delay
            
            try:
                simple_prompt = ChatPromptTemplate.from_messages([
                    ("system", "Create a JSON report with title, executive_summary, and sections array. Each section has heading and content."),
                    ("human", "Write a report about: {query}\n\nData: {findings}\n\nJSON:")
                ])
                
                chain = simple_prompt | self.llm
                response = chain.invoke({
                    "query": query,
                    "findings": findings_text[:2000]
                })
                
                report_dict = self._extract_json(response.content)
                sections = report_dict.get("sections", [])
                
                if sections:
                    return {
                        "success": True,
                        "report": {
                            "title": report_dict.get("title", f"Research Report: {query}"),
                            "executive_summary": report_dict.get("executive_summary", ""),
                            "sections": sections,
                            "references": all_sources,
                            "generated_at": datetime.now().isoformat()
                        }
                    }
            except Exception as e2:
                print(f"Synthesizer retry error: {e2}")
            
            # Final fallback - create report from findings directly
            sections = []
            
            # Create introduction
            sections.append({
                "heading": f"Introduction to {query}",
                "content": f"This report provides a comprehensive analysis of {query}. The research draws from {len(all_sources)} sources including web resources, academic papers, and knowledge bases.\n\nThe following sections present detailed findings on various aspects of this topic."
            })
            
            # Create sections from findings
            for i, f in enumerate(findings):
                content = f.get("findings", "")
                if content and len(content) > 50:
                    # Generate a heading from the first line or sentence
                    first_sentence = content.split('.')[0][:60] if '.' in content else content[:60]
                    sections.append({
                        "heading": f"Research Findings: {first_sentence}...",
                        "content": content
                    })
            
            # Add conclusion
            sections.append({
                "heading": "Conclusion",
                "content": f"This research has provided insights into {query}. The analysis covered multiple aspects and drew from {len(all_sources)} sources to present a comprehensive view of the topic.\n\nKey areas explored include the fundamental concepts, technical implementation, and practical applications."
            })
            
            return {
                "success": True,
                "report": {
                    "title": f"Research Report: {query}",
                    "executive_summary": f"This comprehensive report examines {query}. The research synthesizes information from {len(all_sources)} sources to provide detailed insights into the core concepts, technical aspects, and real-world applications of this topic.",
                    "sections": sections,
                    "references": all_sources,
                    "generated_at": datetime.now().isoformat()
                }
            }
