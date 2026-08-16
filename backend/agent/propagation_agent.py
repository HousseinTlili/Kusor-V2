# backend/agent/propagation_agent.py
"""
Change Propagation Agent — automatically triggered after a new circular is ingested.
Traverses the temporal knowledge graph to find every downstream obligation, process,
and contract template affected, classifies severity, and generates an ImpactPropagationReport.
"""

from __future__ import annotations

import json
import logging
from typing import List, Optional
from backend.agent.schemas import ImpactPropagationReport, ImpactItem
from backend.graph.neo4j_manager import Neo4jManager
from backend.models.impact_record import ImpactRecord
from backend.extensions import db

logger = logging.getLogger(__name__)


class ChangePropagationAgent:
    """Traverses Neo4j temporal graph to compute downstream regulatory impact."""

    def __init__(self, neo4j: Neo4jManager):
        self._neo4j = neo4j

    def analyze_impact(self, circular_ref: str, document_id: Optional[str] = None) -> ImpactPropagationReport:
        cypher = """
        MATCH (c:Circular)
        WHERE c.reference = $ref OR c.number = $ref
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
        med_count = 0
        low_count = 0

        seen_entities = set()

        for rec in records:
            ob_id = rec.get("ob_id")
            if ob_id and ob_id not in seen_entities:
                seen_entities.add(ob_id)
                ob_type = rec.get("ob_type", "REQUIREMENT")
                
                if ob_type == "PROHIBITION":
                    sev = "CRITICAL"
                    crit_count += 1
                elif ob_type == "THRESHOLD":
                    sev = "HIGH"
                    high_count += 1
                elif ob_type == "DEADLINE":
                    sev = "LOW"
                    low_count += 1
                else:
                    sev = "MEDIUM"
                    med_count += 1

                items.append(
                    ImpactItem(
                        entity_type="obligation",
                        entity_id=ob_id,
                        entity_name=rec.get("ob_text", "")[:100],
                        severity=sev,
                        impact_description=f"Nouvelle obligation réglementaire de type {ob_type}",
                        relationship_path=["INTRODUCES"],
                    )
                )

            proc_name = rec.get("proc_name")
            if proc_name and f"proc_{proc_name}" not in seen_entities:
                seen_entities.add(f"proc_{proc_name}")
                items.append(
                    ImpactItem(
                        entity_type="process",
                        entity_id=f"proc_{proc_name}",
                        entity_name=proc_name,
                        severity="HIGH",
                        impact_description=f"Processus bancaire impacté: {proc_name}",
                        relationship_path=["INTRODUCES", "AFFECTS"],
                    )
                )
                high_count += 1

            tmpl_name = rec.get("tmpl_name")
            if tmpl_name and f"tmpl_{tmpl_name}" not in seen_entities:
                seen_entities.add(f"tmpl_{tmpl_name}")
                items.append(
                    ImpactItem(
                        entity_type="contract_template",
                        entity_id=f"tmpl_{tmpl_name}",
                        entity_name=tmpl_name,
                        severity="HIGH",
                        impact_description=f"Modèle de contrat impacté: {tmpl_name}",
                        relationship_path=["INTRODUCES", "CONSTRAINS"],
                    )
                )
                high_count += 1

        report = ImpactPropagationReport(
            source_circular_ref=circular_ref,
            source_circular_title=f"Circulaire N° {circular_ref}",
            total_affected=len(items),
            critical_count=crit_count,
            high_count=high_count,
            medium_count=med_count,
            low_count=low_count,
            affected_items=items,
            summary=f"L'analyse de propagation pour la circulaire {circular_ref} identifie {len(items)} élément(s) impacté(s).",
        )

        if document_id:
            self.persist_impact_records(document_id, report)

        if report.critical_count > 0 or report.high_count > 0:
            self._notify_n8n(report)

        return report

    def _notify_n8n(self, report: ImpactPropagationReport) -> None:
        """Send webhook notification to n8n if active."""
        import requests
        for url in ["http://localhost:5678/webhook/impact-alert", "http://localhost:5678/webhook-test/impact-alert"]:
            try:
                requests.post(
                    url,
                    json={
                        "circular_number": report.source_circular_ref,
                        "circular_ref": report.source_circular_ref,
                        "severity": "CRITICAL" if report.critical_count > 0 else "HIGH",
                        "affected_count": report.total_affected,
                        "total_affected": report.total_affected,
                        "summary": report.summary,
                        "source": "Portail BCT"
                    },
                    timeout=2
                )
                break
            except Exception:
                pass

    def persist_impact_records(self, document_id: str, report: ImpactPropagationReport) -> int:
        """Persist impact records into PostgreSQL database for audit and compliance dashboard."""
        try:
            persisted = 0
            for item in report.affected_items:
                record = ImpactRecord(
                    source_circular_id=document_id,
                    source_circular_ref=report.source_circular_ref,
                    affected_entity_type=item.entity_type,
                    affected_entity_id=item.entity_id,
                    affected_entity_name=item.entity_name,
                    severity=item.severity,
                    impact_description=item.impact_description,
                    relationship_path=json.dumps(item.relationship_path),
                )
                db.session.add(record)
                persisted += 1
            db.session.commit()
            logger.info("Persisted %d ImpactRecord entries for document %s", persisted, document_id)
            return persisted
        except Exception as e:
            db.session.rollback()
            logger.error("Failed to persist ImpactRecord entries: %s", e)
            return 0


