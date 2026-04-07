
import os
import sys
import shutil

root = "/data/workspace/repos/hermes-memory-library"
if root not in sys.path:
    sys.path.insert(0, root)

from domain.core.semantic_memory import SemanticMemory
from domain.core.state_registry import StateRegistry
from domain.core.acl.llm_translator import LLMTranslator
from domain.core.events import InfrastructureErrorEvent, EventSeverity

def run_verification():
    print("🚀 Starting VERBOSE Intelligence Verification...")
    
    test_db_dir = "/tmp/hermes_test_semantic_v2"
    if os.path.exists(test_db_dir):
        shutil.rmtree(test_db_dir)
    os.makedirs(test_db_dir, exist_ok=True)

    sm = SemanticMemory(persist_directory=test_db_dir)
    
    # Add events with explicit context
    print("\n[Setup] Adding events...")
    sm.add_event("marketing_secret_alpha", {"type": "msg"}, context_id="marketing")
    sm.add_event("core_secret_beta", {"type": "msg"}, context_id="core")
    
    print("[Setup] Done.")

    # Test 1: Marketing Query
    print("\n--- [1/1] Testing Semantic Context Isolation ---")
    print("Targeting context: 'marketing' with query: 'marketing_secret_alpha'")
    m_results = sm.query_context("marketing_secret_alpha", context_id="marketing")
    print(f"Results found: {len(m_results)}")
    for r in m_results:
        print(f"  - ID: {r['id']}, Metadata: {r['metadata']}")

    # Test 2: The "Leak" Test (The one that failed)
    print("\nTargeting context: 'core' with query: 'marketing_secret_alpha'")
    c_results = sm.query_context("marketing_secret_alpha", context_id="core")
    print(f"Results found: {len(c_results)}")
    for r in c_results:
        print(f"  - ID: {r['id']}, Metadata: {r['metadata']}")

    if len(c_results) == 0:
        print("\n✅ SUCCESS: No leakage detected.")
    else:
        print("\n❌ FAILURE: Leakage detected!")
        for r in c_results:
            print(f"  LEAKED EVENT: {r['id']} with context {r['metadata'].get('context_id')}")

if __name__ == "__main__":
    run_verification()
