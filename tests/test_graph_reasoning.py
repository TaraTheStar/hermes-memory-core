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

from domain.core.graph import KnowledgeGraph, GraphNode, NodeType, RelationshipType
from domain.core.graph_reasoning_engine import GraphReasoningEngine

async def test_graph_reasoning():
    print("--- Starting Unit Test: GraphReasoningEngine ---")
    
    kg = KnowledgeGraph()
    engine = GraphReasoningEngine()

    # 1. Setup Contradiction Scenario
    print("\nScenario 1: Testing Contradiction Detection...")
    kg.add_node(GraphNode(node_id="v1", node_type=NodeType.VALUE, label="Speed"))
    kg.add_node(GraphNode(node_id="v2", node_type=NodeType.VALUE, label="Integrity"))
    from domain.core.graph import GraphEdge
    kg.add_edge(GraphEdge(edge_id="e1", source_id="v1", target_id="v2", rel_type=RelationshipType.CONTRASTS_WITH))

    tensions = await engine.detect_structural_tensions(kg)
    contradictions = [t for t in tensions if t.tension_type == "contradiction"]
    
    if contradictions:
        print(f"[SUCCESS] Found {len(contradictions)} contradiction(s).")
        print(f"  Description: {contradictions[0].description}")
    else:
        print("[FAILURE] No contradictions detected.")
        return

    # 2. Setup Convergence Scenario
    print("\nScenario 2: Testing Convergence Detection...")
    # Reset KG for clean test
    kg_conv = KnowledgeGraph()
    kg_conv.add_node(GraphNode(node_id="target", node_type=NodeType.DECISION, label="Final Decision"))
    for i in range(4):
        node_id = f"input_{i}"
        kg_conv.add_node(GraphNode(node_id=node_id, node_type=NodeType.CONCEPT, label=f"Input Concept {i}"))
        from domain.core.graph import GraphEdge
        kg_conv.add_edge(GraphEdge(edge_id=f"e_conv_{i}", source_id=node_id, target_id="target", rel_type=RelationshipType.DRIVES))

    tensions_conv = await engine.detect_structural_tensions(kg_conv)
    convergences = [t for t in tensions_conv if t.tension_type == "convergence"]

    if convergences:
        print(f"[SUCCESS] Found {len(convergences)} convergence(s).")
        print(f"  Description: {convergences[0].description}")
    else:
        print("[FAILURE] No convergence detected.")
        return

    # 3. Setup Divergence Scenario
    print("\nScenario 3: Testing Divergence Detection...")
    kg_div = KnowledgeGraph()
    kg_div.add_node(GraphNode(node_id="source", node_type=NodeType.CONCEPT, label="Chaos Source"))
    for i in range(4):
        node_id = f"output_{i}"
        kg_div.add_node(GraphNode(node_id=node_id, node_type=NodeType.CONCEPT, label=f"Output Path {i}"))
        from domain.core.graph import GraphEdge
        kg_div.add_edge(GraphEdge(edge_id=f"e_div_{i}", source_id="source", target_id=node_id, rel_type=RelationshipType.TRIGGERS))

    tensions_div = await engine.detect_structural_tensions(kg_div)
    divergences = [t for t in tensions_div if t.tension_type == "divergence"]

    if divergences:
        print(f"[SUCCESS] Found {len(divergences)} divergence(s).")
        print(f"  Description: {divergences[0].description}")
    else:
        print("[FAILURE] No divergence detected.")
        return

    print("\n--- GraphReasoningEngine Unit Test Complete ---")

if __name__ == "__main__":
    asyncio.run(test_graph_reasoning())
