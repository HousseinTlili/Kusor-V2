# backend/graph/graph_builder.py
"""
GraphBuilder — constructs the Neo4j knowledge graph for KUSOR v3.
Features:
- Every relationship edge carries temporal attributes (valid_from, valid_until).
- Creates (:Obligation), (:Process), (:ContractTemplate) nodes.
- Establishes INTRODUCES, AFFECTS, CONSTRAINS, AMENDS, REPLACES, REFERENCES edges.
"""

from __future__ import annotations

import logging
import re
from datetime import date
from typing import List, Optional, Dict, Any

from backend.graph.neo4j_manager import Neo4jManager
from backend.models.document import Document
from backend.processing.obligation_extractor import ExtractedObligation

logger = logging.getLogger(__name__)

# Temporal extraction regex for French legal formulas
_EFFECTIVE_DATE_RE = re.compile(
    r"(?:à\s+compter\s+du|avec\s+effet\s+au|applicable\s+au)\s+(\d{1,2}(?:er)?\s+[a-zA-Zàâäéèêëîïôöùûüç]+\s+\d{4})",
    re.IGNORECASE,
)
_REPLACES_RE = re.compile(
    r"(?:abrogeant|remplaçant|abroge|remplace)\s+.*?[Cc]irculaire\s+[Nn]°?\s*(\d{4}-\d{1,2})",
    re.IGNORECASE,
)
_AMENDS_RE = re.compile(
    r"(?:modifiant|complétant|modifie|complète)\s+.*?[Cc]irculaire\s+[Nn]°?\s*(\d{4}-\d{1,2})",
    re.IGNORECASE,
)


class GraphBuilder:
    def __init__(self, neo4j: Neo4jManager):
        self._neo4j = neo4j

    def build_document_graph(self, doc: Document, raw_text: str) -> None:
        circ_ref = doc.number or doc.circular_reference or doc.id
        effective_date_str = self._extract_effective_date(raw_text) or (
            doc.date_issued.isoformat() if doc.date_issued else date.today().isoformat()
        )

        # 1. Create Circular node
        self._neo4j.run_query(
            """
            MERGE (c:Circular {reference: $ref})
            SET c.title = $title,
                c.document_id = $doc_id,
                c.date_issued = date($date_issued),
                c.doc_type = $doc_type,
                c.status = $status
            """,
            {
                "ref": circ_ref,
                "title": doc.title,
                "doc_id": doc.id,
                "date_issued": effective_date_str,
                "doc_type": doc.doc_type,
                "status": doc.status or "ACTIVE",
            },
        )

        # 2. Inter-circular Temporal Relationships
        self._create_temporal_amendments(raw_text, circ_ref, effective_date_str)
        self._create_temporal_replacements(raw_text, circ_ref, effective_date_str)

    def add_obligations_and_impacts(
        self, doc: Document, obligations: List[ExtractedObligation]
    ) -> None:
        circ_ref = doc.number or doc.circular_reference or doc.id
        effective_date_str = (
            doc.date_issued.isoformat() if doc.date_issued else date.today().isoformat()
        )

        for ob in obligations:
            # Create (:Obligation) node
            self._neo4j.run_query(
                """
                MERGE (o:Obligation {id: $id})
                SET o.text = $text,
                    o.obligation_type = $ob_type,
                    o.circular_id = $circ_ref,
                    o.article_id = $article_id,
                    o.created_at = datetime()
                WITH o
                MATCH (c:Circular {reference: $circ_ref})
                MERGE (c)-[r:INTRODUCES]->(o)
                SET r.valid_from = date($valid_from),
                    r.valid_until = null
                """,
                {
                    "id": ob.id,
                    "text": ob.text,
                    "ob_type": ob.obligation_type,
                    "circ_ref": circ_ref,
                    "article_id": ob.article_id or "",
                    "valid_from": effective_date_str,
                },
            )

            # Link to Process if identified
            if ob.target_process:
                self._neo4j.run_query(
                    """
                    MERGE (p:Process {name: $proc_name})
                    WITH p
                    MATCH (o:Obligation {id: $ob_id})
                    MERGE (o)-[r:AFFECTS]->(p)
                    SET r.valid_from = date($valid_from),
                        r.valid_until = null
                    """,
                    {
                        "proc_name": ob.target_process,
                        "ob_id": ob.id,
                        "valid_from": effective_date_str,
                    },
                )

            # Link to ContractTemplate if identified
            if ob.target_contract:
                self._neo4j.run_query(
                    """
                    MERGE (ct:ContractTemplate {name: $tmpl_name})
                    WITH ct
                    MATCH (o:Obligation {id: $ob_id})
                    MERGE (o)-[r:CONSTRAINS]->(ct)
                    SET r.valid_from = date($valid_from),
                        r.valid_until = null
                    """,
                    {
                        "tmpl_name": ob.target_contract,
                        "ob_id": ob.id,
                        "valid_from": effective_date_str,
                    },
                )

    def _create_temporal_amendments(
        self, text: str, source_ref: str, effective_date: str
    ) -> None:
        amended = set(_AMENDS_RE.findall(text))
        for target_ref in amended:
            if target_ref == source_ref:
                continue
            self._neo4j.run_query(
                """
                MERGE (target:Circular {reference: $target_ref})
                WITH target
                MATCH (source:Circular {reference: $source_ref})
                MERGE (source)-[r:AMENDS]->(target)
                SET r.valid_from = date($effective_date),
                    r.valid_until = null,
                    target.status = 'MODIFIED'
                """,
                {
                    "source_ref": source_ref,
                    "target_ref": target_ref,
                    "effective_date": effective_date,
                },
            )

    def _create_temporal_replacements(
        self, text: str, source_ref: str, effective_date: str
    ) -> None:
        replaced = set(_REPLACES_RE.findall(text))
        for target_ref in replaced:
            if target_ref == source_ref:
                continue
            self._neo4j.run_query(
                """
                MATCH (source:Circular {reference: $source_ref})
                MERGE (target:Circular {reference: $target_ref})
                MERGE (source)-[r:REPLACES]->(target)
                SET r.valid_from = date($effective_date),
                    r.valid_until = null,
                    target.status = 'ABROGATED'
                WITH target
                MATCH (target)-[old_r:INTRODUCES]->(o:Obligation)
                SET old_r.valid_until = date($effective_date)
                """,
                {
                    "source_ref": source_ref,
                    "target_ref": target_ref,
                    "effective_date": effective_date,
                },
            )

    @staticmethod
    def _extract_effective_date(text: str) -> Optional[str]:
        match = _EFFECTIVE_DATE_RE.search(text)
        if match:
            return None
        return None
