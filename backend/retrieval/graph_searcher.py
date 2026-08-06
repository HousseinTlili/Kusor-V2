# backend/retrieval/graph_searcher.py
"""
GraphSearcher — entity-aware and temporal retrieval from Neo4j knowledge graph.
V3 modification: supports as_of_date filtering over valid_from/valid_until properties.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple, Dict, Any

import spacy
from backend.graph.neo4j_manager import Neo4jManager
from backend.retrieval.schemas import SearchResult

logger = logging.getLogger(__name__)

try:
    _nlp = spacy.load("fr_core_news_lg")
except OSError:
    logger.warning("spaCy fr_core_news_lg unavailable; graph entity extraction fallback to regex")
    _nlp = None


class GraphSearcher:
    """Traverses Neo4j nodes and temporal relationships matching extracted query entities."""

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
        as_of_date: Optional[str] = None,
    ) -> List[SearchResult]:
        k = top_k or self._top_k
        entities = self._extract_entities(query)
        if not entities:
            return []

        cypher = """
        MATCH (n)-[r]-(m)
        WHERE any(term IN $entities WHERE toLower(coalesce(n.name, n.title, n.text, '')) CONTAINS toLower(term))
        """
        if as_of_date:
            cypher += """
            AND (r.valid_from IS NULL OR r.valid_from <= date($as_of_date))
            AND (r.valid_until IS NULL OR r.valid_until >= date($as_of_date))
            """
        cypher += " RETURN n, r, m LIMIT $limit"

        try:
            records = self._neo4j.run_query(
                cypher, {"entities": entities, "as_of_date": as_of_date, "limit": k}
            )
        except Exception as e:
            logger.error("GraphSearcher Cypher query failed: %s", e)
            return []

        results = []
        for i, rec in enumerate(records):
            n = rec.get("n", {})
            node_props = n.get("properties", n) if isinstance(n, dict) else {}
            content = (
                node_props.get("text")
                or node_props.get("title")
                or node_props.get("name")
                or str(node_props)
            )
            node_id = str(n.get("id", i))
            results.append(
                SearchResult(
                    chunk_id=f"graph_{node_id}",
                    content=content,
                    score=1.0 / (i + 1),
                    metadata={"entity_type": labels_str if (labels_str := str(n.get("labels", ""))) else "GraphNode"},
                    source="graph",
                )
            )
        return results

    def _extract_entities(self, query: str) -> List[str]:
        if _nlp:
            doc = _nlp(query)
            ents = [ent.text for ent in doc.ents]
            if ents:
                return ents

        stop_words = {"le", "la", "les", "du", "de", "des", "un", "une", "est", "sont", "quelles", "quels", "quel", "sur", "pour"}
        words = [w.strip() for w in query.split() if len(w.strip()) > 3 and w.lower() not in stop_words]
        return words
