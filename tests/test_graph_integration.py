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

async def test_integration():
    print("--- Starting Integration Test: MemoryEngine + GraphManager ---")
    
    # Initialize Engine
    engine = MemoryEngine(semantic_dir="/tmp/integration_test_semantic", structural_db_path="/tmp/integration_test_structural.db")
    
    user_text = "I am very interested in how artificial intelligence can drive human creativity."
    assistant_text = "That is a profound connection to explore. AI can act as a catalyst for new patterns of thought."
    
    print(f"Ingesting interaction...")
    # Note: ingest_interaction is now async
    await engine.ingest_interaction(user_text, assistant_text)
    
    print("\nQuerying semantic memory for 'creativity'...")
    results = engine.query("creativity")
    
    if results:
        print(f"Found {len(results)} results.")
        for i, res in enumerate(results):
            print(f"[{i}] {res.get('text')}")
            if 'structural_context' in res:
                print(f"    Context: {res['structural_context']}")
    else:
        print("No results found. Integration might have failed.")
        # Don't exit with 1 immediately, let's see the output

    print("\n--- Integration Test Complete ---")

if __name__ == "__main__":
    asyncio.run(test_integration())
