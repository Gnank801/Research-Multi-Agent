"""Test script for DeepResearch Agent."""

import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("DeepResearch Agent - Test Script")
print("=" * 60)

# Test 1: Tool imports
print("\n[1/5] Testing tool imports...")
try:
    from tools import tavily_search, arxiv_search, wikipedia_search, calculator, python_executor
    print("✅ All tools imported successfully")
except Exception as e:
    print(f"❌ Tool import failed: {e}")
    sys.exit(1)

# Test 2: Agent imports
print("\n[2/5] Testing agent imports...")
try:
    from agents import PlannerAgent, ExecutorAgent, VerifierAgent, SynthesizerAgent
    print("✅ All agents imported successfully")
except Exception as e:
    print(f"❌ Agent import failed: {e}")
    sys.exit(1)

# Test 3: Test individual tools
print("\n[3/5] Testing individual tools...")

# Test calculator
calc_result = calculator("sqrt(144) + 10")
if calc_result.get("result") == 22.0:
    print("✅ Calculator: Works correctly")
else:
    print(f"⚠️ Calculator result: {calc_result}")

# Test Wikipedia
wiki_result = wikipedia_search("Python programming language")
if wiki_result and not wiki_result[0].get("error"):
    print(f"✅ Wikipedia: Found '{wiki_result[0].get('title', 'N/A')}'")
else:
    print(f"⚠️ Wikipedia: {wiki_result}")

# Test ArXiv
arxiv_result = arxiv_search("transformer attention mechanism")
if arxiv_result and not arxiv_result[0].get("error"):
    print(f"✅ ArXiv: Found '{arxiv_result[0].get('title', 'N/A')[:50]}...'")
else:
    print(f"⚠️ ArXiv: {arxiv_result}")

# Test Tavily
tavily_result = tavily_search("what is RAG in AI")
if tavily_result and not tavily_result[0].get("error"):
    print(f"✅ Tavily: Search successful")
else:
    print(f"⚠️ Tavily: {tavily_result}")

# Test 4: Test Planner Agent
print("\n[4/5] Testing Planner Agent...")
try:
    planner = PlannerAgent()
    plan_result = planner.plan("Explain how RAG systems work")
    if plan_result.get("success"):
        plan = plan_result["plan"]
        print(f"✅ Planner: Created plan with {len(plan.get('subtasks', []))} subtasks")
        print(f"   Complexity: {plan.get('complexity')}")
        print(f"   Expected sections: {len(plan.get('expected_sections', []))}")
    else:
        print(f"⚠️ Planner failed: {plan_result.get('error')}")
except Exception as e:
    print(f"❌ Planner error: {e}")

# Test 5: Test full workflow (short version)
print("\n[5/5] Testing full workflow...")
try:
    from graph import ResearchWorkflow
    
    def progress_callback(step, message):
        print(f"   [{step}] {message}")
    
    workflow = ResearchWorkflow(callback=progress_callback)
    result = workflow.run("What is vector search?")
    
    if result.get("report"):
        report = result["report"]
        print(f"\n✅ Full workflow completed!")
        print(f"   Report title: {report.get('title', 'N/A')}")
        print(f"   Sections: {len(report.get('sections', []))}")
        print(f"   References: {len(report.get('references', []))}")
    else:
        print(f"⚠️ Workflow completed but no report generated")
        if result.get("errors"):
            for err in result["errors"]:
                print(f"   Error: {err}")
                
except Exception as e:
    print(f"❌ Workflow error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)
