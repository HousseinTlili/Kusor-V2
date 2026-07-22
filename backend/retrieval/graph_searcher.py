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

    def __init__(self, neo4j: Neo4jManager, *, top_k: int = 10):
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
            # Fallback to query words if spaCy produces no entities
            words = [w for w in query.split() if len(w) > 3]
            entities = [(w, "KEYWORD") for w in words[:3]]

        if not entities:
            return []

        results: List[SearchResult] = []
        seen: set[str] = set()

        for ent_text, ent_label in entities:
            hits = self._query_graph(ent_text, ent_label, as_of_date)
            for hit in hits:
                if hit.chunk_id in seen:
                    continue
                seen.add(hit.chunk_id)
                results.append(hit)
                if len(results) >= k:
                    return results

        return results

    @staticmethod
    def _extract_entities(text: str) -> List[Tuple[str, str]]:
        if _nlp is None:
            return []
        doc = _nlp(text)
        return [(ent.text, ent.label_) for ent in doc.ents]

    def _query_graph(
        self, entity: str, label: str, as_of_date: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Query Neo4j for 1-hop subgraphs around matching entities,
        filtering relationships temporally if as_of_date is provided.
        """
        if as_of_date:
            cypher = """
            MATCH (n)
            WHERE toLower(n.name) CONTAINS toLower($entity)
               OR toLower(n.title) CONTAINS toLower($entity)
               OR toLower(n.reference) CONTAINS toLower($entity)
            OPTIONAL MATCH (n)-[r]-(m)
            WHERE (r.valid_from IS NULL OR r.valid_from <= date($as_of_date))
              AND (r.valid_until IS NULL OR r.valid_until >= date($as_of_date))
            RETURN
                n.name AS source_name,
                labels(n) AS source_labels,
                type(r) AS rel_type,
                r.valid_from AS valid_from,
                r.valid_until AS valid_until,
                m.name AS target_name,
                m.title AS target_title,
                labels(m) AS target_labels,
                n.content AS content,
                n.reference AS reference
            LIMIT 50
            """
            params = {"entity": entity, "as_of_date": as_of_date}
        else:
            cypher = """
            MATCH (n)
            WHERE toLower(n.name) CONTAINS toLower($entity)
               OR toLower(n.title) CONTAINS toLower($entity)
               OR toLower(n.reference) CONTAINS toLower($entity)
            OPTIONAL MATCH (n)-[r]-(m)
            RETURN
                n.name AS source_name,
                labels(n) AS source_labels,
                type(r) AS rel_type,
                m.name AS target_name,
                m.title AS target_title,
                labels(m) AS target_labels,
                n.content AS content,
                n.reference AS reference
            LIMIT 50
            """
            params = {"entity": entity}

        records = self._neo4j.run_query(cypher, params)
        results: List[SearchResult] = []

        for rec in records:
            src = rec.get("source_name") or rec.get("reference") or "Inconnu"
            parts = [f"[{','.join(rec.get('source_labels', []))}] {src}"]

            if rec.get("rel_type"):
                tgt = rec.get("target_name") or rec.get("target_title") or ""
                parts.append(f" --{rec['rel_type']}--> [{','.join(rec.get('target_labels', []))}] {tgt}")

            content = rec.get("content") or " | ".join(parts)
            chunk_id = f"graph-{src}-{rec.get('rel_type', 'self')}"

            results.append(
                SearchResult(
                    chunk_id=chunk_id,
                    content=content,
                    score=0.5,
                    metadata={
                        "source_labels": rec.get("source_labels", []),
                        "entity_matched": entity,
                        "temporal_date": as_of_date,
                    },
                    source="graph",
                )
            )
        return results
