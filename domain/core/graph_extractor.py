import os
import sys
import json
import re
import asyncio
from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field

# Add the memory engine to sys.path
engine_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../repos/hermes-memory-engine"))
if engine_path not in sys.path:
    sys.path.append(engine_path)

src_path = os.path.join(engine_path, "src")
if src_path not in sys.path:
    sys.path.append(src_path)

try:
    from domain.core.graph import KnowledgeGraph, GraphNode, GraphEdge, NodeType, RelationshipType
    from domain.core.decision_engine import Archetype
    from infrastructure.llm_implementations import BaseLLMInterface
    print("Successfully imported Graph and LLM components.")
except ImportError as e:
    print(f"Error importing components: {e}")
    sys.exit(1)

class ExtractionTriple(BaseModel):
    subject_id: str
    subject_label: str
    subject_type: NodeType
    predicate: RelationshipType
    object_id: str
    object_label: str
    object_type: NodeType
    properties: Dict[str, Any] = Field(default_factory=dict)

class GraphExtractor:
    """
    Analyzes text to extract semantic relationships and populate a KnowledgeGraph.
    """
    def __init__(self, llm: BaseLLMInterface):
        self.llm = llm
        self.extraction_prompt = """
        You are a semantic analyst. Your task is to extract structured knowledge triples from the provided text.
        Each triple consists of a Subject, a Predicate (Relationship), and an Object.

        EXTRACTION RULES:
        1. Identify key Concepts, Entities, Values, Tensions, Decisions, or Archetypes.
        2. Define the relationship between them using one of these types:
           - relates_to (general connection)
           - contrasts_with (opposing values/concepts)
           - supports (one concept reinforcing another)
           - drives (one concept causing or motivating another)
           - part_of (composition/hierarchy)
           - instantiates (a specific instance of a concept/archetype)
           - resonates_with (thematic similarity)
           - triggers (causal link)
           - refines (improving or clarifying a concept)
        3. Output ONLY a valid JSON list of objects in this format:
        [
          {{
            "subject_id": "unique-id-1",
            "subject_label": "Label",
            "subject_type": "concept|entity|value|tension|decision|archetype|pattern",
            "predicate": "relates_to|contrasts_with|supports|drives|part_of|instantiates|resonates_with|triggers|refines",
            "object_id": "unique-id-2",
            "object_label": "Label",
            "object_type": "concept|entity|value|tension|decision|archetype|pattern",
            "properties": {{"key": "value"}}
          }}
        ]

        TEXT TO ANALYZE:
        {text}
        """

    async def extract_triples(self, text: str) -> List[ExtractionTriple]:
        if not text.strip():
            return []

        prompt = self.extraction_prompt.format(text=text)
        
        try:
            # Using asyncio.to_thread because the LLM call is synchronous in the interface
            response_text = await asyncio.to_thread(self.llm.complete, prompt, "You are a precise semantic extractor.")
            
            # Clean up potential markdown formatting
            json_match = re.search(r'(\[.*\])', response_text, re.DOTALL)
            if not json_match:
                return []
            
            json_str = json_match.group(1)
            data = json.loads(json_str)
            
            triples = []
            for item in data:
                # Map common LLM synonyms to our strict RelationshipType enum
                pred = item.get("predicate")
                mapping = {
                    "resolves": "relates_to",
                    "addresses": "relates_to",
                    "mitigates": "relates_to",
                    "leads_to": "triggers",
                    "causes": "triggers",
                    "strengthens": "supports"
                }
                if pred in mapping:
                    item["predicate"] = mapping[pred]
                
                triples.append(ExtractionTriple(**item))
            return triples
        except Exception as e:
            print(f"Extraction error: {e}")
            return []

    def apply_triples_to_graph(self, kg: KnowledgeGraph, triples: List[ExtractionTriple]):
        for t in triples:
            # 1. Ensure Subject exists
            if t.subject_id not in kg.nodes:
                kg.add_node(GraphNode(
                    node_id=t.subject_id,
                    node_type=t.subject_type,
                    label=t.subject_label,
                    properties=t.properties
                ))
            
            # 2. Ensure Object exists
            if t.object_id not in kg.nodes:
                kg.add_node(GraphNode(
                    node_id=t.object_id,
                    node_type=t.object_type,
                    label=t.object_label,
                    properties=t.properties
                ))
            
            # 3. Add the Edge
            # Check for duplicate edges to avoid bloat
            exists = any(
                edge.source_id == t.subject_id and 
                edge.target_id == t.object_id and 
                edge.rel_type == t.predicate 
                for edge in kg.edges
            )
            
            if not exists:
                kg.add_edge(GraphEdge(
                    edge_id=f"edge-{t.subject_id}-{t.object_id}-{t.predicate}",
                    source_id=t.subject_id,
                    target_id=t.object_id,
                    rel_type=t.predicate
                ))
