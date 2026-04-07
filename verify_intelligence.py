import os
import sys
import shutil

# Ensure the project root is in the path so we can import the library
root = "/data/workspace/repos/hermes-memory-library"
if root not in sys.path:
    sys.path.insert(0, root)

from domain.core.semantic_memory import SemanticMemory
from domain.core.state_registry import StateRegistry
from domain.core.acl.llm_translator import LLMTranslator
from domain.core.events import InfrastructureErrorEvent, EventSeverity

def run_verification():
    print("🚀 Starting Intelligence Verification...")
    
    # Clean up previous test data to ensure a fresh state
    test_db_dir = "/tmp/hermes_test_semantic"
    if os.path.exists(test_db_dir):
        shutil.rmtree(test_db_dir)
    os.makedirs(test_db_dir, exist_ok=True)

    # 1. Test Semantic Context Isolation
    print("\n--- [1/3] Testing Semantic Context Isolation ---")
    sm = SemanticMemory(persist_directory=test_db_dir)
    
    # Use unique keywords per context to prevent semantic overlap in the search
    marketing_keyword = "marketing_secret_alpha"
    core_keyword = "core_secret_beta"
    
    sm.add_event(f"This is a {marketing_keyword} message.", {"type": "msg"}, context_id="marketing")
    sm.add_event(f"This is a {core_keyword} message.", {"type": "msg"}, context_id="core")
    
    # Query marketing context for its secret
    marketing_results = sm.query_context(marketing_keyword, context_id="marketing")
    # Query core context for the marketing secret (should be empty)
    core_results_searching_marketing = sm.query_context(marketing_keyword, context_id="core")
    # Query core context for its own secret
    core_results_searching_core = sm.query_context(core_keyword, context_id="core")
    
    print(f"Marketing query results count: {len(marketing_results)}")
    print(f"Core query (looking for marketing) results count: {len(core_results_searching_marketing)}")
    print(f"Core query (looking for core) results count: {len(core_results_searching_core)}")
    
    # ASSERTIONS
    success_isolation = (len(marketing_results) > 0 and 
                         len(core_results_searching_marketing) == 0 and 
                         len(core_results_searching_core) > 0)
    
    if success_isolation:
        print("✅ SUCCESS: Context isolation verified.")
    else:
        print("❌ FAILURE: Context isolation failed. Metadata filtering is not working as expected.")
        # Debugging: Print all metadata in the collection
        print("\nDEBUG: Current collection contents:")
        all_results = sm.list_events(limit=10)
        for r in all_results:
            print(f"ID: {r['id']}, Metadata: {r['metadata']}")

    # 2. Test ACL Transformation
    print("\n--- [2/3] Testing ACL Transformation ---")
    translator = LLMTranslator()
    try:
        raise ConnectionError("Connection refused by remote server")
    except Exception as e:
        event = translator.translate_exception(e)
        print(f"Caught Exception: {e}")
        print(f"Translated Event: {event}")
        
        if isinstance(event, InfrastructureErrorEvent) and event.severity == EventSeverity.ERROR:
            print("✅ SUCCESS: ACL transformation verified.")
        else:
            print("❌ FAILURE: ACL transformation failed.")

    # 3. Test State Registry
    print("\n--- [3/3] Testing State Registry ---")
    registry = StateRegistry()
    registry.set_state("active_protocol", "alpha", context_id="research")
    registry.set_state("active_protocol", "omega", context_id="combat")
    
    res_research = registry.get_state("active_protocol", context_id="research")
    res_combat = registry.get_state("active_protocol", context_id="combat")
    
    print(f"Research protocol: {res_research}")
    print(f"Combat protocol: {res_combat}")
    
    if res_research == "alpha" and res_combat == "omega":
        print("✅ SUCCESS: State Registry context isolation verified.")
    else:
        print("❌ FAILURE: State Registry isolation failed.")

if __name__ == "__main__":
    try:
        run_verification()
    except Exception as e:
        print(f"Verification script failed with error: {e}")
        import traceback
        traceback.print_exc()
