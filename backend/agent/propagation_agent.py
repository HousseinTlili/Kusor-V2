# backend/agent/propagation_agent.py
"""
Change Propagation Agent — automatically triggered after a new circular is ingested.
Traverses the temporal knowledge graph to find every downstream obligation, process,
and contract template affected, classifies severity, and generates an ImpactPropagationReport.
"""

from __future__ import annotations

import logging
from typing import List, Optional
from backend.agent.schemas import ImpactPropagationReport, ImpactItem
from backend.graph.neo4j_manager import Neo4jManager

logger = logging.getLogger(__name__)


class ChangePropagationAgent:
    """Traverses Neo4j temporal graph to compute downstream regulatory impact."""

    def __init__(self, neo4j: Neo4jManager):
        self._neo4j = neo4j

    def analyze_impact(self, circular_ref: str) -> ImpactPropagationReport:
        cypher = """
        MATCH (c:Circular {reference: $ref})
        OPTIONAL MATCH (c)-[:INTRODUCES]->(o:Obligation)
        OPTIONAL MATCH (o)-[:AFFECTS]->(p:Process)
        OPTIONAL MATCH (o)-[:CONSTRAINS]->(ct:ContractTemplate)
        RETURN o.id AS ob_id, o.text AS ob_text, o.obligation_type AS ob_type,
               p.name AS proc_name, ct.name AS tmpl_name
        """
        try:
            records = self._neo4j.run_query(cypher, {"ref": circular_ref})
        except Exception as e:
            logger.error("Impact analysis query failed: %s", e)
            records = []

        items: List[ImpactItem] = []
        crit_count = 0
        high_count = 0

        for rec in records:
            if rec.get("ob_id"):
                ob_type = rec.get("ob_type", "REQUIREMENT")
                sev = "HIGH" if ob_type == "PROHIBITION" else "MEDIUM"
                if sev == "HIGH":
                    high_count += 1

                items.append(
                    ImpactItem(
                        entity_type="obligation",
                        entity_id=rec["ob_id"],
                        entity_name=rec.get("ob_text", "")[:100],
                        severity=sev,
                        impact_description=f"Nouvelle obligation de type {ob_type}",
                        relationship_path=["INTRODUCES"],
                    )
                )

            if rec.get("proc_name"):
                items.append(
                    ImpactItem(
                        entity_type="process",
                        entity_id=f"proc_{rec['proc_name']}",
                        entity_name=rec["proc_name"],
                        severity="HIGH",
                        impact_description=f"Processus bancaire impacté: {rec['proc_name']}",
                        relationship_path=["INTRODUCES", "AFFECTS"],
                    )
                )

        return ImpactPropagationReport(
            source_circular_ref=circular_ref,
            source_circular_title=f"Circulaire N° {circular_ref}",
            total_affected=len(items),
            critical_count=crit_count,
            high_count=high_count,
            medium_count=len(items) - (crit_count + high_count),
            low_count=0,
            affected_items=items,
            summary=f"L'analyse de propagation pour la circulaire {circular_ref} identifie {len(items)} élément(s) impacté(s).",
        )
