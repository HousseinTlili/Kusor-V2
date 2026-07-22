# backend/agent/agent_graph.py
"""
LangGraph agent for KUSOR v3 — orchestrates 4-channel retrieval, point-in-time
temporal resolution, memory persistence, and signal-based confidence scoring.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END

from backend.agent.prompts import SYSTEM_PROMPT
from backend.agent.schemas import AgentState
from backend.config import Config
from backend.graph.graphiti_manager import GraphitiMemoryManager
from backend.retrieval.hybrid_retriever import HybridRetriever

logger = logging.getLogger(__name__)


def classify_question(state: AgentState, llm: Optional[ChatOllama] = None) -> AgentState:
    q = state["question"]
    q_lower = q.lower()

    if any(kw in q_lower for kw in ["au", "en date du", "à la date", "qu'en était-il le"]):
        state["question_type"] = "point_in_time"
    elif any(kw in q_lower for kw in ["impact", "propagation", "conséquence", "processus affecté"]):
        state["question_type"] = "propagation"
    elif any(kw in q_lower for kw in ["relation", "lien", "entre", "rapport", "connecté"]):
        state["question_type"] = "relational"
    elif any(kw in q_lower for kw in ["comparer", "différence", "versus", "vs"]):
        state["question_type"] = "comparative"
    elif any(kw in q_lower for kw in ["quand", "depuis", "historique", "évolution"]):
        state["question_type"] = "temporal"
    else:
        state["question_type"] = "factual"

    logger.info("Question classified as: %s", state["question_type"])
    return state


def resolve_point_in_time(state: AgentState) -> AgentState:
    q = state["question"]
    date_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", q)
    if not date_match:
        date_match = re.search(r"\b(\d{1,2}/\d{1,2}/\d{4})\b", q)

    if date_match:
        raw_date = date_match.group(1)
        if "/" in raw_date:
            d, m, y = raw_date.split("/")
            state["as_of_date"] = f"{y}-{int(m):02d}-{int(d):02d}"
        else:
            state["as_of_date"] = raw_date
        logger.info("Resolved point-in-time date: %s", state["as_of_date"])
    else:
        state["as_of_date"] = datetime.now().strftime("%Y-%m-%d")
    return state


def recall_past_facts(state: AgentState, memory: Optional[GraphitiMemoryManager] = None) -> AgentState:
    if memory:
        facts = memory.retrieve_session_facts(state["question"], limit=3)
        state["past_facts"] = facts
    else:
        state["past_facts"] = []
    return state


def parallel_retrieve(state: AgentState, retriever: HybridRetriever) -> AgentState:
    res = retriever.retrieve(
        query=state["question"],
        question_type=state.get("question_type", "factual"),
        as_of_date=state.get("as_of_date"),
    )
    state["retrieval_result"] = res
    state["reranked_chunks"] = [
        {
            "chunk_id": r.chunk_id,
            "content": r.content,
            "score": r.score,
            "source": r.source,
            "metadata": r.metadata,
        }
        for r in res.results
    ]
    return state


def generate_answer(state: AgentState, llm: Optional[ChatOllama] = None) -> AgentState:
    chunks = state.get("reranked_chunks", [])
    if not chunks:
        state["answer"] = "Je n'ai pas trouvé d'informations pertinentes dans la réglementation pour répondre."
        state["sources"] = []
        return state

    context_parts = []
    sources = []
    for i, c in enumerate(chunks, 1):
        context_parts.append(f"[Source {i}] {c['content']}")
        sources.append({
            "chunk_id": c["chunk_id"],
            "content": c["content"][:200],
            "score": round(c["score"], 4),
            "source": c["source"],
            "metadata": c["metadata"],
        })

    facts = state.get("past_facts", [])
    facts_block = ""
    if facts:
        facts_block = "\nFaits connus des sessions précédentes:\n" + "\n".join([f"- {f['fact']}" for f in facts])

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"{facts_block}\n\n"
        f"Contexte Récupéré (4 canaux):\n" + "\n\n".join(context_parts) + "\n\n"
        f"Question: {state['question']}"
    )

    if llm:
        try:
            resp = llm.invoke([HumanMessage(content=prompt)])
            state["answer"] = resp.content
            state["sources"] = sources
        except Exception as e:
            logger.exception("LLM generation error")
            state["answer"] = "Erreur lors de la génération de la réponse."
            state["error"] = str(e)
    else:
        state["answer"] = f"Réponse basée sur {len(chunks)} source(s):\n\n" + "\n\n".join([c["content"] for c in chunks[:2]])
        state["sources"] = sources

    return state


def compute_confidence(state: AgentState) -> AgentState:
    rr = state.get("retrieval_result")
    if not rr or not rr.results:
        state["confidence_score"] = 0.0
        return state

    top_score = max(r.score for r in rr.results) if rr.results else 0.0
    top_norm = min(max(top_score, 0.0), 1.0)
    source_cov = min(rr.unique_sources / 3.0, 1.0)
    method_div = rr.channels_used / 4.0
    chunk_suf = min(rr.total_candidates / 10.0, 1.0)
    graph_bonus = 1.0 if (rr.graph_used or rr.obligation_used) else 0.0

    confidence = (
        top_norm * 0.35
        + source_cov * 0.25
        + method_div * 0.20
        + chunk_suf * 0.10
        + graph_bonus * 0.10
    )
    state["confidence_score"] = round(min(confidence, 1.0), 4)
    return state


def persist_fact_memory(state: AgentState, memory: Optional[GraphitiMemoryManager] = None) -> AgentState:
    sid = state.get("session_id")
    if sid and state.get("answer") and memory:
        memory.add_conversation_turn(sid, state["question"], state["answer"])
    return state


def build_main_agent_graph(
    retriever: HybridRetriever,
    memory: Optional[GraphitiMemoryManager] = None,
    config: Optional[Config] = None,
):
    cfg = config or Config()
    try:
        llm = ChatOllama(
            model=cfg.LLM_MODEL,
            base_url=cfg.OLLAMA_BASE_URL,
            temperature=0.1,
        )
    except Exception:
        llm = None

    graph = StateGraph(AgentState)

    graph.add_node("classify_question", lambda s: classify_question(s, llm))
    graph.add_node("resolve_point_in_time", resolve_point_in_time)
    graph.add_node("recall_past_facts", lambda s: recall_past_facts(s, memory))
    graph.add_node("parallel_retrieve", lambda s: parallel_retrieve(s, retriever))
    graph.add_node("generate_answer", lambda s: generate_answer(s, llm))
    graph.add_node("compute_confidence", compute_confidence)
    graph.add_node("persist_fact_memory", lambda s: persist_fact_memory(s, memory))

    graph.set_entry_point("classify_question")

    def route_after_classification(state: AgentState) -> str:
        return "resolve_point_in_time" if state.get("question_type") == "point_in_time" else "recall_past_facts"

    graph.add_conditional_edges(
        "classify_question",
        route_after_classification,
        {"resolve_point_in_time": "resolve_point_in_time", "recall_past_facts": "recall_past_facts"},
    )
    graph.add_edge("resolve_point_in_time", "recall_past_facts")
    graph.add_edge("recall_past_facts", "parallel_retrieve")
    graph.add_edge("parallel_retrieve", "generate_answer")
    graph.add_edge("generate_answer", "compute_confidence")
    graph.add_edge("compute_confidence", "persist_fact_memory")
    graph.add_edge("persist_fact_memory", END)

    return graph.compile()
