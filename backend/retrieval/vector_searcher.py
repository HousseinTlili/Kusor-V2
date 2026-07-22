# backend/retrieval/vector_searcher.py
"""
VectorSearcher — embedding-based retrieval over ChromaDB vectors.
COPY from v2 with module-scope metadata filtering.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Dict, Any

import chromadb
from backend.retrieval.schemas import SearchResult

logger = logging.getLogger(__name__)


class VectorSearcher:
    """Query ChromaDB for semantically similar document chunks."""

    def __init__(self, collection: chromadb.Collection, *, top_k: int = 10):
        self._col = collection
        self._top_k = top_k

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        *,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        Embed query using ChromaDB's configured embedding function (nomic-embed-text)
        and return the nearest neighbors.
        """
        k = top_k or self._top_k
        kwargs: Dict[str, Any] = {"query_texts": [query], "n_results": k}
        if metadata_filter:
            kwargs["where"] = metadata_filter

        try:
            raw = self._col.query(**kwargs)
        except Exception as e:
            logger.error("ChromaDB query failed: %s", e)
            return []

        results: List[SearchResult] = []
        ids = raw.get("ids", [[]])[0]
        docs = raw.get("documents", [[]])[0]
        dists = raw.get("distances", [[]])[0]
        metas = raw.get("metadatas", [[]])[0]

        for cid, doc, dist, meta in zip(ids, docs, dists, metas):
            # Convert L2 distance to cosine similarity proxy score (0..1)
            score = 1.0 / (1.0 + dist)
            results.append(
                SearchResult(
                    chunk_id=cid,
                    content=doc,
                    score=score,
                    metadata=meta or {},
                    source="vector",
                )
            )
        return results
