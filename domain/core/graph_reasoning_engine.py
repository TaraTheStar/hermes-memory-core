import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from domain.core.graph import KnowledgeGraph, NodeType, RelationshipType

class StructuralTension(BaseModel):
    """
    Represents a tension or conflict discovered through structural graph analysis.
    """
    tension_type: str  # e.g., "contradiction", "divergence", "convergence", "instability"
    description: str
    involved_node_ids: List[str]
    severity: float = Field(ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class GraphReasoningEngine:
    """
    Analyzes the structural topology of a KnowledgeGraph to detect 
    latent tensions, patterns, and complexities that keyword-based 
    extraction might miss.
    """

    def __init__(self):
        pass

    async def detect_structural_tensions(self, kg: KnowledgeGraph) -> List[StructuralTension]:
        """
        Traverses the graph to find topological patterns indicating tension.
        """
        tensions = []
        
        # 1. Detect Direct Contradictions
        tensions.extend(self._detect_contradictions(kg))
        
        # 2. Detect Convergence/Divergence (Potential Bottlenecks or Chaotic Divergence)
        tensions.extend(self._detect_convergence_divergence(kg))
        
        return tensions

    def _detect_contradictions(self, kg: KnowledgeGraph) -> List[StructuralTension]:
        """
        Finds nodes connected by 'contrasts_with' edges.
        """
        found = []
        for edge in kg.edges:
            if edge.rel_type == RelationshipType.CONTRASTS_WITH:
                # We treat a contrast edge as a tension point
                node_a = kg.nodes.get(edge.source_id)
                node_b = kg.nodes.get(edge.target_id)
                
                if node_a and node_b:
                    found.append(StructuralTension(
                        tension_type="contradiction",
                        description=f"Direct contradiction detected between '{node_a.label}' and '{node_b.label}'.",
                        involved_node_ids=[edge.source_id, edge.target_id],
                        severity=0.7,
                        metadata={
                            "source_label": node_a.label,
                            "target_label": node_b.label,
                            "edge_id": edge.edge_id
                        }
                    ))
        return found

    def _detect_convergence_divergence(self, kg: KnowledgeGraph) -> List[StructuralTension]:
        """
        Analyzes in-degree and out-degree to find structural bottlenecks or chaotic expansions.
        """
        found = []
        in_degree: Dict[str, int] = {}
        out_degree: Dict[str, int] = {}

        for edge in kg.edges:
            in_degree[edge.target_id] = in_degree.get(edge.target_id, 0) + 1
            out_degree[edge.source_id] = out_degree.get(edge.source_id, 0) + 1

        # Convergence: Many things driving into one node (potential bottleneck/decision point)
        for node_id, count in in_degree.items():
            if count >= 3:
                node = kg.nodes.get(node_id)
                if node:
                    found.append(StructuralTension(
                        tension_type="convergence",
                        description=f"High convergence detected at '{node.label}'. {count} entities are driving towards this single point.",
                        involved_node_ids=[node_id],
                        severity=0.5,
                        metadata={"in_degree": count}
                    ))

        # Divergence: One node driving many things (potential source of chaos/instability)
        for node_id, count in out_degree.items():
            if count >= 3:
                node = kg.nodes.get(node_id)
                if node:
                    found.append(StructuralTension(
                        tension_type="divergence",
                        description=f"High divergence detected from '{node.label}'. This entity is triggering {count} distinct paths.",
                        involved_node_ids=[node_id],
                        severity=0.4,
                        metadata={"out_degree": count}
                    ))

        return found
