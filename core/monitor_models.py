import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy import Column, String, Float, DateTime, JSON, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.models import Base

# New Base for Monitoring models to keep them logically separated if needed, 
# but we can also just use the main Base for simplicity in this prototype.
MonitoringBase = declarative_base()

class GraphSnapshot(MonitoringBase):
    """
    Stores a point-in-time 'fingerprint' of the knowledge graph's structure.
    """
    __tablename__ = 'graph_snapshots'

    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    
    # Global Metrics
    density = Column(Float)
    community_count = Column(Integer)
    
    # Node-level Metrics (Stored as JSON for flexibility)
    # Format: { "node_id": {"degree": 0.5, "betweenness": 0.1, ...}, ... }
    centrality_metrics = Column(JSON)
    
    # Metadata
    metadata_tags = Column(JSON)

class AnomalyEvent(MonitoringBase):
    """
    Records detected structural anomalies for auditing and trigger history.
    """
    __tablename__ = 'anomaly_events'

    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    anomaly_type = Column(String, nullable=False)  # e.g., 'HUB_EMERGENCE', 'COMMUNITY_SPLIT'
    description = Column(String, nullable=False)
    severity = Column(String, default='medium')   # 'low', 'medium', 'high', 'critical'
    
    # The raw data that triggered the anomaly for debugging/audit
    trigger_data = Column(JSON)

from sqlalchemy import Integer

# Re-importing to ensure everything is correctly linked to the same registry if using one Base
# For this prototype, we will use the primary Base from core.models
