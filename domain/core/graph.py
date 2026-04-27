import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Set
from pydantic import BaseModel, Field, ConfigDict

class NodeType(str, Enum):
    CONCEPT = "concept"
    ENTITY = "entity"
    VALUE = "value"
    TENSION = "tension"
    DECISION = "decision"
    ARCHETYPE = "archetype"
    PATTERN = "pattern"

class RelationshipType(str, Enum):
    RELATES_TO = "relates_to"
    CONTRASTS_WITH = "contrasts_with"
    SUPPORTS = "supports"
    DRIVES = "drives"
    PART_OF = "part_of"
    INSTANTIATES = "instantiates"
    RESONATES_WITH = "resonates_with"
    TRIGGERS = "triggers"
    REFINES = "refines"

class GraphNode(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    node_id: str
    node_type: NodeType
    label: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())

class GraphEdge(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    edge_id: str
    source_id: str
    target_id: str
    rel_type: RelationshipType
    weight: float = 1.0
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())

class KnowledgeGraph(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    nodes: Dict[str, GraphNode] = Field(default_factory=dict)
    edges: List[GraphEdge] = Field(default_factory=list)

    def add_node(self, node: GraphNode):
        self.nodes[node.node_id] = node

    def add_edge(self, edge: GraphEdge):
        if edge.source_id in self.nodes and edge.target_id in self.nodes:
            self.edges.append(edge)
        else:
            raise ValueError(f"Both source ({edge.source_id}) and target ({edge.target_id}) nodes must exist.")

    def get_neighbors(self, node_id: str) -> List[str]:
        return [edge.target_id for edge in self.edges if edge.source_id == node_id]

    def get_relationships(self, node_id: str) -> List[Dict[str, Any]]:
        rels = []
        for edge in self.edges:
            if edge.source_id == node_id:
                rels.append({
                    "target": edge.target_id,
                    "type": edge.rel_type,
                    "weight": edge.weight
                })
            elif edge.target_id == node_id:
                rels.append({
                    "target": edge.source_id,
                    "type": edge.rel_type,
                    "weight": edge.weight
                })
        return rels
