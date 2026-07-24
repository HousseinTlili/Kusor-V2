from typing import List
import math
from sentence_transformers import CrossEncoder
from backend.retrieval.schemas import RetrievedChunk

class CrossEncoderReranker:
    """
    Re-ranks chunks using cross-encoder/ms-marco-MiniLM-L-6-v2.
    Takes (query, chunk_content) pairs and produces relevance scores.
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    ) -> None:
        self.model = CrossEncoder(model_name)

    def rerank(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        top_k: int = 5,
    ) -> List[RetrievedChunk]:
        """
        Re-score each chunk against the query using the cross-encoder.
        Input: top-20 RRF-fused chunks.
        Output: top-5 chunks, re-scored and re-sorted.
        Updates each chunk's score with the cross-encoder score.
        """
        if not chunks:
            return []

        pairs = [(query, chunk.content) for chunk in chunks]
        scores = self.model.predict(pairs)
        
        for chunk, score in zip(chunks, scores):
            try:
                s_val = float(score)
                # Clip score to prevent overflow in math.exp
                s_val = max(-100.0, min(100.0, s_val))
                normalized_score = 1.0 / (1.0 + math.exp(-s_val))
            except Exception:
                normalized_score = float(score)
            
            chunk.score = normalized_score
            
        # Sort chunks by score descending
        chunks.sort(key=lambda x: x.score, reverse=True)
        
        return chunks[:top_k]
