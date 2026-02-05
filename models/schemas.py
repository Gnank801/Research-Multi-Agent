"""Pydantic schemas for structured LLM outputs."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class ResearchSubtask(BaseModel):
    """A single research subtask."""
    id: int = Field(description="Subtask ID")
    description: str = Field(description="What to research")
    tools_needed: List[str] = Field(description="Tools to use: tavily, arxiv, wikipedia, calculator, python")
    priority: Literal["high", "medium", "low"] = Field(default="medium")


class ResearchPlan(BaseModel):
    """Structured research plan from Planner Agent."""
    query_understanding: str = Field(description="Understanding of what user wants")
    complexity: Literal["simple", "moderate", "complex"] = Field(description="Query complexity")
    subtasks: List[ResearchSubtask] = Field(description="List of research subtasks")
    expected_sections: List[str] = Field(description="Expected report sections")
    estimated_sources: int = Field(description="Estimated number of sources needed")


class SourceInfo(BaseModel):
    """Information about a source."""
    title: str
    url: Optional[str] = None
    source_type: Literal["web", "arxiv", "wikipedia", "calculation"]
    snippet: str


class ResearchFindings(BaseModel):
    """Findings from Executor Agent."""
    subtask_id: int
    findings: str = Field(description="Research findings for this subtask")
    sources: List[SourceInfo] = Field(default_factory=list)
    code_examples: Optional[str] = None
    needs_more_research: bool = False


class VerificationResult(BaseModel):
    """Result from Verifier Agent."""
    is_complete: bool = Field(description="Whether research is complete")
    is_accurate: bool = Field(description="Whether findings appear accurate")
    missing_aspects: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0, le=1, description="Confidence in findings")
    approved: bool = Field(description="Whether to proceed to synthesis")


class FinalReport(BaseModel):
    """Final synthesized report."""
    title: str
    executive_summary: str
    sections: List[dict] = Field(description="List of {heading, content} dicts")
    references: List[SourceInfo]
    generated_at: str


class AgentState(BaseModel):
    """State passed between agents in LangGraph."""
    query: str
    plan: Optional[ResearchPlan] = None
    findings: List[ResearchFindings] = Field(default_factory=list)
    verification: Optional[VerificationResult] = None
    report: Optional[FinalReport] = None
    current_step: str = "planning"
    iteration: int = 0
    messages: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
