from dataclasses import dataclass, field
from typing import Optional, List, Any

@dataclass
class SearchResult:
    """Single result item returned by any search channel."""
    chunk_id: str = ""
    content: str = ""
    score: float = 0.0
    metadata: dict = field(default_factory=dict)
    source: str = ""


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
    chunks: List[RetrievedChunk] = field(default_factory=list)
    query: str = ""
    vector_count: int = 0
    bm25_count: int = 0
    graph_count: int = 0
    fusion_method: str = "rrf"
    reranked: bool = False
    results: List[Any] = field(default_factory=list)
    total_candidates: int = 0
    channels_used: int = 0
    unique_sources: int = 0
    graph_used: bool = False
    obligation_used: bool = False
