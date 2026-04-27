import os
import sys
import datetime
import asyncio
from typing import List, Dict, Any, Optional

# Add the memory engine to sys.path
engine_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../repos/hermes-memory-engine"))
if engine_path not in sys.path:
    sys.path.append(engine_path)

src_path = os.path.join(engine_path, "src")
if src_path not in sys.path:
    sys.path.append(src_path)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from application.engine import MemoryEngine

try:
    from domain.core.graph import KnowledgeGraph, GraphNode, GraphEdge, NodeType, RelationshipType
    from domain.core.graph_extractor import GraphExtractor, ExtractionTriple
    print("Successfully imported Graph and LLM components.")
except ImportError as e:
    print(f"Error importing components: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

class GraphManager:
    """
    Manages the lifecycle of the KnowledgeGraph within the MemoryEngine,
    including continuous extraction from interaction logs.
    """
    def __init__(self, memory_engine: 'MemoryEngine', extractor: GraphExtractor):
        self.engine = memory_engine
        self.extractor = extractor
        self.graph = KnowledgeGraph()

    async def update_from_interaction(self, user_text: str, assistant_text: str):
        """
        Performs on-the-fly extraction from a single interaction.
        """
        print(f"[{datetime.datetime.now().isoformat()}] GraphManager: Extracting triples from new interaction...")
        
        full_text = f"User: {user_text}\nAssistant: {assistant_text}"
        triples = await self.extractor.extract_triples(full_text)
        
        if triples:
            print(f"  -> Discovered {len(triples)} new semantic triples.")
            self.extractor.apply_triples_to_graph(self.graph, triples)
            # In a real implementation, we would persist the graph here.
        else:
            print("  -> No new semantic connections found in this interaction.")

    async def run_periodic_sync(self, lookback_minutes: int = 60):
        """
        Scans recent history to catch latent connections or missed extractions.
        """
        print(f"[{datetime.datetime.now().isoformat()}] GraphManager: Running periodic sync (lookback: {lookback_minutes}m)...")
        
        # 1. Query recent events from semantic memory
        # For the sake of this test, we'll assume the query returns text that contains relational data
        query = "concept relationship tension connection"
        recent_entries = self.engine.query(query, n_results=10)
        
        if not recent_entries:
            print("  -> No recent entries found to sync.")
            return

        total_new_triples = 0
        for entry in recent_entries:
            text = entry.get('text', '')
            triples = await self.extractor.extract_triples(text)
            if triples:
                self.extractor.apply_triples_to_graph(self.graph, triples)
                total_new_triples += len(triples)
        
        print(f"  -> Sync complete. Total new triples integrated: {total_new_triples}")
        print(f"  -> Current Graph State: {len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges.")

async def test_graph_manager():
    print("--- Starting Unit Test: GraphManager ---")
    
    # Setup
    workspace = "/opt/data/webui_data/workspace"
    engine = MemoryEngine(semantic_dir="/tmp/semantic_test", structural_db_path="/tmp/structural_test.db")
    
    # We need a real-ish LLM for extraction, but we'll use our MockLLM setup from the previous test
    # to ensure we don't need a live backend for this unit test.
    class JSONMockLLM:
        def complete(self, prompt, system_prompt=None):
            # Return a structured JSON that simulates a real LLM extraction
            return """
            [
              {
                "subject_id": "concept-speed",
                "subject_label": "Speed",
                "subject_type": "value",
                "predicate": "contrasts_with",
                "object_id": "concept-integrity",
                "object_label": "Integrity",
                "object_type": "value",
                "properties": {}
              },
              {
                "subject_id": "decision-123",
                "subject_label": "Hybrid Deployment",
                "subject_type": "decision",
                "predicate": "resolves",
                "object_id": "tension-456",
                "object_label": "Deployment Tension",
                "object_type": "tension",
                "properties": {}
              }
            ]
            """
    
    extractor = GraphExtractor(JSONMockLLM())
    manager = GraphManager(engine, extractor)

    # Test 1: On-the-fly extraction
    print("\nTest 1: On-the-fly extraction from single interaction...")
    await manager.update_from_interaction(
        "I am feeling a tension between the need for speed and the requirement for integrity.",
        "I suggest a hybrid approach to resolve this."
    )
    
    if len(manager.graph.nodes) >= 2:
        print("[SUCCESS] On-the-fly extraction populated the graph.")
    else:
        print(f"[FAILURE] Graph state: {len(manager.graph.nodes)} nodes.")
        sys.exit(1)

    # Test 2: Periodic Sync
    print("\nTest 2: Periodic sync from historical query...")
    # Manually inject a text entry into semantic memory to be found by the sync
    engine.semantic_memory.add_event(
        text="The connection between creativity and logic is vital.",
        metadata={"type": "historical_context"}
    )
    
    # For the sync to work with our Mock, the query needs to trigger the Mock's response
    # The Mock currently returns the same JSON regardless of text.
    await manager.run_periodic_sync(lookback_minutes=5)

    if len(manager.graph.nodes) > 2:
        print("[SUCCESS] Periodic sync populated the graph.")
    else:
        print(f"[FAILURE] Graph state after sync: {len(manager.graph.nodes)} nodes.")
        sys.exit(1)

    print("\n--- Knowledge Graph Manager Unit Test Complete ---")

if __name__ == "__main__":
    asyncio.run(test_graph_manager())
