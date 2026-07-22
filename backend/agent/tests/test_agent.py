# backend/agent/tests/test_agent.py
"""
Unit tests for main RAG Agent classification and confidence scoring.
"""

from backend.agent.agent_graph import classify_question, compute_confidence, resolve_point_in_time
from backend.agent.schemas import AgentState
from backend.retrieval.schemas import RetrievalResult, SearchResult


def test_question_classification():
    state: AgentState = {"question": "Quelles sont les obligations en date du 31/12/2023 ?"}
    classify_question(state)
    assert state["question_type"] == "point_in_time"


def test_point_in_time_resolution():
    state: AgentState = {"question": "Quelles étaient les règles au 2023-12-31 ?"}
    resolve_point_in_time(state)
    assert state["as_of_date"] == "2023-12-31"


def test_confidence_score_computation():
    state: AgentState = {
        "retrieval_result": RetrievalResult(
            results=[
                SearchResult(chunk_id="c1", content="Text 1", score=0.9, source="vector", metadata={"document_id": "doc1"}),
                SearchResult(chunk_id="c2", content="Text 2", score=0.8, source="graph", metadata={"circular_reference": "2024-01"}),
            ],
            total_candidates=15,
            channels_used=3,
            unique_sources=2,
            graph_used=True,
            obligation_used=False,
        )
    }
    compute_confidence(state)
    assert state["confidence_score"] > 0.6
