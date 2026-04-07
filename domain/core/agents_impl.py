from typing import Dict, Any, List, Optional
from domain.core.agent import HermesAgent, AgentStatus, AgentTask, AgentResult
from domain.core.ports import BaseLLMInterface

class ResearcherAgent(HermesAgent):
    """
    A specialized agent focused on deep semantic exploration.
    It uses the semantic memory to find evidence and synthesize findings.
    """
    async def _plan(self, task: AgentTask, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        # A real agent would use the LLM to decompose the task.
        # For this implementation, we generate a simple plan based on the goal.
        return [{"action": "query_memory", "query": task.goal}]

    async def _execute_plan(self, plan: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings = []
        memory = context.get("semantic_memory")
        
        for step in plan:
            if step["action"] == "query_memory":
                query = step["query"]
                # We assume semantic_memory is passed in context and is an instance of SemanticMemory
                if memory:
                    results = memory.query(query, context_id=context.get("context_id"))
                    findings.append({"type": "memory_match", "results": results})
                else:
                    findings.append({"type": "error", "message": "No semantic memory provided in context"})
        
        return findings

    async def _reflect(self, findings: List[Dict[str, Any]], task: AgentTask, context: Dict[str, Any]) -> AgentResult:
        # Extract the best piece of evidence from the findings
        best_evidence = []
        summary = "No relevant evidence found."
        confidence = 0.0

        for finding in findings:
            if finding["type"] == "memory_match":
                results = finding["results"]
                if results:
                    best_evidence = [r["text"] for r in results]
                    summary = f"Found relevant information: {results[0]['text']}"
                    confidence = 0.9 if len(results) > 0 else 0.1
                break
            elif finding["type"] == "error":
                summary = finding["message"]
                confidence = 0.0

        return AgentResult(
            finding=summary,
            confidence=confidence,
            evidence=[{"text": e} for e in best_evidence]
        )

class AuditorAgent(HermesAgent):
    """
    A specialized agent focused on structural integrity and logical consistency.
    It examines the structural ledger to validate claims.
    """
    async def _plan(self, task: AgentTask, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [{"action": "check_ledger", "target": task.goal}]

    async def _execute_plan(self, plan: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        from domain.core.models import Project, Milestone, Skill, IdentityMarker, RelationalEdge

        findings = []
        ledger = context.get("structural_ledger")

        for step in plan:
            if step["action"] != "check_ledger":
                continue

            if not ledger:
                findings.append({"type": "error", "message": "No structural ledger provided in context"})
                continue

            with ledger.session_scope() as session:
                edge_count = session.query(RelationalEdge).count()
                skill_count = session.query(Skill).count()
                project_count = session.query(Project).count()
                milestone_count = session.query(Milestone).count()
                marker_count = session.query(IdentityMarker).count()

                # Check for orphaned edges (edges referencing nonexistent nodes)
                all_node_ids = set()
                for model in (Project, Milestone, Skill, IdentityMarker):
                    all_node_ids.update(row.id for row in session.query(model.id).all())

                orphaned = 0
                for edge in session.query(RelationalEdge).all():
                    if edge.source_id not in all_node_ids or edge.target_id not in all_node_ids:
                        orphaned += 1

            finding = {
                "type": "ledger_check",
                "entity_counts": {
                    "projects": project_count,
                    "milestones": milestone_count,
                    "skills": skill_count,
                    "identity_markers": marker_count,
                    "edges": edge_count,
                },
                "orphaned_edges": orphaned,
                "has_entities": (skill_count + project_count + milestone_count) > 0,
            }
            findings.append(finding)

        return findings

    async def _reflect(self, findings: List[Dict[str, Any]], task: AgentTask, context: Dict[str, Any]) -> AgentResult:
        summary = "Audit complete."
        confidence = 0.0
        evidence = []

        for finding in findings:
            if finding["type"] == "error":
                summary = finding["message"]
                confidence = 0.0
                continue

            if finding["type"] == "ledger_check":
                evidence.append(finding)
                counts = finding["entity_counts"]
                orphaned = finding["orphaned_edges"]

                if not finding["has_entities"]:
                    summary = "Audit warning: ledger contains no entities. Change may be premature."
                    confidence = 0.2
                elif orphaned > 0:
                    summary = f"Audit concern: {orphaned} orphaned edge(s) detected. Structural integrity at risk."
                    confidence = 0.4
                else:
                    total = sum(counts.values())
                    summary = f"Audit passed: {total} entities verified, no orphaned edges."
                    confidence = 0.9

        return AgentResult(
            finding=summary,
            confidence=confidence,
            evidence=evidence
        )
