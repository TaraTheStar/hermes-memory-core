import asyncio
import os
import sys
import datetime

# Add the memory engine to sys.path
engine_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../repos/hermes-memory-engine"))
if engine_path not in sys.path:
    sys.path.append(engine_path)

src_path = os.path.join(engine_path, "src")
if src_path not in sys.path:
    sys.path.append(src_path)

from application.engine import MemoryEngine
from application.proactive_agent import ProactiveAgent
from domain.core.graph import KnowledgeGraph, GraphNode, GraphEdge, NodeType, RelationshipType

async def test_structural_evolution():
    print("--- Starting Structural Evolution Integration Test ---")
    
    workspace = "/opt/data/webui_data/workspace"
    soul_path = os.path.join(workspace, "SOUL.md")
    
    # Clean up
    if os.path.exists(soul_path):
        os.remove(soul_path)
    
    # Setup
    test_semantic = "/tmp/evo_test_semantic"
    test_structural = "/tmp/evo_test_structural.db"
    
    engine = MemoryEngine(semantic_dir=test_semantic, structural_db_path=test_structural)
    agent = ProactiveAgent(workspace)
    agent.engine = engine 

    print("\n[Step 1] Injecting a Structural Contradiction into the KnowledgeGraph...")
    
    kg = engine.graph_manager.graph
    
    # Create two nodes
    node_a_id = "node_stability"
    node_b_id = "node_expansion"
    
    kg.add_node(GraphNode(node_id=node_a_id, node_type=NodeType.CONCEPT, label="Stability"))
    kg.add_node(GraphNode(node_id=node_b_id, node_type=NodeType.CONCEPT, label="Expansion"))
    
    # Create the contradiction edge
    kg.add_edge(GraphEdge(
        edge_id="edge_contradict_1",
        source_id=node_a_id,
        target_id=node_b_id,
        rel_type=RelationshipType.CONTRASTS_WITH
    ))
    
    print(f"  -> Injected contradiction: {node_a_id} <-> {node_b_id}")

    # 2. Run the scan
    print("Running Proactive Scan...")
    await agent.scan_for_tensions()

    # 3. Verify SOUL.md was updated
    print(f"\nVerifying evolution in {soul_path}...")
    if os.path.exists(soul_path):
        with open(soul_path, "r") as f:
            content = f.read()
            print("[SUCCESS] SOUL.md was created.")
            # Check for existence of evolution-related terms
            if "Evolution Log" in content or "Adopted" in content or "paradigm" in content:
                 print("[SUCCESS] SOUL.md contains evolution data.")
            else:
                 print("[WARNING] SOUL.md exists but content is unexpected.")
    else:
        print("[FAILURE] SOUL.md was not created.")

    print("\n--- Structural Evolution Test Complete ---")

if __name__ == "__main__":
    asyncio.run(test_structural_evolution())
