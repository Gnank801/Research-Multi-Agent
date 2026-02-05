"""
DeepResearch Agent - Autonomous Multi-Agent Research System

A Streamlit application that uses multiple AI agents to research topics
and generate comprehensive, cited reports.
"""

import streamlit as st
from datetime import datetime
import time

# Page config must be first Streamlit command
st.set_page_config(
    page_title="DeepResearch Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        max-width: 1200px;
    }
    
    /* Agent status cards */
    .agent-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    }
    
    .agent-inactive {
        background: linear-gradient(135deg, #434343 0%, #000000 100%);
        opacity: 0.6;
    }
    
    .agent-active {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(102, 126, 234, 0); }
        100% { box-shadow: 0 0 0 0 rgba(102, 126, 234, 0); }
    }
    
    /* Status badges */
    .status-planning { color: #ffd93d; }
    .status-executing { color: #6bcb77; }
    .status-verifying { color: #4d96ff; }
    .status-synthesizing { color: #ff6b6b; }
    .status-complete { color: #6bcb77; }
    
    /* Report styling */
    .report-container {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
    }
    
    /* Tool call styling */
    .tool-call {
        background: #e8f4f8;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 0.25rem 0;
        font-size: 0.9rem;
    }
    
    /* Citation styling */
    .citation {
        font-size: 0.8rem;
        color: #666;
        border-left: 2px solid #ddd;
        padding-left: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "research_history" not in st.session_state:
        st.session_state.research_history = []
    if "current_status" not in st.session_state:
        st.session_state.current_status = None
    if "status_messages" not in st.session_state:
        st.session_state.status_messages = []
    if "is_researching" not in st.session_state:
        st.session_state.is_researching = False


def render_sidebar():
    """Render the sidebar with history and info."""
    with st.sidebar:
        st.markdown("## 🔬 DeepResearch Agent")
        st.markdown("---")
        
        st.markdown("### 🤖 Agents")
        agents = [
            ("🧠", "Planner", "Creates research plan"),
            ("⚡", "Executor", "Runs search tools"),
            ("✅", "Verifier", "Validates findings"),
            ("📝", "Synthesizer", "Writes report"),
        ]
        
        current = st.session_state.current_status
        for emoji, name, desc in agents:
            is_active = current and name.lower() in current.lower()
            status = "🟢" if is_active else "⚪"
            st.markdown(f"{status} **{emoji} {name}**")
            st.caption(desc)
        
        st.markdown("---")
        st.markdown("### 🔧 Tools")
        tools = ["🔍 Tavily Search", "📚 ArXiv Papers", "📖 Wikipedia", "🧮 Calculator", "🐍 Python"]
        for tool in tools:
            st.markdown(f"• {tool}")
        
        st.markdown("---")
        st.markdown("### 📜 History")
        if st.session_state.research_history:
            for i, item in enumerate(reversed(st.session_state.research_history[-5:])):
                with st.expander(f"📄 {item['query'][:30]}..."):
                    st.caption(item['timestamp'])
                    if st.button("Load", key=f"load_{i}"):
                        st.session_state.loaded_report = item['report']
        else:
            st.caption("No research history yet")


def render_status_panel():
    """Render the agent status panel."""
    if st.session_state.status_messages:
        st.markdown("### 📊 Agent Activity")
        
        # Show last 5 messages
        for msg in st.session_state.status_messages[-5:]:
            step = msg.get("step", "")
            message = msg.get("message", "")
            
            icon_map = {
                "planning": "🧠",
                "executing": "⚡",
                "verifying": "✅",
                "synthesizing": "📝"
            }
            icon = icon_map.get(step, "📌")
            
            st.markdown(f"<div class='tool-call'>{icon} {message}</div>", unsafe_allow_html=True)


def render_report(report: dict):
    """Render the final research report."""
    if not report:
        return
    
    st.markdown("---")
    st.markdown(f"# 📄 {report.get('title', 'Research Report')}")
    
    # Executive Summary
    st.markdown("## Executive Summary")
    st.markdown(report.get("executive_summary", ""))
    
    # Main sections
    for section in report.get("sections", []):
        st.markdown(f"## {section.get('heading', 'Section')}")
        st.markdown(section.get("content", ""))
    
    # References
    references = report.get("references", [])
    if references:
        st.markdown("## 📚 References")
        for i, ref in enumerate(references, 1):
            title = ref.get("title", "Untitled")
            url = ref.get("url", "")
            source_type = ref.get("source_type", "web")
            
            type_emoji = {"web": "🌐", "arxiv": "📚", "wikipedia": "📖", "calculation": "🧮"}.get(source_type, "📄")
            
            if url:
                st.markdown(f"[{i}] {type_emoji} [{title}]({url})")
            else:
                st.markdown(f"[{i}] {type_emoji} {title}")
    
    # Metadata
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"Generated: {report.get('generated_at', 'Unknown')}")
    with col2:
        st.caption(f"Sources: {len(references)}")


def run_research(query: str):
    """Run the research workflow."""
    from graph.workflow import ResearchWorkflow
    
    # Status callback
    def status_callback(step: str, message: str):
        st.session_state.current_status = step
        st.session_state.status_messages.append({"step": step, "message": message})
    
    # Create and run workflow
    workflow = ResearchWorkflow(callback=status_callback)
    result = workflow.run(query)
    
    return result


def main():
    """Main application entry point."""
    init_session_state()
    render_sidebar()
    
    # Main content area
    st.markdown("# 🔬 DeepResearch Agent")
    st.markdown("*Autonomous multi-agent system for comprehensive research reports*")
    
    # Query input
    col1, col2 = st.columns([4, 1])
    with col1:
        query = st.text_input(
            "What would you like to research?",
            placeholder="e.g., Explain how transformer attention mechanisms work in LLMs",
            key="query_input"
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        research_button = st.button("🔍 Research", type="primary", use_container_width=True)
    
    # Example prompts
    st.markdown("**Try these examples:**")
    example_cols = st.columns(3)
    examples = [
        "Explain RAG systems and vector databases",
        "How does RLHF work in training LLMs?",
        "Compare React vs Vue.js for web apps"
    ]
    
    for col, example in zip(example_cols, examples):
        with col:
            if st.button(example, key=f"ex_{example[:20]}", use_container_width=True):
                query = example
                research_button = True
    
    st.markdown("---")
    
    # Run research
    if research_button and query:
        st.session_state.status_messages = []
        st.session_state.is_researching = True
        
        with st.spinner("🔬 Researching... This may take 1-2 minutes"):
            try:
                # Create status container
                status_container = st.container()
                
                # Run the research
                result = run_research(query)
                
                # Display status messages
                with status_container:
                    render_status_panel()
                
                # Check for report
                if result.get("report"):
                    report = result["report"]
                    
                    # Save to history
                    st.session_state.research_history.append({
                        "query": query,
                        "report": report,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    
                    # Render report
                    render_report(report)
                    
                    # Download button
                    report_md = f"# {report.get('title', 'Report')}\n\n"
                    report_md += f"## Executive Summary\n{report.get('executive_summary', '')}\n\n"
                    for section in report.get("sections", []):
                        report_md += f"## {section.get('heading', '')}\n{section.get('content', '')}\n\n"
                    
                    st.download_button(
                        "📥 Download Report (Markdown)",
                        report_md,
                        file_name=f"research_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                        mime="text/markdown"
                    )
                else:
                    st.error("❌ Research failed. Please try again.")
                    if result.get("errors"):
                        for error in result["errors"]:
                            st.error(error)
                            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("💡 Make sure your API keys are configured in the .env file")
        
        st.session_state.is_researching = False
    
    # Show loaded report if exists
    elif hasattr(st.session_state, 'loaded_report') and st.session_state.loaded_report:
        render_report(st.session_state.loaded_report)
        st.session_state.loaded_report = None
    
    # Show welcome message
    elif not query:
        st.markdown("""
        ### 👋 Welcome to DeepResearch Agent!
        
        This autonomous research system uses **4 specialized AI agents** working together:
        
        | Agent | Role |
        |-------|------|
        | 🧠 **Planner** | Analyzes your query and creates a research plan |
        | ⚡ **Executor** | Searches the web, papers, and knowledge bases |
        | ✅ **Verifier** | Reviews findings for completeness and accuracy |
        | 📝 **Synthesizer** | Compiles everything into a cited report |
        
        **How it works:**
        1. Enter a research topic above
        2. Watch the agents work in real-time
        3. Get a comprehensive 2-3 page report with citations
        4. Download your report as Markdown
        
        ---
        
        > ⚠️ **Note:** Make sure you have configured your API keys in the `.env` file:
        > - `GROQ_API_KEY` - Get free at [console.groq.com](https://console.groq.com)
        > - `TAVILY_API_KEY` - Get free at [tavily.com](https://tavily.com)
        """)


if __name__ == "__main__":
    main()
