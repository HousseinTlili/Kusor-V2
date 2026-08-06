# backend/retrieval/hybrid_retriever.py
"""
HybridRetriever — orchestrates vector, BM25, entity/temporal graph, and obligation search channels,
fuses candidate lists with 4-way Reciprocal Rank Fusion (RRF), and rescores top candidates via CrossEncoder.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Dict, Any

from backend.retrieval.bm25_searcher import BM25Searcher
from backend.retrieval.graph_searcher import GraphSearcher
from backend.retrieval.obligation_searcher import ObligationSearcher
from backend.retrieval.reranker import Reranker
from backend.retrieval.schemas import RetrievalResult, SearchResult
from backend.retrieval.vector_searcher import VectorSearcher

logger = logging.getLogger(__name__)


def _rrf_fuse(
    ranked_lists: List[List[SearchResult]],
    weights: Optional[List[float]] = None,
    k: int = 60,
) -> List[SearchResult]:
    """
    Merge multiple ranked candidate lists using 4-way RRF formula:
        rrf_score(chunk) = sum( weight_i / (k + rank_i) )
    """
    if weights is None:
        weights = [1.0] * len(ranked_lists)
    if len(weights) != len(ranked_lists):
        raise ValueError("len(weights) must equal len(ranked_lists)")

    scores: Dict[str, float] = {}
    best: Dict[str, SearchResult] = {}

    for weight, results in zip(weights, ranked_lists):
        for rank, sr in enumerate(results, start=1):
            rrf_score = weight / (k + rank)
            scores[sr.chunk_id] = scores.get(sr.chunk_id, 0.0) + rrf_score
            if sr.chunk_id not in best or sr.score > best[sr.chunk_id].score:
                best[sr.chunk_id] = sr

    fused = [
        SearchResult(
            chunk_id=cid,
            content=best[cid].content,
            score=score,
            metadata=best[cid].metadata,
            source=best[cid].source,
        )
        for cid, score in scores.items()
    ]
    fused.sort(key=lambda x: x.score, reverse=True)
    return fused


class HybridRetriever:
    """4-channel hybrid retrieval orchestrator."""

    # Default weights for general queries
    DEFAULT_WEIGHTS = {
        "vector": 0.35,
        "bm25": 0.25,
        "graph": 0.25,
        "obligation": 0.15,
    }

    # Weight adjustments by classified QuestionType
    QUESTION_TYPE_WEIGHTS = {
        "factual": {"vector": 0.40, "bm25": 0.30, "graph": 0.15, "obligation": 0.15},
        "relational": {"vector": 0.20, "bm25": 0.15, "graph": 0.45, "obligation": 0.20},
        "temporal": {"vector": 0.25, "bm25": 0.15, "graph": 0.40, "obligation": 0.20},
        "comparative": {"vector": 0.35, "bm25": 0.25, "graph": 0.25, "obligation": 0.15},
        "propagation": {"vector": 0.15, "bm25": 0.15, "graph": 0.35, "obligation": 0.35},
        "point_in_time": {"vector": 0.20, "bm25": 0.15, "graph": 0.45, "obligation": 0.20},
    }

    def __init__(
        self,
        vector_searcher: Optional[VectorSearcher] = None,
        bm25_searcher: Optional[BM25Searcher] = None,
        graph_searcher: Optional[GraphSearcher] = None,
        obligation_searcher: Optional[ObligationSearcher] = None,
        reranker: Optional[Reranker] = None,
        top_k_fuse: int = 20,
        top_k_final: int = 5,
    ):
        self.vector = vector_searcher or VectorSearcher()
        self.bm25 = bm25_searcher or BM25Searcher()
        self.graph = graph_searcher or GraphSearcher()
        self.obligation = obligation_searcher or ObligationSearcher()
        self.reranker = reranker
        self.top_k_fuse = top_k_fuse
        self.top_k_final = top_k_final

    def retrieve(
        self,
        query: str,
        question_type: str = "factual",
        as_of_date: Optional[str] = None,
    ) -> List[SearchResult]:
        weights_dict = self.QUESTION_TYPE_WEIGHTS.get(
            question_type, self.DEFAULT_WEIGHTS
        )

        vec_res = self.vector.search(query, top_k=self.top_k_fuse)
        bm25_res = self.bm25.search(query, top_k=self.top_k_fuse)
        graph_res = self.graph.search(query, as_of_date=as_of_date, top_k=self.top_k_fuse)
        ob_res = self.obligation.search(query, top_k=self.top_k_fuse)

        ranked_lists = [vec_res, bm25_res, graph_res, ob_res]
        weights = [
            weights_dict["vector"],
            weights_dict["bm25"],
            weights_dict["graph"],
            weights_dict["obligation"],
        ]

        fused = _rrf_fuse(ranked_lists, weights=weights, k=60)
        top_fused = fused[: self.top_k_fuse]

        if self.reranker and top_fused:
            return self.reranker.rerank(query, top_fused, top_k=self.top_k_final)

        return top_fused[: self.top_k_final]
