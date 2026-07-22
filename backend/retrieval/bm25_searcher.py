# backend/retrieval/bm25_searcher.py
"""
BM25Searcher — keyword-based retrieval using rank_bm25 with disk persistence.
COPY from v2.
"""

from __future__ import annotations

import logging
import os
import pickle
from typing import List, Optional, Dict, Any

from rank_bm25 import BM25Okapi
from backend.retrieval.schemas import SearchResult

logger = logging.getLogger(__name__)

_DEFAULT_INDEX_PATH = os.path.join("backend", "data", "bm25_index.pkl")


class BM25Searcher:
    """In-memory BM-25 index over document chunks with pickle persistence."""

    def __init__(self, *, index_path: str = _DEFAULT_INDEX_PATH, top_k: int = 10):
        self._index_path = index_path
        self._top_k = top_k
        self._bm25: Optional[BM25Okapi] = None
        self._corpus_ids: List[str] = []
        self._corpus_texts: List[str] = []
        self._corpus_meta: List[Dict[str, Any]] = []
        self._try_load()

    def search(self, query: str, top_k: Optional[int] = None) -> List[SearchResult]:
        if self._bm25 is None:
            logger.warning("BM25 index empty or not built")
            return []

        k = top_k or self._top_k
        tokens = query.lower().split()
        scores = self._bm25.get_scores(tokens)

        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        max_score = max(scores) if len(scores) > 0 and max(scores) > 0 else 1.0

        results: List[SearchResult] = []
        for idx in ranked_indices:
            if scores[idx] <= 0:
                continue
            norm_score = float(scores[idx] / max_score)
            results.append(
                SearchResult(
                    chunk_id=self._corpus_ids[idx],
                    content=self._corpus_texts[idx],
                    score=norm_score,
                    metadata=self._corpus_meta[idx],
                    source="bm25",
                )
            )
        return results

    def append_to_index(
        self, ids: List[str], texts: List[str], metadatas: List[Dict[str, Any]]
    ) -> None:
        """Add new document chunks to the existing BM25 index."""
        self._corpus_ids.extend(ids)
        self._corpus_texts.extend(texts)
        self._corpus_meta.extend(metadatas)

        tokenized = [t.lower().split() for t in self._corpus_texts]
        self._bm25 = BM25Okapi(tokenized)
        self._persist()
        logger.info("BM25 index updated (total docs: %d)", len(self._corpus_texts))

    def _persist(self) -> None:
        os.makedirs(os.path.dirname(self._index_path), exist_ok=True)
        with open(self._index_path, "wb") as f:
            pickle.dump(
                {
                    "bm25": self._bm25,
                    "ids": self._corpus_ids,
                    "texts": self._corpus_texts,
                    "meta": self._corpus_meta,
                },
                f,
            )

    def _try_load(self) -> None:
        if not os.path.exists(self._index_path):
            return
        try:
            with open(self._index_path, "rb") as f:
                data = pickle.load(f)
            self._bm25 = data["bm25"]
            self._corpus_ids = data["ids"]
            self._corpus_texts = data["texts"]
            self._corpus_meta = data["meta"]
            logger.info("Loaded BM25 index with %d docs", len(self._corpus_ids))
        except Exception as e:
            logger.error("Failed loading BM25 index: %s", e)
