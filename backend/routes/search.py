# backend/routes/search.py
"""Search endpoints: /search/hybrid, /search/classic, /search/vector, /search/graph."""

from flask import request
from flask_jwt_extended import jwt_required
from flask_restx import Namespace, Resource

from backend.extensions import (
    get_hybrid_retriever,
    get_bm25_searcher,
    get_vector_searcher,
    get_graph_searcher,
)

ns = Namespace("search", description="Multi-channel search operations")


@ns.route("/hybrid")
class HybridSearch(Resource):
    @jwt_required()
    def post(self):
        """4-Channel Hybrid RAG Search (Vector + BM25 + Graph + Obligation with RRF)."""
        data = request.get_json() or {}
        query = data.get("query", "")
        if not query:
            return {"error": "Paramètre 'query' requis"}, 400

        retriever = get_hybrid_retriever()
        res = retriever.retrieve(
            query=query,
            question_type=data.get("question_type", "factual"),
            as_of_date=data.get("as_of_date"),
        )

        return {
            "query": query,
            "total_candidates": res.total_candidates,
            "channels_used": res.channels_used,
            "graph_used": res.graph_used,
            "obligation_used": res.obligation_used,
            "results": [
                {
                    "chunk_id": r.chunk_id,
                    "content": r.content,
                    "score": round(r.score, 4),
                    "source": r.source,
                    "metadata": r.metadata,
                }
                for r in res.results
            ],
        }, 200


@ns.route("/classic")
class ClassicSearch(Resource):
    @jwt_required()
    def post(self):
        """BM25 Keyword Search."""
        data = request.get_json() or {}
        query = data.get("query", "")
        bm25 = get_bm25_searcher()
        results = bm25.search(query, top_k=data.get("top_k", 10))
        return {
            "results": [
                {"chunk_id": r.chunk_id, "content": r.content, "score": round(r.score, 4)}
                for r in results
            ]
        }, 200


@ns.route("/vector")
class VectorSearch(Resource):
    @jwt_required()
    def post(self):
        """ChromaDB Vector Search."""
        data = request.get_json() or {}
        query = data.get("query", "")
        vector = get_vector_searcher()
        results = vector.search(query, top_k=data.get("top_k", 10))
        return {
            "results": [
                {"chunk_id": r.chunk_id, "content": r.content, "score": round(r.score, 4)}
                for r in results
            ]
        }, 200


@ns.route("/graph")
class GraphSearch(Resource):
    @jwt_required()
    def post(self):
        """Neo4j Temporal Graph Search."""
        data = request.get_json() or {}
        query = data.get("query", "")
        graph = get_graph_searcher()
        results = graph.search(query, top_k=data.get("top_k", 10), as_of_date=data.get("as_of_date"))
        return {
            "results": [
                {"chunk_id": r.chunk_id, "content": r.content, "score": round(r.score, 4)}
                for r in results
            ]
        }, 200
