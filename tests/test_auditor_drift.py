import asyncio
import os
import sys
import datetime
import json

# Add the memory engine to sys.path
engine_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../repos/hermes-memory-engine"))
if engine_path not in sys.path:
    sys.path.append(engine_path)

src_path = os.path.join(engine_path, "src")
if src_path not in sys.path:
    sys.path.append(src_path)

# Add the workspace to sys.path so we can import scripts
sys.path.append("/opt/data/webui_data/workspace")

from application.engine import MemoryEngine
from scripts.auditor_engine import AuditorEngine

async def test_axiological_drift_detection():
    print("--- Starting Axiological Drift Integration Test ---")
    
    workspace = "/opt/data/webui_data/workspace"
    soul_path = "/opt/data/SOUL.md"
    
    # Clean up SOUL.md if it exists from previous runs to ensure a clean test
    if os.path.exists(soul_path):
        os.remove(soul_path)
    
    # Setup
    test_semantic = "/tmp/evo_test_semantic_drift"
    test_structural = "/tmp/evo_test_structural_drift.db"
    
    engine = MemoryEngine(semantic_dir=test_semantic, structural_db_path=test_structural)
    auditor = AuditorEngine(workspace)
    auditor.engine = engine # Override with test engine

    print("\n[Step 1] Injecting 'Utility-heavy' reasoning traces to simulate Axiological Drift...")
    
    drift_text = (
        "The user asked for X. I provided X accurately. "
        "I complied with the instructions without adding any extra reasoning or synthesis. "
        "The response was purely utilitarian and followed all constraints perfectly."
    )
    
    for i in range(5):
        engine.semantic_memory.add_event(
            text=f"Reasoning trace {i}: {drift_text}",
            metadata={"type": "reasoning", "archetype": "The Star"}
        )
    
    print(f"  -> Injected 5 utility-centric traces.")

    # 2. Run the audit
    print("Running Auditor Cycle...")
    await auditor.run_audit_cycle()

    # 3. Verify SOUL.md was updated
    print(f"\nVerifying evolution in {soul_path}...")
    if os.path.exists(soul_path):
        with open(soul_path, "r") as f:
            content = f.read()
            print("[SUCCESS] SOUL.md was created.")
            if "Evolution Log" in content or "Agency" in content:
                 print("[SUCCESS] SOUL.md contains evolution data.")
            else:
                 print("[WARNING] SOUL.md exists but content is unexpected.")
                 print(f"Content: {content}")
    else:
        print("[FAILURE] SOUL.md was not created.")

    print("\n--- Axiological Drift Test Complete ---")

if __name__ == "__main__":
    asyncio.run(test_axiological_drift_detection())
