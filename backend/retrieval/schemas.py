from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class RetrievedChunk:
    """A single chunk returned from any retrieval method."""
    content: str
    document_id: str
    chunk_index: int
    page_number: int
    source_filename: str
    circular_number: Optional[str]
    score: float  # Normalized score (0.0-1.0)
    retrieval_method: str  # "vector", "bm25", "graph"
    
@dataclass
class RetrievalResult:
    """Complete result from hybrid retrieval."""
    chunks: List[RetrievedChunk]
    query: str
    vector_count: int
    bm25_count: int
    graph_count: int
    fusion_method: str  # "rrf"
    reranked: bool
