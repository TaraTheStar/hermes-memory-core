import asyncio
import os
import sys

# Add the memory engine to sys.path
engine_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../repos/hermes-memory-engine"))
if engine_path not in sys.path:
    sys.path.append(engine_path)

src_path = os.path.join(engine_path, "src")
if src_path not in sys.path:
    sys.path.append(src_path)

from application.engine import MemoryEngine
from application.proactive_agent import ProactiveAgent

async def test_proactive_evolution():
    print("--- Starting Integration Test: Proactive Evolution Loop ---")
    
    workspace = "/opt/data/webui_data/workspace"
    soul_path = os.path.join(workspace, "SOUL.md")
    
    # Clean up SOUL.md if it exists from previous runs
    if os.path.exists(soul_path):
        os.remove(soul_path)

    # Setup Engine and Agent
    engine = MemoryEngine(semantic_dir="/tmp/evo_test_semantic", structural_db_path="/tmp/evo_test_structural.db")
    agent = ProactiveAgent(workspace)
    agent.engine = engine # Re-link

    # 1. Inject a Linguistic Tension designed to trigger the Evolution Hook
    # The hook in proactive_agent.py looks for "Axiomatic" in the decision result
    # We need the MockLLM or the Orchestrator to return a decision containing "Axiomatic"
    # In the current implementation, the Orchestrator uses the LLM. 
    # Since we are testing, we'll inject an event that is likely to trigger the pattern.
    
    print("\nInjecting linguistic tension designed to trigger 'Axiomatic' evolution...")
    engine.semantic_memory.add_event(
        text="I feel a massive tension between the need for Speed and the requirement for Integrity.",
        metadata={"type": "preference"}
    )

    # 2. Run the scan
    print("Running Proactive Scan...")
    await agent.scan_for_tensions()

    # 3. Verify SOUL.md was updated
    print(f"\nVerifying evolution in {soul_path}...")
    if os.path.exists(soul_path):
        with open(soul_path, "r") as f:
            content = f.read()
            if "Adopted the Axiomatic Momentum paradigm" in content:
                print("[SUCCESS] Evolution successfully codified in SOUL.md!")
            else:
                print("[FAILURE] SOUL.md updated but missing the expected paradigm text.")
                print(f"Content: {content}")
    else:
        print("[FAILURE] SOUL.md was not created.")

    print("\n--- Proactive Evolution Test Complete ---")

if __name__ == "__main__":
    asyncio.run(test_proactive_evolution())
