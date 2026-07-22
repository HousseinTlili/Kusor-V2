# backend/retrieval/obligation_searcher.py
"""
ObligationSearcher — fourth hybrid retrieval channel querying (:Obligation) nodes directly via Cypher.
Retrieves matching regulatory obligations and their downstream (:Process) and (:ContractTemplate) impact paths.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Dict, Any

from backend.graph.neo4j_manager import Neo4jManager
from backend.retrieval.schemas import SearchResult

logger = logging.getLogger(__name__)


class ObligationSearcher:
    """Direct Cypher search over extracted regulatory obligation nodes."""

    def __init__(self, neo4j: Neo4jManager, *, top_k: int = 10):
        self._neo4j = neo4j
        self._top_k = top_k

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        obligation_type: Optional[str] = None,
    ) -> List[SearchResult]:
        k = top_k or self._top_k

        if obligation_type:
            cypher = """
            MATCH (c:Circular)-[:INTRODUCES]->(o:Obligation)
            WHERE o.obligation_type = $ob_type
              AND (toLower(o.text) CONTAINS toLower($query) OR toLower(c.title) CONTAINS toLower($query))
            OPTIONAL MATCH (o)-[:AFFECTS]->(p:Process)
            OPTIONAL MATCH (o)-[:CONSTRAINS]->(ct:ContractTemplate)
            RETURN o.id AS ob_id,
                   o.text AS ob_text,
                   o.obligation_type AS ob_type,
                   c.reference AS circular_ref,
                   p.name AS process_name,
                   ct.name AS contract_name
            LIMIT $limit
            """
            params = {"query": query, "ob_type": obligation_type, "limit": k}
        else:
            cypher = """
            MATCH (c:Circular)-[:INTRODUCES]->(o:Obligation)
            WHERE toLower(o.text) CONTAINS toLower($query)
               OR toLower(c.reference) CONTAINS toLower($query)
            OPTIONAL MATCH (o)-[:AFFECTS]->(p:Process)
            OPTIONAL MATCH (o)-[:CONSTRAINS]->(ct:ContractTemplate)
            RETURN o.id AS ob_id,
                   o.text AS ob_text,
                   o.obligation_type AS ob_type,
                   c.reference AS circular_ref,
                   p.name AS process_name,
                   ct.name AS contract_name
            LIMIT $limit
            """
            params = {"query": query, "limit": k}

        records = self._neo4j.run_query(cypher, params)
        results: List[SearchResult] = []

        for rec in records:
            circ = rec.get("circular_ref", "Inconnu")
            ob_type = rec.get("ob_type", "REQUIREMENT")
            ob_text = rec.get("ob_text", "")
            proc = rec.get("process_name")
            contract = rec.get("contract_name")

            content = f"[{ob_type}] (Circulaire N° {circ}): {ob_text}"
            if proc:
                content += f" | Impacte le processus: {proc}"
            if contract:
                content += f" | Requis pour le contrat: {contract}"

            results.append(
                SearchResult(
                    chunk_id=f"ob-{rec['ob_id']}",
                    content=content,
                    score=0.6,
                    metadata={
                        "circular_reference": circ,
                        "obligation_type": ob_type,
                        "process_name": proc,
                        "contract_name": contract,
                    },
                    source="obligation",
                )
            )

        return results
