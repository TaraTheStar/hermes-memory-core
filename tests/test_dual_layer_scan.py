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

class MockLLM:
    def complete(self, prompt, system_prompt=None):
        return "[]"

async def test_dual_layer_scan():
    print("--- Starting Integration Test: ProactiveAgent Dual-Layer Scan ---")
    
    # Setup
    engine = MemoryEngine(semantic_dir="/tmp/dual_test_semantic", structural_db_path="/tmp/dual_test_structural.db")
    workspace = "/opt/data/webui_data/workspace"
    
    from application.proactive_agent import ProactiveAgent
    agent = ProactiveAgent(workspace)
    # Re-link agent to our test engine
    agent.engine = engine

    # 1. Inject Linguistic Tension
    print("\nInjecting Linguistic Tension into semantic memory...")
    engine.semantic_memory.add_event(
        text="I feel a massive tension between the need for Speed and the requirement for Integrity.",
        metadata={"type": "preference"}
    )

    # 2. Inject Structural Tension (Contradiction)
    print("Injecting Structural Contradiction into KnowledgeGraph...")
    from domain.core.graph import GraphNode, GraphEdge, NodeType, RelationshipType
    
    kg = engine.graph_manager.graph
    kg.add_node(GraphNode(node_id="v1", node_type=NodeType.VALUE, label="Freedom"))
    kg.add_node(GraphNode(node_id="v2", node_type=NodeType.VALUE, label="Security"))
    kg.add_edge(GraphEdge(edge_id="e_struct", source_id="v1", target_id="v2", rel_type=RelationshipType.CONTRASTS_WITH))

    # Run the scan
    await agent.scan_for_tensions()

    print("\n--- Dual-Layer Scan Test Complete ---")

if __name__ == "__main__":
    asyncio.run(test_dual_layer_scan())
