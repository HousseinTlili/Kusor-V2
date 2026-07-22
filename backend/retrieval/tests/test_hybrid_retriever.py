# backend/retrieval/tests/test_hybrid_retriever.py
"""
Unit tests for HybridRetriever and 4-way RRF fusion.
"""

from backend.retrieval.hybrid_retriever import HybridRetriever, _rrf_fuse
from backend.retrieval.schemas import SearchResult


def test_rrf_fuse_weighting():
    list1 = [SearchResult(chunk_id="chunk_1", content="Content 1", score=0.9, source="vector")]
    list2 = [SearchResult(chunk_id="chunk_2", content="Content 2", score=0.8, source="bm25")]

    fused = _rrf_fuse([list1, list2], weights=[0.4, 0.2])
    assert len(fused) == 2
    assert fused[0].chunk_id == "chunk_1"


def test_hybrid_retriever_question_type_weights():
    weights = HybridRetriever.QUESTION_TYPE_WEIGHTS["relational"]
    assert weights["graph"] == 0.45
    assert weights["obligation"] == 0.20
