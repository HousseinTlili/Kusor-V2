# KUSOR — AI-Powered Regulatory Intelligence Assistant

KUSOR is an AI-powered compliance assistant designed to allow regulatory and compliance staff (specifically for the Banque Centrale de Tunisie - BCT) to query regulatory circulars using natural language. 

The system leverages **GraphRAG** (a Neo4j knowledge graph mapping inter-circular relationships), **Hybrid RAG** (combining Vector, BM25, and Graph-based retrievers using Reciprocal Rank Fusion and Cross-Encoder reranking), and a **LangGraph agentic layer** to orchestrate query classification and execution.

---

## 1. Project Architecture & Technologies

### Seven-Layer Architecture
```
┌──────────────────────────────────────────────────────────┐
│  Layer 7: Angular Frontend (kusor-ui)                    │
├──────────────────────────────────────────────────────────┤
│  Layer 6: Flask REST API (Flask-RESTX + Swagger)         │
├──────────────────────────────────────────────────────────┤
│  Layer 5: LangGraph AI Agent (question classification,   │
│           tool selection, answer generation)              │
├──────────────────────────────────────────────────────────┤
│  Layer 4: Hybrid RAG Engine (RRF fusion + reranker)      │
├──────────────────────────────────────────────────────────┤
│  Layer 3: GraphRAG Knowledge Graph (Neo4j)               │
├──────────────────────────────────────────────────────────┤
│  Layer 2: Document Pre-Processing Pipeline               │
├──────────────────────────────────────────────────────────┤
│  Layer 1: BCT Circular Collector (scraper + scheduler)   │
└──────────────────────────────────────────────────────────┘
```

### Core Technologies
- **Frontend**: Angular 21 (Standalone, SCSS, ngx-graph)
- **Backend Framework**: Flask + Flask-RESTX (OpenAPI/Swagger docs exposed at `/api/docs`)
- **Metadata Database**: PostgreSQL 16 (via SQLAlchemy & Alembic migrations)
- **Vector Search**: ChromaDB 1.5 (Running on port `8001`, `kusor_documents` collection)
- **Knowledge Graph**: Neo4j 5.18 (Running on port `7474` / `7687`, APOC enabled)
- **Agent Orchestrator**: LangGraph
- **Models**:
  - LLM: `qwen2.5:7b` (via local Ollama)
  - Embedding: `nomic-embed-text` (via local Ollama)
  - Reranker: `cross-encoder/ms-marco-MiniLM-L-6-v2` (loaded via SentenceTransformers)
- **OCR Engine**: Tesseract OCR (with French language pack fallback for scanned PDFs)

---

## 2. Prerequisites

Ensure you have the following installed on your system:
- **Python 3.11**
- **Node.js (v20)** & **npm**
- **Docker & Docker Compose**
- **Ollama** (locally serving `qwen2.5:7b` and `nomic-embed-text`)
- **Tesseract OCR** (specifically the French package: `tesseract-ocr` and `tesseract-ocr-fra`)

---

## 3. Getting Started

### Step 1: Start Infrastructure (Docker Databases)
All databases run inside Docker containers. Start them by navigating to the `docker/` directory and running:
```bash
cd docker
docker compose up -d
```
This spins up:
- **Neo4j** (bolt://localhost:7687)
- **ChromaDB** (http://localhost:8001)
- **PostgreSQL** (postgresql://kusor_user:kusor_password@localhost:5432/kusor_db)

### Step 2: Set Up the Backend
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt   # If present, or install dependencies manually
   pip install spacy
   python -m spacy download fr_core_news_lg
   ```
4. Set up the environment variables:
   Create a `.env` file in the `backend/` directory (see `backend/.env.example` if available, or base it on the values below):
   ```env
   FLASK_ENV=development
   SECRET_KEY=generate_a_random_key_here
   JWT_SECRET_KEY=generate_another_random_key_here
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=kusor_password
   CHROMA_HOST=localhost
   CHROMA_PORT=8001
   DATABASE_URL=postgresql://kusor_user:kusor_password@localhost:5432/kusor_db
   OLLAMA_BASE_URL=http://localhost:11434
   LLM_MODEL=qwen2.5:7b
   EMBEDDING_MODEL=nomic-embed-text
   ```

### Step 3: Initialize Databases & Admin User
With your virtual environment active in the `backend/` directory:
1. Run PostgreSQL database migrations:
   ```bash
   flask db upgrade
   ```
2. Initialize Neo4j graph constraints and indexes:
   ```bash
   python scripts/init_neo4j.py
   ```
3. Create the default administrator user:
   The database setup will automatically provision the default admin user:
   - **Username**: `admin`
   - **Password**: `admin123`

### Step 4: Set Up the Frontend
1. Navigate to the frontend UI project:
   ```bash
   cd frontend/kusor-ui
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```

---

## 4. Running the Application

### Running the Backend REST API
From the `backend/` directory with active venv:
```bash
flask run --port 5000
```
- Swagger API Documentation is accessible at [http://localhost:5000/api/docs](http://localhost:5000/api/docs).

### Running the Frontend
From the `frontend/kusor-ui/` directory:
```bash
npm run start
# Or using Angular CLI:
ng serve
```
- The local UI is served at [http://localhost:4200](http://localhost:4200).

---

## 5. Running Tests

To verify all components (Document Processing, GraphRAG, Hybrid Search Engine, LangGraph Agent, and Scraper), execute pytest in the backend directory:
```bash
cd backend
source .venv/bin/activate
python -m pytest -v --tb=short
```
All unit tests should pass with a 100% success rate.
