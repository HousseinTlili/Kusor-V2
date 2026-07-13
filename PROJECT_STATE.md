# KUSOR — Project Setup & Current State Report

This document summarizes the current implementation state, dependencies installed, configuration details, and verification test results for **KUSOR** (AI-Powered Regulatory Intelligence Assistant).

---

## 1. Project Overview & Architecture

KUSOR is built to allow Banque Centrale de Tunisie (BCT) compliance staff to query regulatory circulars using natural language. It integrates three storage engines and a multi-stage retrieval/agentic generation pipeline:

- **Frontend**: Angular 21 (Standalone, SCSS, ngx-graph)
- **Backend Framework**: Flask + Flask-RESTX (OpenAPI/Swagger docs at `/api/docs`)
- **Metadata DB**: PostgreSQL 16 (via SQLAlchemy & Alembic migrations)
- **Vector Search**: ChromaDB 1.5 (Port `8001`, `kusor_documents` collection)
- **Knowledge Graph**: Neo4j 5.18 (Port `7474`/`7687`, APOC enabled)
- **Agent Orchestrator**: LangGraph
- **Models**:
  - LLM: `qwen2.5:7b` (via local Ollama)
  - Embedding: `nomic-embed-text` (via local Ollama)
  - Reranker: `cross-encoder/ms-marco-MiniLM-L-6-v2` (loaded via SentenceTransformers)

---

## 2. Infrastructure Setup & Tasks Done

We completed **Phase 0 (Infrastructure Setup)** on Ubuntu 22.04 LTS:

### System Dependencies Installed:
- **Python 3.11**: Installed system package via deadsnakes PPA to replace the broken Python 3.12 symbolic links.
- **Tesseract OCR**: Installed `tesseract-ocr` and French langpack `tesseract-ocr-fra` for scanned PDF text extraction fallbacks.
- **Docker & Docker Compose**: Installed Docker Engine and configured group permissions.
- **Ollama**: Installed Ollama locally and successfully pulled:
  - `qwen2.5:7b`
  - `nomic-embed-text`
- **Node.js**: Installed NVM, Node.js v20, and global `@angular/cli`.

### Environment Configuration:
- Created and activated Python 3.11 virtual environment (`backend/.venv`).
- Installed all python packages (Flask, LangChain, LangGraph, PyMuPDF, sentence-transformers, SQLAlchemy, psycopg2-binary, spacy, etc.).
- Downloaded French spaCy language package `fr_core_news_lg`.
- Generated cryptographically secure hex keys for `SECRET_KEY` and `JWT_SECRET_KEY` in `backend/.env`.
- Added missing keys to `backend/.env` (paths, models, scheduling configs).

### Database Initialization:
- **PostgreSQL**: Ran Alembic migrations (`flask db upgrade`) to set up the DB schemas (tables: `documents`, `chunks`, `users`, `conversation_sessions`, `conversation_messages`, `audit_logs`).
- **Neo4j**: Ran a custom script (`backend/scripts/init_neo4j.py`) to create constraints (e.g. unique circular numbers) and node property indexes.
- **Admin Setup**: Created initial administrator user:
  - **Username**: `admin`
  - **Password**: `admin123`

---

## 3. Implementation Verification & Unit Tests

All implementation modules were verified by executing the project unit tests in the activated python environment:

```bash
python -m pytest backend/ -v --tb=short
```

### Test Results Breakdown:
- **Module 3 (Document Processing Pipeline)**: `7/7 PASSED`
  - Structural pre-segmentation boundaries (Articles/Chapitres) correctly isolated.
  - OCR fallback triggered on image-only pages.
  - Semantic chunking with nomic embeddings stored successfully in ChromaDB.
  - spaCy French NER correctly extracted `LAW` and `ORG` entities.
- **Module 4 (GraphRAG Knowledge Graph)**: `7/7 PASSED`
  - Unique Circular/Entity constraints prevent duplicates on re-merge.
  - Abrogations correctly set status of past circulars to `ABROGATED`.
  - Regex and LLM relationship extraction pipelines verified.
  - Subgraph extraction for Angular visualization formatted properly.
- **Module 5 (Hybrid RAG Search Engine)**: `6/6 PASSED`
  - Vector, BM25, and Graph-based retrievers work concurrently.
  - Reciprocal Rank Fusion (RRF) rank-based scoring verified.
  - Cross-Encoder reranker re-scored top candidate chunks accurately.
- **Module 6 (LangGraph AI Agent)**: `8/8 PASSED`
  - LLM-based question classification and routing strategy functioning.
  - Structured AgentResponse schema output validation and citation enforcement verified.
- **Module 1 (BCT Scraper/Collector)**: `5/5 PASSED`
  - Web scraping parser correctly gathers circular metadata.
  - Scheduler successfully integrates with APScheduler.

**Total Status**: **`33/33 Tests Passed`** (100% success rate).

---

## 4. Run State & Live Services

Both application services have been started and are running in the background:

### Backend REST API:
- **Command**: `flask run --port 5000`
- **Swagger Docs URL**: [http://localhost:5000/api/docs](http://localhost:5000/api/docs)
- Exposes namespace endpoints for Authentication, Documents, Chat, Search, Admin Stats, and Knowledge Graph.

### Frontend Standalone App:
- **Command**: `npm run start` (ngx-graph, Auth0-JWT, standalone components)
- **Local URL**: [http://localhost:4200](http://localhost:4200)
- Configured with dark theme, SCSS styles, and responsive CSS variables.

You can log in to the dashboard at `http://localhost:4200` using:
- **Username**: `admin`
- **Password**: `admin123`
