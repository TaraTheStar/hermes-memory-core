# Phase 4.1: Graph Insights Service - Technical Specification

## 1. Objective
To transition the Hermes Memory Engine from a "discovery" system to an "understanding" system. The Graph Insights Service will interpret the relationships found by the Synthesis Engine and extract meaningful patterns about the user's identity, skills, and progress.

## 2. Core Components

### A. The Graph Analyzer (Mathematical Layer)
This component interfaces directly with the `RelationalEdge` data in the `StructuralLedger` and converts it into a `NetworkX` graph object for analysis.

**Key Metrics to Calculate:**
- **Degree Centrality**: Identifies the most "connected" entities (e.g., which skill is mentioned in the most milestones).
- **Betweenness Centrality**: Identifies "bridge" entities that connect different thematic clusters (e.g., a specific project that connects two seemingly unrelated skill sets).
- **Clustering Coefficient**: Measures how tightly knit certain groups of knowledge are.
- **Eigenvector Centrality**: Identifies entities connected to *other* highly connected entities (finding the "power nodes").

### B. The Insight Synthesizer (Narrative Layer)
This component acts as the "translator." It takes the raw numerical outputs from the Graph Analyzer and feeds them into a structured prompt for an LLM.

**Input Data:**
- Top $N$ nodes by Centrality.
- Detected "Communities" (clusters) from the graph.
- Bridge nodes identified by betweenness.

**Output Format:**
A structured "Insight Report" containing:
- **The Core Pillars**: The most foundational elements of the current memory state.
- **The Connective Tissue**: How different domains are currently interlocking.
- **Emerging Symmetries**: New patterns observed in the recent synthesis scans.
- **Growth Vectors**: Areas where connections are accelerating.

## 3. Implementation Plan

### Step 1: The `GraphAnalyzer` Class
- Method: `get_networkx_graph()` -> Returns a loaded `networkx.Graph`.
- Method: `calculate_centralities()` -> Returns a dictionary of node IDs and their scores.
- Method: `detect_communities()` -> Returns groups of related node IDs.

### Step 2: The `InsightSynthesizer` Class
- Method: `generate_report(metrics: dict, communities: list)` -> Uses an LLM (via a provided interface) to create the narrative report.

### Step 3: The `StateOfSoul` Orchestrator
- A high-level method that runs the analyzer, then the synthesizer, and returns the final report.

## 4. Success Criteria
- **Accuracy**: The mathematical metrics must correctly reflect the underlying graph structure.
- **Narrative Value**: The generated report must feel "alive" and provide actual insight, rather than just reciting numbers.
- **Performance**: Graph traversal and centrality calculations must complete in sub-second time for the current prototype scale.
