from typing import List, Dict, Any
import concurrent.futures
import copy
from backend.retrieval.schemas import RetrievedChunk, RetrievalResult
from backend.retrieval.vector_searcher import VectorSearcher
from backend.retrieval.bm25_searcher import BM25Searcher
from backend.retrieval.graph_searcher import GraphSearcher
from backend.retrieval.reranker import CrossEncoderReranker

class HybridRetriever:
    """
    Orchestrates all three retrieval strategies and fuses results.
    
    Pipeline:
    1. Run VectorSearcher, BM25Searcher, GraphSearcher in parallel
    2. Fuse results with Reciprocal Rank Fusion (RRF)
    3. Re-rank top-20 with CrossEncoderReranker
    4. Return top-5 most relevant chunks
    """

    RRF_K: int = 60  # RRF constant: score = sum(1 / (k + rank))

    def __init__(
        self,
        vector_searcher: VectorSearcher,
        bm25_searcher: BM25Searcher,
        graph_searcher: GraphSearcher,
        reranker: CrossEncoderReranker,
    ) -> None:
        self.vector_searcher = vector_searcher
        self.bm25_searcher = bm25_searcher
        self.graph_searcher = graph_searcher
        self.reranker = reranker

    def retrieve(
        self,
        question: str,
        top_k: int = 5,
        use_vector: bool = True,
        use_bm25: bool = True,
        use_graph: bool = True,
    ) -> List[RetrievedChunk]:
        """
        Single public method. Runs the full hybrid retrieval pipeline.
        
        1. Execute enabled searchers in parallel
        2. Fuse with RRF
        3. Re-rank top-20
        4. Return top-k (default 5)
        """
        lists_to_fuse = []
        
        # Parallel execution of enabled searchers
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {}
            if use_vector:
                futures[executor.submit(self.vector_searcher.search, question, top_k=20)] = "vector"
            if use_bm25:
                futures[executor.submit(self.bm25_searcher.search, question, top_k=20)] = "bm25"
            if use_graph:
                futures[executor.submit(self.graph_searcher.search, question, top_k=20)] = "graph"
                
            for future in concurrent.futures.as_completed(futures):
                try:
                    res_list = future.result()
                    if res_list:
                        lists_to_fuse.append(res_list)
                except Exception:
                    pass
                    
        if not lists_to_fuse:
            return []
            
        # Reciprocal Rank Fusion (RRF)
        fused_chunks = self._reciprocal_rank_fusion(lists_to_fuse)
        
        # Re-rank top-20 using the CrossEncoder
        chunks_to_rerank = fused_chunks[:20]
        reranked_chunks = self.reranker.rerank(question, chunks_to_rerank, top_k=top_k)
        
        return reranked_chunks

    def _reciprocal_rank_fusion(
        self,
        ranked_lists: List[List[RetrievedChunk]],
    ) -> List[RetrievedChunk]:
        """
        Merge multiple ranked lists using RRF.
        
        For each chunk appearing in any list:
            rrf_score = sum(1 / (RRF_K + rank_in_list_i)) for each list containing it
        
        Chunks are identified by (document_id, chunk_index) tuple.
        Returns merged list sorted by RRF score descending.
        """
        fused = {}
        
        for ranked_list in ranked_lists:
            for rank, chunk in enumerate(ranked_list):
                key = (chunk.document_id, chunk.chunk_index)
                rank_score = 1.0 / (self.RRF_K + (rank + 1))
                
                if key not in fused:
                    chunk_copy = copy.copy(chunk)
                    fused[key] = {
                        "score": rank_score,
                        "chunk": chunk_copy,
                        "methods": {chunk.retrieval_method}
                    }
                else:
                    fused[key]["score"] += rank_score
                    fused[key]["methods"].add(chunk.retrieval_method)
                    
        fused_chunks = []
        for key, item in fused.items():
            chunk = item["chunk"]
            chunk.score = item["score"]
            # Join methods sorted alphabetically
            sorted_methods = sorted(list(item["methods"]))
            chunk.retrieval_method = "+".join(sorted_methods)
            fused_chunks.append(chunk)
            
        # Sort by RRF score descending
        fused_chunks.sort(key=lambda x: x.score, reverse=True)
        return fused_chunks
