from typing import List, Optional, Any
from collections import defaultdict

from backend.retrieval.schemas import RetrievedChunk
from backend.retrieval.vector_searcher import VectorSearcher
from backend.retrieval.bm25_searcher import BM25Searcher
from backend.retrieval.graph_searcher import GraphSearcher
from backend.retrieval.reranker import CrossEncoderReranker


class HybridRetriever:
    """
    Module 5 — Hybrid Search Engine:
    Combines Vector Search (Dense), BM25 (Sparse), and Graph Traversals (Neo4j),
    fuses candidate lists with Reciprocal Rank Fusion (RRF),
    and re-ranks top candidates using a Cross-Encoder.
    """

    def __init__(
        self,
        vector_searcher: Optional[VectorSearcher] = None,
        bm25_searcher: Optional[BM25Searcher] = None,
        graph_searcher: Optional[GraphSearcher] = None,
        reranker: Optional[CrossEncoderReranker] = None,
        k: int = 60
    ) -> None:
        self.vector_searcher = vector_searcher or VectorSearcher()
        self.bm25_searcher = bm25_searcher or BM25Searcher()
        self.graph_searcher = graph_searcher or GraphSearcher()
        self.reranker = reranker or CrossEncoderReranker()
        self.k = k

    def _reciprocal_rank_fusion(
        self,
        ranked_lists: List[List[Any]],
        k: Optional[int] = None
    ) -> List[RetrievedChunk]:
        """
        Combine multiple ranked lists using Reciprocal Rank Fusion (RRF):
        RRF_score(d) = sum(1 / (k + rank(d)))
        """
        k_val = k if k is not None else self.k
        scores = defaultdict(float)
        chunk_map = {}
        methods_map = defaultdict(set)

        for r_list in ranked_lists:
            for rank, item in enumerate(r_list, start=1):
                doc_id = item.get("document_id") if isinstance(item, dict) else getattr(item, "document_id", "doc")
                chunk_idx = item.get("chunk_index", 0) if isinstance(item, dict) else getattr(item, "chunk_index", 0)
                key = (doc_id, chunk_idx)
                
                scores[key] += 1.0 / (k_val + rank)
                chunk_map[key] = item
                
                method_val = item.get("retrieval_method") if isinstance(item, dict) else getattr(item, "retrieval_method", "")
                if method_val:
                    for m in str(method_val).split("+"):
                        methods_map[key].add(m)

        fused_chunks = []
        for key, total_score in scores.items():
            base_item = chunk_map[key]
            combined_method = "+".join(sorted(methods_map[key]))
            
            if isinstance(base_item, dict):
                content = base_item.get("content") or base_item.get("text", "")
                doc_id = base_item.get("document_id", key[0])
                c_idx = base_item.get("chunk_index", key[1])
                p_num = base_item.get("page_number") or base_item.get("page", 1)
                src_file = base_item.get("source_filename") or f"{doc_id}.pdf"
                circ_num = base_item.get("circular_number") or ""
            else:
                content = getattr(base_item, "content", "")
                doc_id = getattr(base_item, "document_id", key[0])
                c_idx = getattr(base_item, "chunk_index", key[1])
                p_num = getattr(base_item, "page_number", 1)
                src_file = getattr(base_item, "source_filename", f"{doc_id}.pdf")
                circ_num = getattr(base_item, "circular_number", "")

            fused_chunk = RetrievedChunk(
                content=content,
                document_id=doc_id,
                chunk_index=c_idx,
                page_number=p_num,
                source_filename=src_file,
                circular_number=circ_num,
                score=total_score,
                retrieval_method=combined_method
            )
            fused_chunks.append(fused_chunk)

        fused_chunks.sort(key=lambda x: x.score, reverse=True)
        return fused_chunks

    def retrieve(
        self,
        question: str,
        top_k: int = 5,
        use_vector: bool = True,
        use_bm25: bool = True,
        use_graph: bool = True
    ) -> List[RetrievedChunk]:
        """Run candidate retrieval, RRF fusion, and Cross-Encoder re-ranking."""
        ranked_lists = []

        if use_vector:
            v_chunks = self.vector_searcher.search(question, top_k=20)
            if v_chunks:
                ranked_lists.append(v_chunks)

        if use_bm25:
            b_chunks = self.bm25_searcher.search(question, top_k=20)
            if b_chunks:
                ranked_lists.append(b_chunks)

        if use_graph:
            g_chunks = self.graph_searcher.search(question, top_k=20)
            if g_chunks:
                # If g_chunks are dicts, map them to RetrievedChunk
                mapped_g = []
                for item in g_chunks:
                    if isinstance(item, RetrievedChunk):
                        mapped_g.append(item)
                    elif isinstance(item, dict):
                        mapped_g.append(RetrievedChunk(
                            content=item.get("text") or item.get("content") or f"Circulaire {item.get('related_circular')}",
                            document_id=str(item.get("document_id") or item.get("related_circular")),
                            chunk_index=int(item.get("chunk_index", 0)),
                            page_number=int(item.get("page", 1)),
                            source_filename=str(item.get("source_filename", "graph")),
                            circular_number=str(item.get("related_circular", "")),
                            score=float(item.get("score", 0.5)),
                            retrieval_method="graph"
                        ))
                if mapped_g:
                    ranked_lists.append(mapped_g)

        if not ranked_lists:
            return []

        # RRF Fusion
        fused = self._reciprocal_rank_fusion(ranked_lists)
        top_candidates = fused[:20]

        # Re-ranking
        if self.reranker:
            return self.reranker.rerank(question, top_candidates, top_k=top_k)

        return top_candidates[:top_k]

    def close(self):
        if hasattr(self.graph_searcher, "close"):
            self.graph_searcher.close()