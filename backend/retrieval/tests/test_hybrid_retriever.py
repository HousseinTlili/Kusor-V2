import pytest
from unittest.mock import MagicMock
from backend.retrieval.schemas import RetrievedChunk
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.retrieval.vector_searcher import VectorSearcher
from backend.retrieval.bm25_searcher import BM25Searcher
from backend.retrieval.graph_searcher import GraphSearcher
from backend.retrieval.reranker import CrossEncoderReranker

class TestHybridRetriever:
    @pytest.fixture
    def mock_components(self):
        vector_searcher = MagicMock(spec=VectorSearcher)
        bm25_searcher = MagicMock(spec=BM25Searcher)
        graph_searcher = MagicMock(spec=GraphSearcher)
        reranker = MagicMock(spec=CrossEncoderReranker)
        return vector_searcher, bm25_searcher, graph_searcher, reranker

    def test_all_three_paths_contribute(self, mock_components) -> None:
        """Vector, BM25, and graph searchers must all return results."""
        vs, bs, gs, rr = mock_components
        
        chunk_v = RetrievedChunk("content vector", "doc1", 0, 1, "file1.pdf", "2024-01", 0.9, "vector")
        chunk_b = RetrievedChunk("content bm25", "doc2", 1, 2, "file2.pdf", "2024-02", 0.8, "bm25")
        chunk_g = RetrievedChunk("content graph", "doc3", 2, 3, "file3.pdf", "2024-03", 0.7, "graph")
        
        vs.search.return_value = [chunk_v]
        bs.search.return_value = [chunk_b]
        gs.search.return_value = [chunk_g]
        
        rr.rerank.side_effect = lambda q, chunks, top_k: chunks[:top_k]
        
        hr = HybridRetriever(vs, bs, gs, rr)
        results = hr.retrieve("test query", top_k=3)
        
        assert len(results) == 3
        methods = {c.retrieval_method for c in results}
        assert "vector" in methods
        assert "bm25" in methods
        assert "graph" in methods
        
        vs.search.assert_called_once_with("test query", top_k=20)
        bs.search.assert_called_once_with("test query", top_k=20)
        gs.search.assert_called_once_with("test query", top_k=20)

    def test_rrf_fusion_scores(self, mock_components) -> None:
        """RRF scores should increase for chunks appearing in multiple lists."""
        vs, bs, gs, rr = mock_components
        
        chunk_v1 = RetrievedChunk("common content", "doc_common", 0, 1, "file.pdf", "2024-01", 0.9, "vector")
        chunk_b1 = RetrievedChunk("common content", "doc_common", 0, 1, "file.pdf", "2024-01", 0.8, "bm25")
        
        chunk_v2 = RetrievedChunk("vector unique", "doc_v", 1, 1, "file.pdf", "2024-01", 0.7, "vector")
        chunk_b2 = RetrievedChunk("bm25 unique", "doc_b", 2, 1, "file.pdf", "2024-01", 0.6, "bm25")
        
        vs.search.return_value = [chunk_v1, chunk_v2]
        bs.search.return_value = [chunk_b1, chunk_b2]
        gs.search.return_value = []
        
        rr.rerank.side_effect = lambda q, chunks, top_k: chunks[:top_k]
        
        hr = HybridRetriever(vs, bs, gs, rr)
        
        fused = hr._reciprocal_rank_fusion([
            [chunk_v1, chunk_v2],
            [chunk_b1, chunk_b2]
        ])
        
        assert len(fused) == 3
        assert fused[0].document_id == "doc_common"
        assert fused[0].chunk_index == 0
        assert fused[0].score > fused[1].score
        assert fused[0].score > fused[2].score
        assert fused[0].retrieval_method == "bm25+vector"

    def test_reranked_more_relevant(self, mock_components) -> None:
        """Cross-encoder reranked output should be more relevant than raw vector."""
        vs, bs, gs, rr = mock_components
        
        chunk1 = RetrievedChunk("less relevant content", "doc1", 0, 1, "file.pdf", "2024-01", 0.9, "vector")
        chunk2 = RetrievedChunk("highly relevant content", "doc2", 0, 1, "file.pdf", "2024-01", 0.5, "vector")
        
        vs.search.return_value = [chunk1, chunk2]
        bs.search.return_value = []
        gs.search.return_value = []
        
        def mock_rerank(query, chunks, top_k):
            chunks[0].score = 0.1  # doc1
            chunks[1].score = 0.95  # doc2
            chunks.sort(key=lambda x: x.score, reverse=True)
            return chunks[:top_k]
            
        rr.rerank.side_effect = mock_rerank
        
        hr = HybridRetriever(vs, bs, gs, rr)
        results = hr.retrieve("query", top_k=2)
        
        assert results[0].document_id == "doc2"
        assert results[0].score == 0.95
        assert results[1].document_id == "doc1"
        assert results[1].score == 0.1

    def test_single_strategy_mode(self, mock_components) -> None:
        """Setting use_bm25=False should exclude BM25 results."""
        vs, bs, gs, rr = mock_components
        
        chunk_v = RetrievedChunk("content vector", "doc1", 0, 1, "file1.pdf", "2024-01", 0.9, "vector")
        chunk_b = RetrievedChunk("content bm25", "doc2", 1, 2, "file2.pdf", "2024-02", 0.8, "bm25")
        
        vs.search.return_value = [chunk_v]
        bs.search.return_value = [chunk_b]
        gs.search.return_value = []
        
        rr.rerank.side_effect = lambda q, chunks, top_k: chunks[:top_k]
        
        hr = HybridRetriever(vs, bs, gs, rr)
        results = hr.retrieve("test query", use_bm25=False)
        
        assert len(results) == 1
        assert results[0].retrieval_method == "vector"
        bs.search.assert_not_called()
        vs.search.assert_called_once()

    def test_empty_graph_results_handled(self, mock_components) -> None:
        """If graph search finds nothing, vector+BM25 still work."""
        vs, bs, gs, rr = mock_components
        
        chunk_v = RetrievedChunk("content vector", "doc1", 0, 1, "file1.pdf", "2024-01", 0.9, "vector")
        chunk_b = RetrievedChunk("content bm25", "doc2", 1, 2, "file2.pdf", "2024-02", 0.8, "bm25")
        
        vs.search.return_value = [chunk_v]
        bs.search.return_value = [chunk_b]
        gs.search.return_value = []
        
        rr.rerank.side_effect = lambda q, chunks, top_k: chunks[:top_k]
        
        hr = HybridRetriever(vs, bs, gs, rr)
        results = hr.retrieve("test query")
        
        assert len(results) == 2
        methods = {c.retrieval_method for c in results}
        assert "vector" in methods
        assert "bm25" in methods
        assert "graph" not in methods

    def test_deduplication(self, mock_components) -> None:
        """Same chunk from multiple searchers should appear once in final output."""
        vs, bs, gs, rr = mock_components
        
        chunk_v = RetrievedChunk("identical content", "doc1", 0, 1, "file.pdf", "2024-01", 0.9, "vector")
        chunk_b = RetrievedChunk("identical content", "doc1", 0, 1, "file.pdf", "2024-01", 0.8, "bm25")
        chunk_g = RetrievedChunk("identical content", "doc1", 0, 1, "file.pdf", "2024-01", 0.7, "graph")
        
        vs.search.return_value = [chunk_v]
        bs.search.return_value = [chunk_b]
        gs.search.return_value = [chunk_g]
        
        hr = HybridRetriever(vs, bs, gs, rr)
        
        fused = hr._reciprocal_rank_fusion([
            [chunk_v],
            [chunk_b],
            [chunk_g]
        ])
        
        assert len(fused) == 1
        assert fused[0].document_id == "doc1"
        assert fused[0].chunk_index == 0
        assert fused[0].retrieval_method == "bm25+graph+vector"
