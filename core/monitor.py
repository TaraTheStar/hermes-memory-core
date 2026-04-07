import datetime
import uuid
from typing import Dict, List, Any, Optional, Set
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.models import Base
from core.analyzer import GraphAnalyzer
from core.monitor_models import GraphSnapshot, AnomalyEvent

class StateTracker:
    """
    Responsible for periodic snapshotting of the graph's structural state.
    """
    def __init__(self, structural_db_path: str):
        self.engine = create_engine(f"sqlite:///{structural_db_path}")
        # Ensure the monitoring tables are created
        from core.monitor_models import Base as MonitorBase
        MonitorBase.metadata.create_all(self.engine)
        
        self.Session = sessionmaker(bind=self.engine)
        self.analyzer = GraphAnalyzer(structural_db_path)

    def capture_snapshot(self) -> GraphSnapshot:
        """
        Analyzes the current graph and saves a snapshot to the database.
        """
        print("[StateTracker] Capturing graph snapshot...")
        self.analyzer.build_graph()
        
        metrics = self.analyzer.get_centrality_metrics()
        communities = self.analyzer.detect_communities()
        
        # Calculate density: edges / (nodes * (nodes - 1))
        nodes_count = len(self.analyzer.graph.nodes)
        edges_count = len(self.analyzer.graph.edges)
        density = 0.0
        if nodes_count > 1:
            density = (2 * edges_count) / (nodes_count * (nodes_count - 1))

        snapshot = GraphSnapshot(
            id=str(uuid.uuid4()),
            timestamp=datetime.datetime.utcnow(),
            density=density,
            community_count=len(communities),
            centrality_metrics=metrics,
            metadata_tags={"node_count": nodes_count, "edge_count": edges_count}
        )

        session = self.Session()
        try:
            session.add(snapshot)
            session.commit()
            print(f"[StateTracker] Snapshot saved: {snapshot.id} (Nodes: {nodes_count}, Communities: {len(communities)})")
            return snapshot
        except Exception as e:
            session.rollback()
            print(f"[StateTracker] Error saving snapshot: {e}")
            raise
        finally:
            session.close()

class AnomalyDetector:
    """
    Compares the current snapshot against historical data to find significant patterns.
    """
    def __init__(self, structural_db_path: str, sensitivity: float = 2.0):
        self.engine = create_engine(f"sqlite:///{structural_db_path}")
        self.Session = sessionmaker(bind=self.engine)
        self.sensitivity = sensitivity  # Sigma threshold for anomaly detection

    def detect_anomalies(self, current_snapshot: GraphSnapshot) -> List[AnomalyEvent]:
        """
        Scans historical snapshots to find statistical deviations.
        """
        print("[AnomalyDetector] Scanning for structural anomalies...")
        anomalies = []
        session = self.Session()
        
        try:
            # 1. Get historical snapshots (excluding the current one)
            history = session.query(GraphSnapshot).filter(
                GraphSnapshot.timestamp < current_snapshot.timestamp
            ).order_by(GraphSnapshot.timestamp.desc()).all()

            if len(history) < 3:
                print("[AnomalyDetector] Insufficient history for statistical analysis. Skipping.")
                return []

            # --- HEURISTIC 1: Hub Emergence (Centrality Spike) ---
            # We look for nodes whose degree centrality has spiked significantly
            for node_id, node_metrics in current_snapshot.centrality_metrics.items():
                current_degree = node_metrics.get('degree', 0.0)
                
                # Calculate mean and std of degree centrality for this node across history
                historical_degrees = []
                for snap in history:
                    hist_metrics = snap.centrality_metrics.get(node_id, {})
                    if hist_metrics:
                        historical_degrees.append(hist_metrics.get('degree', 0.0))
                
                if len(historical_degrees) >= 3:
                    import statistics
                    mean_deg = statistics.mean(historical_degrees)
                    stdev_deg = statistics.stdev(historical_degrees) if len(historical_degrees) > 1 else 0.0
                    
                    # If current degree is > mean + (sensitivity * stdev)
                    if current_degree > (mean_deg + (self.sensitivity * stdev_deg)) and current_degree > 0.1:
                        event = AnomalyEvent(
                            id=str(uuid.uuid4()),
                            anomaly_type="HUB_EMERGENCE",
                            description=f"Node '{node_id}' has emerged as a significant hub. (Degree: {current_degree:.2f}, Hist Mean: {mean_deg:.2f})",
                            severity="medium",
                            trigger_data={"node_id": node_id, "new_degree": current_degree, "mean_degree": mean_deg}
                        )
                        anomalies.append(event)

            # --- HEURISTIC 2: Community Shifts (Community Count) ---
            # A sudden change in the number of communities
            historical_counts = [s.community_count for s in history]
            mean_comm = sum(historical_counts) / len(historical_counts)
            
            if abs(current_snapshot.community_count - mean_comm) > 2: # Threshold of 2 communities
                anomalies.append(AnomalyEvent(
                    id=str(uuid.uuid4()),
                    anomaly_type="COMMUNITY_SHIFT",
                    description=f"Significant shift in graph structure: Community count changed from ~{mean_comm:.1f} to {current_snapshot.community_count}.",
                    severity="medium",
                    trigger_data={"old_count": mean_comm, "new_count": current_snapshot.community_count}
                ))

            # Save detected anomalies
            if anomalies:
                for anomaly in anomalies:
                    session.add(anomaly)
                session.commit()
                print(f"[AnomalyDetector] Detected {len(anomalies)} anomalies.")
            else:
                print("[AnomalyDetector] No significant anomalies detected.")

            return anomalies

        except Exception as e:
            print(f"[AnomalyDetector] Error during detection: {e}")
            raise
        finally:
            session.close()
