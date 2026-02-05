"""LangGraph workflow connecting all agents."""

from typing import TypedDict, Annotated, List, Dict, Any, Callable, Optional
from langgraph.graph import StateGraph, END
from agents.planner import PlannerAgent
from agents.executor import ExecutorAgent
from agents.verifier import VerifierAgent
from agents.synthesizer import SynthesizerAgent
from config import MAX_VERIFICATION_RETRIES


class ResearchState(TypedDict):
    """State passed between nodes in the graph."""
    query: str
    plan: Optional[Dict[str, Any]]
    findings: List[Dict[str, Any]]
    verification: Optional[Dict[str, Any]]
    report: Optional[Dict[str, Any]]
    current_step: str
    iteration: int
    messages: List[str]
    errors: List[str]


class ResearchWorkflow:
    """LangGraph workflow for multi-agent research."""
    
    def __init__(self, callback: Callable[[str, str], None] = None):
        """
        Initialize the research workflow.
        
        Args:
            callback: Optional callback(step, message) for progress updates
        """
        self.callback = callback or (lambda s, m: None)
        
        # Initialize agents
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent()
        self.verifier = VerifierAgent()
        self.synthesizer = SynthesizerAgent()
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _notify(self, step: str, message: str):
        """Send progress notification."""
        self.callback(step, message)
    
    def _plan_node(self, state: ResearchState) -> ResearchState:
        """Planning node - creates research plan."""
        self._notify("planning", "🧠 Creating research plan...")
        
        result = self.planner.plan(state["query"])
        
        if result["success"]:
            state["plan"] = result["plan"]
            state["current_step"] = "executing"
            state["messages"].append("✅ Research plan created")
            self._notify("planning", f"✅ Plan ready: {len(result['plan']['subtasks'])} subtasks")
        else:
            state["errors"].append(result.get("error", "Planning failed"))
            state["current_step"] = "error"
            self._notify("planning", f"❌ Planning failed: {result.get('error')}")
        
        return state
    
    def _execute_node(self, state: ResearchState) -> ResearchState:
        """Execution node - runs research using tools."""
        self._notify("executing", "⚡ Executing research plan...")
        
        def progress_callback(msg):
            self._notify("executing", msg)
        
        findings = self.executor.execute_plan(state["plan"], callback=progress_callback)
        
        state["findings"].extend(findings)
        state["current_step"] = "verifying"
        state["messages"].append(f"✅ Gathered {len(findings)} findings")
        
        total_sources = sum(len(f.get("sources", [])) for f in findings)
        self._notify("executing", f"✅ Research complete: {total_sources} sources collected")
        
        return state
    
    def _verify_node(self, state: ResearchState) -> ResearchState:
        """Verification node - reviews findings."""
        self._notify("verifying", "✅ Verifying research quality...")
        
        result = self.verifier.verify(
            state["query"],
            state["plan"],
            state["findings"]
        )
        
        verification = result["verification"]
        state["verification"] = verification
        
        if verification["approved"]:
            state["current_step"] = "synthesizing"
            state["messages"].append(f"✅ Research verified (confidence: {verification['confidence_score']:.0%})")
            self._notify("verifying", f"✅ Verified with {verification['confidence_score']:.0%} confidence")
        else:
            state["iteration"] += 1
            if state["iteration"] < MAX_VERIFICATION_RETRIES:
                state["current_step"] = "executing"
                state["messages"].append(f"🔄 Need more research: {', '.join(verification.get('missing_aspects', []))}")
                self._notify("verifying", "🔄 Requesting additional research...")
            else:
                state["current_step"] = "synthesizing"
                state["messages"].append("⚠️ Max iterations reached, proceeding anyway")
                self._notify("verifying", "⚠️ Proceeding with available findings")
        
        return state
    
    def _synthesize_node(self, state: ResearchState) -> ResearchState:
        """Synthesis node - creates final report."""
        self._notify("synthesizing", "📝 Writing research report...")
        
        result = self.synthesizer.synthesize(
            state["query"],
            state["plan"],
            state["findings"]
        )
        
        if result["success"]:
            state["report"] = result["report"]
            state["current_step"] = "complete"
            state["messages"].append("✅ Report generated successfully")
            self._notify("synthesizing", "✅ Report complete!")
        else:
            state["errors"].append("Synthesis failed")
            state["current_step"] = "error"
        
        return state
    
    def _should_continue(self, state: ResearchState) -> str:
        """Determine next node based on current step."""
        step = state["current_step"]
        
        if step == "executing":
            return "execute"
        elif step == "verifying":
            return "verify"
        elif step == "synthesizing":
            return "synthesize"
        elif step == "complete":
            return END
        elif step == "error":
            return END
        else:
            return END
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(ResearchState)
        
        # Add nodes
        workflow.add_node("plan", self._plan_node)
        workflow.add_node("execute", self._execute_node)
        workflow.add_node("verify", self._verify_node)
        workflow.add_node("synthesize", self._synthesize_node)
        
        # Set entry point
        workflow.set_entry_point("plan")
        
        # Add edges
        workflow.add_conditional_edges(
            "plan",
            self._should_continue,
            {
                "execute": "execute",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "execute",
            self._should_continue,
            {
                "verify": "verify",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "verify",
            self._should_continue,
            {
                "execute": "execute",  # Loop back for more research
                "synthesize": "synthesize",
                END: END
            }
        )
        
        workflow.add_edge("synthesize", END)
        
        return workflow.compile()
    
    def run(self, query: str) -> Dict[str, Any]:
        """
        Run the complete research workflow.
        
        Args:
            query: User's research query
            
        Returns:
            Final state with report
        """
        initial_state: ResearchState = {
            "query": query,
            "plan": None,
            "findings": [],
            "verification": None,
            "report": None,
            "current_step": "planning",
            "iteration": 0,
            "messages": [],
            "errors": []
        }
        
        final_state = self.graph.invoke(initial_state)
        
        return final_state
