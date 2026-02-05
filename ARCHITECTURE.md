# DeepResearch Agent - Architecture

## Overview

DeepResearch Agent is a **multi-agent AI system** that transforms natural language research queries into comprehensive, cited reports. The system uses a pipeline of specialized agents coordinated by LangGraph.

---

## System Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                  │
│                         (Streamlit @ localhost:8501)                         │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │  📝 Query Input  │  📊 Agent Status  │  📄 Report View  │  ⬇️ Download  │  
│  └────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────┬────────────────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                           LANGGRAPH WORKFLOW                                  │
│                         (State Machine Controller)                            │
│                                                                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   START     │───▶│   PLANNER   │───▶│  EXECUTOR   │───▶│  VERIFIER  │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    └──────┬──────┘     │
│                                              ▲                    │          │
│                                              │   (retry if needed)│          │
│                                              └────────────────────┘          │
│                                                                   │          │
│                                                                   ▼          │
│                                                         ┌─────────────┐      │
│                                                         │ SYNTHESIZER │      │
│                                                         └──────┬──────┘      │
│                                                                │             │
└────────────────────────────────────────────────────────────────┼─────────────┘
                                                                 │
                                                                 ▼
                                                    ┌─────────────────────┐
                                                    │   FINAL REPORT      │
                                                    │  • Executive Summary│
                                                    │  • 5-7 Sections     │
                                                    │  • References       │
                                                    └─────────────────────┘
```

---

## Agent Details

### 1. Planner Agent (`agents/planner.py`)

**Purpose**: Converts user query into a structured research plan.

**Input**: Natural language query (e.g., "Explain how RAG systems work")

**Output**: JSON plan with subtasks
```json
{
  "query_analysis": "User wants to understand RAG architecture",
  "complexity": "complex",
  "subtasks": [
    {
      "id": 1,
      "description": "Define RAG and core components",
      "tools_needed": ["wikipedia", "tavily"]
    },
    {
      "id": 2,
      "description": "Explore vector databases and embeddings",
      "tools_needed": ["arxiv", "tavily"]
    }
  ],
  "expected_sections": ["Introduction", "Architecture", "Applications"]
}
```

**LLM Prompt Strategy**: Constrained JSON schema output with explicit instructions.

---

### 2. Executor Agent (`agents/executor.py`)

**Purpose**: Executes each subtask by calling appropriate tools.

**Flow**:
1. Iterates through subtasks from Planner
2. Calls tools (Tavily, ArXiv, Wikipedia) based on `tools_needed`
3. Synthesizes raw tool results into coherent findings
4. Collects sources for citation

**Tools Available**:
| Tool | API | Purpose |
|------|-----|---------|
| `tavily_search` | Tavily API | Current web information |
| `arxiv_search` | ArXiv API | Academic papers |
| `wikipedia_search` | Wikipedia API | Background knowledge |
| `calculator` | Local | Math expressions |
| `python_executor` | Local (sandboxed) | Code examples |

---

### 3. Verifier Agent (`agents/verifier.py`)

**Purpose**: Validates research quality and completeness.

**Checks**:
- Sufficient coverage of all subtasks
- Quality and depth of findings
- Accuracy of information
- Confidence scoring (0-100%)

**Actions**:
- If confidence ≥ 70%: Proceed to Synthesizer
- If confidence < 70%: Request more research (max 2 retries)

---

### 4. Synthesizer Agent (`agents/synthesizer.py`)

**Purpose**: Compiles findings into a final research report.

**Output Format**:
```json
{
  "title": "Research Report: Topic Name",
  "executive_summary": "2-3 paragraph summary...",
  "sections": [
    {"heading": "1. Introduction", "content": "..."},
    {"heading": "2. Core Concepts", "content": "..."},
    {"heading": "3. Applications", "content": "..."}
  ],
  "references": [
    {"title": "Source Title", "url": "https://...", "snippet": "..."}
  ]
}
```

---

## Tool Integration Details

### Tavily Search API
- **Endpoint**: `api.tavily.com`
- **Purpose**: AI-optimized web search
- **Rate Limit**: 1000 searches/month (free tier)
- **Returns**: Title, URL, content snippet, relevance score

### ArXiv API
- **Endpoint**: `export.arxiv.org/api/query`
- **Purpose**: Academic paper search
- **Rate Limit**: None (public API)
- **Returns**: Title, authors, abstract, PDF link, publication date

### Wikipedia API
- **Endpoint**: `en.wikipedia.org/api`
- **Purpose**: Encyclopedia knowledge
- **Rate Limit**: None (public API)
- **Returns**: Article title, summary, full content, URL

---

## LangGraph State Machine

```python
class ResearchState(TypedDict):
    query: str                    # Original user query
    plan: Dict                    # Planner output
    findings: List[Dict]          # Executor results
    verification: Dict            # Verifier assessment
    report: Dict                  # Final synthesized report
    current_step: str             # Current workflow step
    iteration: int                # Verification retry count
    errors: List[str]             # Error tracking
```

### State Transitions
```
START → plan_step → execute_step → verify_step
                         ↑              ↓
                         └── (retry) ───┘
                                        ↓
                                synthesize_step → END
```

---

## Data Flow

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ PLANNER: "Explain RAG systems"                              │
│    └─▶ JSON Plan: 4 subtasks, tools assigned                │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ EXECUTOR: For each subtask...                               │
│    ├─▶ Tavily: Search "RAG retrieval augmented generation"  │
│    ├─▶ ArXiv: Search "RAG neural information retrieval"     │
│    ├─▶ Wikipedia: Search "Vector database"                  │
│    └─▶ Synthesize: Combine into findings                    │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ VERIFIER: Check completeness                                │
│    ├─▶ Coverage: 85%                                        │
│    ├─▶ Quality: Good                                        │
│    └─▶ Decision: PROCEED (confidence: 85%)                  │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ SYNTHESIZER: Generate report                                │
│    ├─▶ Executive Summary                                    │
│    ├─▶ 6 Detailed Sections                                  │
│    └─▶ 15 References with URLs                              │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
Final Research Report (Markdown)
```

---

## Error Handling

| Error Type | Handling Strategy |
|------------|-------------------|
| API Rate Limit | Retry with exponential backoff |
| JSON Parse Error | Sanitize control characters, use `strict=False` |
| Tool Failure | Skip tool, use other available tools |
| LLM Timeout | Retry up to 3 times |
| Empty Results | Generate from available data |

---

## Configuration

```python
# config.py
GROQ_API_KEY = os.getenv("GROQ_API_KEY")     # Required
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY") # Required
MODEL_NAME = "llama-3.1-8b-instant"          # Fast, reliable
TEMPERATURE = 0.1                             # Low for consistency
MAX_SEARCH_RESULTS = 5
MAX_VERIFICATION_RETRIES = 2
LLM_CALL_DELAY = 0.5                          # Rate limit protection
```

---

## Performance Characteristics

| Metric | Typical Value |
|--------|---------------|
| Total Query Time | 30-90 seconds |
| LLM Calls | 8-15 per query |
| Tool Calls | 10-20 per query |
| Sources Collected | 30-60 per query |
| Report Sections | 5-8 sections |
