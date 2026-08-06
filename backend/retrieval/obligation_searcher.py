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

    def __init__(self, neo4j: Optional[Neo4jManager] = None, *, top_k: int = 10):
        if neo4j is None:
            from backend.extensions import get_neo4j_manager
            neo4j = get_neo4j_manager()
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
              AND toLower(o.text) CONTAINS toLower($query)
            OPTIONAL MATCH (o)-[:AFFECTS]->(p:Process)
            RETURN c, o, p LIMIT $limit
            """
            params = {"ob_type": obligation_type, "query": query, "limit": k}
        else:
            cypher = """
            MATCH (c:Circular)-[:INTRODUCES]->(o:Obligation)
            WHERE any(term IN split(toLower($query), ' ') WHERE size(term) > 3 AND toLower(o.text) CONTAINS term)
            OPTIONAL MATCH (o)-[:AFFECTS]->(p:Process)
            RETURN c, o, p LIMIT $limit
            """
            params = {"query": query, "limit": k}

        try:
            records = self._neo4j.run_query(cypher, params)
        except Exception as e:
            logger.error("ObligationSearcher query failed: %s", e)
            return []

        results = []
        for i, rec in enumerate(records):
            o = rec.get("o", {})
            o_props = o.get("properties", o) if isinstance(o, dict) else {}
            content = o_props.get("text", "")
            ob_type = o_props.get("obligation_type", "OBLIGATION")
            ob_id = o_props.get("id", f"ob_{i}")

            results.append(
                SearchResult(
                    chunk_id=str(ob_id),
                    content=content,
                    score=1.0 / (i + 1),
                    metadata={"obligation_type": ob_type},
                    source="obligation",
                )
            )
        return results
