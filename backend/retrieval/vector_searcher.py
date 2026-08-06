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

    def __init__(self, collection: Optional[chromadb.Collection] = None, *, top_k: int = 10):
        if collection is None:
            from backend.extensions import get_chroma_collection
            collection = get_chroma_collection()
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
            res = self._col.query(**kwargs)
        except Exception as e:
            logger.error("Vector search failed: %s", e)
            return []

        ids = (res.get("ids") or [[]])[0]
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]

        results = []
        for i in range(len(ids)):
            score = 1.0 - (dists[i] if i < len(dists) else 0.0)
            results.append(
                SearchResult(
                    chunk_id=ids[i],
                    content=docs[i] if i < len(docs) else "",
                    score=score,
                    metadata=metas[i] if i < len(metas) else {},
                    source="vector",
                )
            )
        return results
