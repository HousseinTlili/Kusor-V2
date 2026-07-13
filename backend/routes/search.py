"""Search namespace: hybrid, vector-only, graph-only."""
from flask import request, current_app
from flask_restx import Namespace, Resource, fields, abort
from flask_jwt_extended import jwt_required

api = Namespace("search", description="Search operations")

# RESTX Models for Swagger
search_request = api.model("SearchRequest", {
    "query": fields.String(required=True, description="The search query or question"),
    "top_k": fields.Integer(default=5, description="Number of results to return"),
})

chunk_response = api.model("SearchChunkResponse", {
    "content": fields.String(description="Text content of the chunk"),
    "document_id": fields.String(description="Document ID"),
    "chunk_index": fields.Integer(description="Index of the chunk in the document"),
    "page_number": fields.Integer(description="Page number in the source PDF"),
    "source_filename": fields.String(description="Source filename of the PDF"),
    "circular_number": fields.String(description="BCT circular number"),
    "score": fields.Float(description="Relevance score"),
    "retrieval_method": fields.String(description="Retrieval strategy used (vector, bm25, graph, hybrid)"),
})

@api.route("/hybrid")
class HybridSearch(Resource):
    @api.doc("hybrid_search", security="Bearer")
    @jwt_required()
    @api.expect(search_request, validate=True)
    @api.marshal_list_with(chunk_response)
    def post(self):
        """POST /api/search/hybrid — full hybrid search (vector + BM25 + graph + reranker)"""
        data = request.json
        query = data.get("query")
        top_k = data.get("top_k", 5)
        
        try:
            chunks = current_app.hybrid_retriever.retrieve(
                question=query,
                top_k=top_k,
                use_vector=True,
                use_bm25=True,
                use_graph=True
            )
            
            # Map retrieved chunks to dict format
            from backend.agent.tools import _chunk_to_dict
            return [_chunk_to_dict(c) for c in chunks]
        except Exception as e:
            abort(500, f"Hybrid search failed: {str(e)}")

@api.route("/vector")
class VectorSearch(Resource):
    @api.doc("vector_search", security="Bearer")
    @jwt_required()
    @api.expect(search_request, validate=True)
    @api.marshal_list_with(chunk_response)
    def post(self):
        """POST /api/search/vector — vector-only search"""
        data = request.json
        query = data.get("query")
        top_k = data.get("top_k", 5)
        
        try:
            chunks = current_app.hybrid_retriever.vector_searcher.search(
                query=query,
                top_k=top_k
            )
            
            # Map retrieved chunks to dict format
            from backend.agent.tools import _chunk_to_dict
            return [_chunk_to_dict(c) for c in chunks]
        except Exception as e:
            abort(500, f"Vector search failed: {str(e)}")

@api.route("/graph")
class GraphSearch(Resource):
    @api.doc("graph_search", security="Bearer")
    @jwt_required()
    @api.expect(search_request, validate=True)
    @api.marshal_list_with(chunk_response)
    def post(self):
        """POST /api/search/graph — graph-only search"""
        data = request.json
        query = data.get("query")
        top_k = data.get("top_k", 5)
        
        try:
            chunks = current_app.hybrid_retriever.graph_searcher.search(
                query=query,
                top_k=top_k
            )
            
            # Map retrieved chunks to dict format
            from backend.agent.tools import _chunk_to_dict
            return [_chunk_to_dict(c) for c in chunks]
        except Exception as e:
            abort(500, f"Graph search failed: {str(e)}")
