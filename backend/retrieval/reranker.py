# backend/retrieval/reranker.py
"""
Reranker — cross-encoder rescoring for fused candidate chunks.
COPY from v2.
"""

from __future__ import annotations

import logging
from typing import List

from sentence_transformers import CrossEncoder
from backend.retrieval.schemas import SearchResult

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class Reranker:
    """Rescores query-chunk candidate pairs using SentenceTransformers CrossEncoder."""

    def __init__(self, model_name: str = _DEFAULT_MODEL):
        logger.info("Loading CrossEncoder model: %s", model_name)
        self._model = CrossEncoder(model_name)

    def rerank(
        self,
        query: str,
        candidates: List[SearchResult],
        top_k: int = 5,
    ) -> List[SearchResult]:
        if not candidates:
            return []

        pairs = [(query, c.content) for c in candidates]
        scores = self._model.predict(pairs)

        for cand, new_score in zip(candidates, scores):
            cand.score = float(new_score)

        candidates.sort(key=lambda x: x.score, reverse=True)
        return candidates[:top_k]
