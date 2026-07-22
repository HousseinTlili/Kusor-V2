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
        vector_searcher: VectorSearcher,
        bm25_searcher: BM25Searcher,
        graph_searcher: GraphSearcher,
        obligation_searcher: ObligationSearcher,
        reranker: Optional[Reranker] = None,
        top_k_fuse: int = 20,
        top_k_final: int = 5,
    ):
        self.vector = vector_searcher
        self.bm25 = bm25_searcher
        self.graph = graph_searcher
        self.obligation = obligation_searcher
        self.reranker = reranker
        self.top_k_fuse = top_k_fuse
        self.top_k_final = top_k_final

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        question_type: str = "factual",
        as_of_date: Optional[str] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> RetrievalResult:
        final_k = top_k or self.top_k_final
        weights_dict = self.QUESTION_TYPE_WEIGHTS.get(question_type, self.DEFAULT_WEIGHTS)

        # 1. Execute all 4 channels
        vec_results = self._safe_search("vector", self.vector.search, query, metadata_filter=metadata_filter)
        bm25_results = self._safe_search("bm25", self.bm25.search, query)
        graph_results = self._safe_search("graph", self.graph.search, query, as_of_date=as_of_date)
        ob_results = self._safe_search("obligation", self.obligation.search, query)

        # 2. 4-Way RRF Fusion
        fused = _rrf_fuse(
            [vec_results, bm25_results, graph_results, ob_results],
            weights=[
                weights_dict["vector"],
                weights_dict["bm25"],
                weights_dict["graph"],
                weights_dict["obligation"],
            ],
        )
        candidates = fused[: self.top_k_fuse]

        # 3. Cross-encoder Reranking if available
        if self.reranker and candidates:
            reranked = self.reranker.rerank(query, candidates, top_k=final_k)
        else:
            reranked = candidates[:final_k]

        active_channels = sum(1 for ch in [vec_results, bm25_results, graph_results, ob_results] if ch)
        all_results = vec_results + bm25_results + graph_results + ob_results
        unique_sources = {
            r.metadata.get("document_id") or r.metadata.get("circular_reference")
            for r in all_results
            if r.metadata.get("document_id") or r.metadata.get("circular_reference")
        }

        return RetrievalResult(
            results=reranked,
            total_candidates=len(fused),
            channels_used=active_channels,
            unique_sources=len(unique_sources),
            graph_used=bool(graph_results),
            obligation_used=bool(ob_results),
        )

    @staticmethod
    def _safe_search(name: str, fn, *args, **kwargs) -> List[SearchResult]:
        try:
            return fn(*args, **kwargs) or []
        except Exception:
            logger.exception("Retrieval channel '%s' failed", name)
            return []
