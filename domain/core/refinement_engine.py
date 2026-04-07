from typing import List, Dict, Any
import networkx as nx
from domain.supporting.ledger import StructuralLedger
from domain.core.analyzer import GraphAnalyzer
from domain.core.anomaly_detector import ContextualAnomalyDetector
from domain.core.anomaly_config import MetricType

class RefinementProposal:
    def __init__(self, proposal_type: str, target_id: str, description: str, data: Dict[str, Any]):
        self.proposal_type = proposal_type  # 'PRUNE_EDGE', 'MERGE_COMMUNITY', 'CREATE_CONCEPT'
        self.target_id = target_id
        self.description = description
        self.data = data

class RefinementEngine:
    """
    Analyst component that identifies opportunities to simplify and optimize
    the knowledge graph hierarchy using context-aware anomaly detection.
    """
    def __init__(self,
                 structural_db_path: str,
                 detector: ContextualAnomalyDetector):
        self.ledger = StructuralLedger(structural_db_path)
        self.analyzer = GraphAnalyzer(structural_db_path)
        self.detector = detector

    def analyze_for_refinement(self, context_id: str = "global") -> List[RefinementProposal]:
        """
        Scans the graph for structural bloat or redundancy using context-aware thresholds.
        """
        print(f"[RefinementEngine] Analyzing graph structure for context: {context_id}...")
        self.analyzer.build_graph()
        graph = self.analyzer.graph
        proposals = []

        # 1. Detect Bloat: Overly large communities that need condensation
        communities = self.analyzer.detect_communities()
        for i, community in enumerate(communities):
            # We evaluate community size as a metric
            event = self.detector.evaluate_metric(
                MetricType.COMMUNITY_SIZE, 
                float(len(community)), 
                context_id=context_id
            )
            
            if event:
                # Propose a 'Merge' or 'Condensation' into a concept node
                proposal = RefinementProposal(
                    proposal_type="MERGE_COMMUNITY",
                    target_id=f"community_{i}",
                    description=f"Anomaly detected in community size ({len(community)}). Proposing condensation.",
                    data={"nodes": list(community), "event": event}
                )
                proposals.append(proposal)

        # 2. Detect Redundancy: Low-weight edges
        for u, v, data in graph.edges(data=True):
            weight = data.get('weight', 1.0)
            event = self.detector.evaluate_metric(
                MetricType.EDGE_WEIGHT, 
                weight, 
                context_id=context_id
            )
            
            if event:
                proposal = RefinementProposal(
                    proposal_type="PRUNE_EDGE",
                    target_id=f"{u}->{v}",
                    description=f"Edge weight anomaly detected ({weight}). Potential redundancy.",
                    data={"source": u, "target": v, "event": event}
                )
                proposals.append(proposal)

        # 3. Detect Complexity Wall: High Global Density
        density = nx.density(graph)
        event = self.detector.evaluate_metric(
            MetricType.GRAPH_DENSITY, 
            density, 
            context_id=context_id
        )
        
        if event:
            proposal = RefinementProposal(
                proposal_type="GLOBAL_REBALANCE",
                target_id="graph_root",
                description=f"Global graph density anomaly ({density:.4f}) detected.",
                data={"density": density, "event": event}
            )
            proposals.append(proposal)

        return proposals
