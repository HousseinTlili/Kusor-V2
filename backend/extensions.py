# backend/extensions.py
"""
Flask extensions and database singletons for KUSOR v3.
"""

import logging
from typing import Optional
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate

logger = logging.getLogger(__name__)

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()
migrate = Migrate()

# Singleton cache
_neo4j_manager = None
_chroma_collection = None
_bm25_searcher = None
_vector_searcher = None
_graph_searcher = None
_obligation_searcher = None
_reranker = None
_hybrid_retriever = None


def get_neo4j_manager():
    global _neo4j_manager
    if _neo4j_manager is None:
        from backend.config import Config
        from backend.graph.neo4j_manager import Neo4jManager
        cfg = Config()
        _neo4j_manager = Neo4jManager(cfg.NEO4J_URI, cfg.NEO4J_USER, cfg.NEO4J_PASSWORD)
    return _neo4j_manager


def get_chroma_collection():
    global _chroma_collection
    if _chroma_collection is None:
        import chromadb
        from backend.config import Config
        cfg = Config()
        client = chromadb.HttpClient(host=cfg.CHROMA_HOST, port=cfg.CHROMA_PORT)
        _chroma_collection = client.get_or_create_collection(cfg.CHROMA_COLLECTION)
    return _chroma_collection


def get_bm25_searcher():
    global _bm25_searcher
    if _bm25_searcher is None:
        from backend.retrieval.bm25_searcher import BM25Searcher
        _bm25_searcher = BM25Searcher()
    return _bm25_searcher


def get_vector_searcher():
    global _vector_searcher
    if _vector_searcher is None:
        from backend.retrieval.vector_searcher import VectorSearcher
        _vector_searcher = VectorSearcher(get_chroma_collection())
    return _vector_searcher


def get_graph_searcher():
    global _graph_searcher
    if _graph_searcher is None:
        from backend.retrieval.graph_searcher import GraphSearcher
        _graph_searcher = GraphSearcher(get_neo4j_manager())
    return _graph_searcher


def get_obligation_searcher():
    global _obligation_searcher
    if _obligation_searcher is None:
        from backend.retrieval.obligation_searcher import ObligationSearcher
        _obligation_searcher = ObligationSearcher(get_neo4j_manager())
    return _obligation_searcher


def get_reranker():
    global _reranker
    if _reranker is None:
        try:
            from backend.retrieval.reranker import Reranker
            _reranker = Reranker()
        except Exception as e:
            logger.warning("CrossEncoder Reranker failed to initialize: %s", e)
            _reranker = None
    return _reranker


def get_hybrid_retriever():
    global _hybrid_retriever
    if _hybrid_retriever is None:
        from backend.retrieval.hybrid_retriever import HybridRetriever
        _hybrid_retriever = HybridRetriever(
            vector_searcher=get_vector_searcher(),
            bm25_searcher=get_bm25_searcher(),
            graph_searcher=get_graph_searcher(),
            obligation_searcher=get_obligation_searcher(),
            reranker=get_reranker(),
        )
    return _hybrid_retriever
