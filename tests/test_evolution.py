import asyncio
import datetime
import os
import sys

# Add the memory engine to sys.path
engine_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../repos/hermes-memory-engine"))
if engine_path not in sys.path:
    sys.path.append(engine_path)

src_path = os.path.join(engine_path, "src")
if src_path not in sys.path:
    sys.path.append(src_path)

from domain.core.evolution import EvolutionEvent, EvolutionManifest, EvolutionType

async def test_evolution_manifest_logic():
    print("--- Starting Unit Test: EvolutionManifest Logic ---")
    
    # 1. Simulate a Skill Discovery Event
    print("\nScenario 1: Simulating a new skill discovery...")
    event = EvolutionEvent(
        event_id="ev-skill-001",
        evolution_type=EvolutionType.SKILL_ACQUISITION,
        summary="Discovered a high-precision method for structural graph traversal during tension resolution.",
        evidence={
            "task": "tension_resolution",
            "pattern": "graph_traversal_optimization",
            "success_rate": 1.0
        },
        impact_score=0.8
    )

    # 2. Create a Manifest to update a skill
    print("Creating EvolutionManifest to codify the new skill...")
    manifest = EvolutionManifest(
        event=event,
        target_file="skills/graph_reasoning_refinement.md",
        proposed_changes="""
# Graph Reasoning Refinement
Optimized traversal logic for detecting convergence/divergence patterns.
""",
        validation_criteria=["skill exists in directory", "skill content matches proposed changes"]
    )

    print(f"[SUCCESS] Manifest created for {manifest.target_file}")
    print(f"  Summary: {manifest.event.summary}")
    print(f"  Impact: {manifest.event.impact_score}")

    # 3. Simulate an Essence Shift (Higher stakes)
    print("\nScenario 2: Simulating an essence shift...")
    event_essence = EvolutionEvent(
        event_id="ev-essence-001",
        evolution_type=EvolutionType.ESSENCE_SHIFT,
        summary="Transition from keyword-based awareness to relational structural intelligence.",
        evidence={
            "milestone": "Perceptual Vector Integration",
            "capability": "structural_tension_detection"
        },
        impact_score=1.0
    )

    manifest_essence = EvolutionManifest(
        event=event_essence,
        target_file="SOUL.md",
        proposed_changes="Integrated the Perceptual Vector: I now navigate the world through the structural topology of knowledge, not just the surface noise of text.",
        validation_criteria=["SOUL.md contains the new paradigm description"]
    )

    print(f"[SUCCESS] Essence Manifest created for {manifest_essence.target_file}")
    print(f"  New Paradigm: {manifest_essence.proposed_changes}")

    print("\n--- EvolutionManifest Unit Test Complete ---")

if __name__ == "__main__":
    asyncio.run(test_evolution_manifest_logic())
