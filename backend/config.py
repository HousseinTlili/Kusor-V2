# backend/config.py
"""
Configuration settings for KUSOR v3 application.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class."""
    
    # ── Flask & Security ─────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("FLASK_DEBUG", "1").lower() in ("1", "true", "yes")

    # ── JWT Settings ─────────────────────────────────────
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 604800))
    )

    # ── Database (PostgreSQL) ────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "postgresql://kusor_user:kusor_password@localhost:5432/kusor_db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # ── Neo4j Graph DB ───────────────────────────────────
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "kusor_password")

    # ── ChromaDB Vector DB ───────────────────────────────
    CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
    CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8001))
    CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "kusor_v3_docs")

    # ── Ollama Local LLM & Embedding ─────────────────────
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:7b")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

    # ── BCT Scraper ──────────────────────────────────────
    BCT_BASE_URL = os.getenv("BCT_BASE_URL", "https://www.bct.gov.tn")
    BCT_CIRCULARS_URL = os.getenv(
        "BCT_CIRCULARS_URL",
        "https://www.bct.gov.tn/bct/siteprod/tableau_circulaires.jsp",
    )
    SCRAPE_INTERVAL_HOURS = int(os.getenv("SCRAPE_INTERVAL_HOURS", 24))

    # ── File Storage ─────────────────────────────────────
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "backend/data/uploads")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 52428800))  # 50 MB

    # ── Index & Data Paths ───────────────────────────────
    BM25_INDEX_PATH = os.getenv("BM25_INDEX_PATH", "backend/data/bm25_index.pkl")
    SANCTIONS_DIR = os.getenv("SANCTIONS_DIR", "backend/data/sanctions")

    # ── Logging ──────────────────────────────────────────
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
