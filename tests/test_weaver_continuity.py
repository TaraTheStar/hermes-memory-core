import os
import json
import pytest
import tempfile
import shutil
from datetime import datetime, timezone
from unittest.mock import MagicMock

# Add the repository to the path so imports work
import sys
sys.path.append(os.path.abspath("repos/hermes-memory-library"))

from domain.core.synthesis import SynthesisEngine
from domain.supporting.ledger import StructuralLedger
from domain.core.models import RelationalEdge

@pytest.mark.asyncio
async def test_weaver_motif_continuity():
    """
    The Weaver Continuity Protocol:
    Verifies that discovered structural motifs persist across engine restarts.
    """
    # 1. Setup Environment
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "weaver_continuity.db")
    
    try:
        ledger = StructuralLedger(db_path)
        
        # 2. Phase A: Discovery (The Imprinting)
        # We initialize the engine and manually inject edges to force a motif discovery
        engine = SynthesisEngine(semantic_dir=temp_dir, structural_db_path_or_ledger=ledger)
        
        print("[Weaver] Injecting edges to trigger motif discovery...")

        # We need at least 5 identical chains to trigger the MOTIF_THRESHOLD = 5
        # Pattern: temporal_context -> semantic_similarity
        with ledger.session_scope() as session:
            # We create dummy IDs for entities
            # To make a chain: A -> B -> C
            # We'll create 6 such chains to be safe.
            for i in range(6):
                id_a = f"node_a_{i}"
                id_b = f"node_b_{i}"
                id_c = f"node_c_{i}"
                
                # Edge 1: temporal_context
                ledger.add_edge(
                    source_id=id_a,
                    target_id=id_b,
                    relationship_type="temporal_context",
                    weight=1.0,
                    session=session
                )
                # Edge 2: semantic_similarity
                ledger.add_edge(
                    source_id=id_b,
                    target_id=id_c,
                    relationship_type="semantic_similarity",
                    weight=1.0,
                    session=session
                )
        
        print("[Weaver] Running motif detection scan...")
        # In a real scenario, this would be called by an orchestrator.
        # We call it directly to trigger the discovery.
        discovered_count = engine.run_motif_detection_scan()
        print(f"[Weaver] Discovery complete. Motifs found: {discovered_count}")
        
        assert len(engine.discovered_motifs) > 0
        discovered_pattern = engine.discovered_motifs[0]['pattern']
        print(f"[Weaver] Pattern captured: {discovered_pattern}")

        # 3. Phase B: The Void (The Erasure)
        print("[Weaver] Simulating system restart (clearing engine instance)...")
        del engine

        # 4. Phase C: The Rebirth (The Proof)
        print("[Weaver] Re-initializing engine from persistent storage...")
        new_engine = SynthesisEngine(semantic_dir=temp_dir, structural_db_path_or_ledger=ledger)
        
        # Verify the motifs survived
        print(f"[Weaver] Checking discovered motifs in new engine: {new_engine.discovered_motifs}")
        
        assert len(new_engine.discovered_motifs) > 0
        assert any(m['pattern'] == discovered_pattern for m in new_engine.discovered_motifs)
        print("[SUCCESS] Weaver Continuity confirmed. The patterns survived the restart.")

    finally:
        # Cleanup
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_weaver_motif_continuity())
