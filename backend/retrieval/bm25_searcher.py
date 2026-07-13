from typing import List
import pickle
from pathlib import Path
from backend.retrieval.schemas import RetrievedChunk

class BM25Searcher:
    """
    BM25 keyword search over the persisted index.
    Loads index from backend/data/bm25_index.pkl.
    """

    def __init__(
        self,
        index_path: str = "backend/data/bm25_index.pkl",
    ) -> None:
        self.index_path = index_path
        self.corpus = []
        self.chunks = []
        self.bm25 = None
        self.reload_index()

    def search(
        self,
        query: str,
        top_k: int = 10,
    ) -> List[RetrievedChunk]:
        """
        Tokenize query (whitespace + lowercase), run BM25Okapi.get_scores(),
        return top-k chunks with normalized BM25 scores.
        """
        if not self.bm25 or not self.chunks:
            return []

        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        
        # Zip and sort by score descending
        scored_chunks = list(zip(self.chunks, scores))
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        
        # Take top_k
        top_chunks = scored_chunks[:top_k]
        
        # Max score for normalization
        max_score = max(scores) if len(scores) > 0 else 0.0
        
        retrieved = []
        for chunk, score in top_chunks:
            # Only include if score > 0 (or include anyway up to top_k, but score=0 means no keyword match)
            # Actually, standard RAG includes them but they get score 0.0. Let's include up to top_k.
            normalized_score = (score / max_score) if max_score > 0.0 else 0.0
            
            retrieved.append(RetrievedChunk(
                content=chunk.get("content", ""),
                document_id=chunk.get("document_id", ""),
                chunk_index=int(chunk.get("chunk_index", 0)),
                page_number=int(chunk.get("page_number", 1)),
                source_filename=chunk.get("source_filename", ""),
                circular_number=chunk.get("circular_number"),
                score=normalized_score,
                retrieval_method="bm25"
            ))
            
        return retrieved

    def reload_index(self) -> None:
        """Reload the BM25 index from disk (call after new documents are processed)."""
        if Path(self.index_path).exists():
            try:
                with open(self.index_path, "rb") as f:
                    data = pickle.load(f)
                self.corpus = data.get("corpus", [])
                self.chunks = data.get("chunks", [])
                self.bm25 = data.get("bm25")
            except Exception:
                self.corpus = []
                self.chunks = []
                self.bm25 = None
        else:
            self.corpus = []
            self.chunks = []
            self.bm25 = None
