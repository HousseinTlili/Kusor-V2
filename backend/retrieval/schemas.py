# backend/retrieval/schemas.py
"""Data classes for multi-channel retrieval results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SearchResult:
    """Single result item returned by any search channel."""
    chunk_id: str
    content: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = ""  # "vector" | "bm25" | "graph" | "obligation"


@dataclass
class RetrievalResult:
    """Aggregated output of the 4-channel retrieval engine."""
    results: List[SearchResult]
    total_candidates: int = 0
    channels_used: int = 0
    unique_sources: int = 0
    graph_used: bool = False
    obligation_used: bool = False
