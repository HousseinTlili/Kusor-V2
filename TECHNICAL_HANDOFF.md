# 🔧 KUSOR v3 — Complete Technical Handoff Document

> **Purpose**: This document contains every technical detail an AI agent or developer needs to understand, maintain, extend, and debug the KUSOR v3 codebase without guessing or re-discovering prior work.  
> **Last Updated**: August 14, 2026

---

## Table of Contents
1. [System Architecture & Service Topology](#1-system-architecture--service-topology)
2. [Environment Variables & Configuration](#2-environment-variables--configuration)
3. [PostgreSQL Database Schemas](#3-postgresql-database-schemas)
4. [Neo4j Knowledge Graph Topology](#4-neo4j-knowledge-graph-topology)
5. [ChromaDB Vector Store Schema](#5-chromadb-vector-store-schema)
6. [Complete REST API Reference (10 Namespaces)](#6-complete-rest-api-reference)
7. [Document Ingestion Pipeline (End-to-End Data Flow)](#7-document-ingestion-pipeline)
8. [4-Channel Hybrid Retrieval Architecture](#8-4-channel-hybrid-retrieval-architecture)
9. [LangGraph Agent State Machine](#9-langgraph-agent-state-machine)
10. [Specialized Banking Agents](#10-specialized-banking-agents)
11. [Multi-Source Scraping Engine](#11-multi-source-scraping-engine)
12. [Frontend Architecture (Angular 19)](#12-frontend-architecture)
13. [Authentication & Authorization Flow](#13-authentication--authorization-flow)
14. [Docker Compose Production Stack](#14-docker-compose-production-stack)
15. [Key Dependencies & Their Roles](#15-key-dependencies--their-roles)
16. [Design Decisions & Rationale](#16-design-decisions--rationale)
17. [Known Gotchas, Traps & Anti-Patterns](#17-known-gotchas-traps--anti-patterns)
18. [File Quick-Reference Index](#18-file-quick-reference-index)

---

## 1. System Architecture & Service Topology

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        KUSOR v3 SYSTEM ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────┐     HTTP/JSON      ┌──────────────────────────────┐     │
│   │  Angular 19  │◄──────────────────►│     Flask REST API           │     │
│   │  Frontend    │    :4200 ► :5000   │     (10 RESTX Namespaces)    │     │
│   │  (kusor-ui)  │                    │     + Swagger at /api/docs   │     │
│   └──────────────┘                    └──────────┬───────────────────┘     │
│                                                  │                         │
│                          ┌───────────────────────┼───────────────────────┐ │
│                          │                       │                       │ │
│                          ▼                       ▼                       ▼ │
│               ┌──────────────────┐   ┌─────────────────┐   ┌───────────┐ │
│               │   PostgreSQL 16  │   │   Neo4j 5        │   │ ChromaDB  │ │
│               │   :5432          │   │   Community      │   │ :8001     │ │
│               │                  │   │   :7687 (Bolt)   │   │           │ │
│               │  • documents     │   │   :7474 (HTTP)   │   │ Collection│ │
│               │  • chunks        │   │                  │   │ kusor_v3_ │ │
│               │  • users         │   │  • :Circular     │   │ docs      │ │
│               │  • audit_logs    │   │  • :Obligation   │   │           │ │
│               │  • impact_records│   │  • :Process      │   │ nomic-    │ │
│               │  • conversation_ │   │  • :Contract     │   │ embed-text│ │
│               │    sessions      │   │    Template      │   │ vectors   │ │
│               │  • conversation_ │   │                  │   │           │ │
│               │    messages      │   │  Temporal edges  │   │           │ │
│               └──────────────────┘   │  (valid_from/to) │   └───────────┘ │
│                                      └─────────────────┘                   │
│                          ┌───────────────────────┐                         │
│                          │   Ollama LLM Server   │                         │
│                          │   :11434              │                         │
│                          │                       │                         │
│                          │   Model: qwen2.5:7b   │                         │
│                          │   Embed: nomic-embed  │                         │
│                          │          -text         │                         │
│                          └───────────────────────┘                         │
│                                                                             │
│   ┌──────────────┐  (Optional)                                             │
│   │  n8n :5678   │  3 automation workflows                                │
│   │  Workflow    │  calling Flask REST API                                 │
│   │  Engine      │                                                         │
│   └──────────────┘                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Service Connection Map

| From | To | Protocol | Port | Purpose |
|------|----|----------|------|---------|
| Angular Frontend | Flask Backend | HTTP REST + SSE | 4200 → 5000 | All API calls (JWT Bearer auth) |
| Flask Backend | PostgreSQL | TCP (psycopg2) | → 5432 | Document/User/Audit CRUD |
| Flask Backend | Neo4j | Bolt Protocol | → 7687 | Cypher queries, graph traversal |
| Flask Backend | ChromaDB | HTTP | → 8001 | Vector similarity search |
| Flask Backend | Ollama | HTTP | → 11434 | LLM inference + embedding generation |
| n8n | Flask Backend | HTTP REST | 5678 → 5000 | Automated webhook triggers |

---

## 2. Environment Variables & Configuration

**File**: `backend/config.py` — Loaded via `python-dotenv` from `.env`

| Variable | Default | Type | Description |
|----------|---------|------|-------------|
| `SECRET_KEY` | `"dev-secret-key-change-in-production"` | str | Flask session signing key |
| `FLASK_ENV` | `"development"` | str | Flask environment mode |
| `FLASK_DEBUG` | `"1"` | bool | Debug mode (`"1"`, `"true"`, `"yes"` → True) |
| `JWT_SECRET_KEY` | `"dev-jwt-secret-key"` | str | JWT token signing secret |
| `JWT_ACCESS_TOKEN_EXPIRES` | `604800` | int→timedelta | Token expiry (7 days in seconds) |
| `DATABASE_URL` | `"postgresql://kusor_user:kusor_password@localhost:5432/kusor_db"` | str | PostgreSQL connection URI |
| `NEO4J_URI` | `"bolt://localhost:7687"` | str | Neo4j Bolt URI |
| `NEO4J_USER` | `"neo4j"` | str | Neo4j username |
| `NEO4J_PASSWORD` | `"kusor_password"` | str | Neo4j password |
| `CHROMA_HOST` | `"localhost"` | str | ChromaDB server host |
| `CHROMA_PORT` | `8001` | int | ChromaDB HTTP port |
| `CHROMA_COLLECTION` | `"kusor_v3_docs"` | str | ChromaDB collection name |
| `OLLAMA_BASE_URL` | `"http://localhost:11434"` | str | Ollama API base URL |
| `LLM_MODEL` | `"qwen2.5:7b"` | str | Primary LLM model name |
| `EMBEDDING_MODEL` | `"nomic-embed-text"` | str | Embedding model name |
| `BCT_BASE_URL` | `"https://www.bct.gov.tn"` | str | BCT portal base URL |
| `BCT_CIRCULARS_URL` | `"https://www.bct.gov.tn/bct/siteprod/tableau_circulaires.jsp"` | str | BCT circulars listing page |
| `SCRAPE_INTERVAL_HOURS` | `24` | int | Auto-scrape interval |
| `UPLOAD_FOLDER` | `"backend/data/uploads"` | str | PDF upload directory |
| `MAX_CONTENT_LENGTH` | `52428800` | int | Max upload size (50 MB) |
| `BM25_INDEX_PATH` | `"backend/data/bm25_index.pkl"` | str | BM25 index persistence path |
| `SANCTIONS_DIR` | `"backend/data/sanctions"` | str | Sanctions data directory |
| `LOG_LEVEL` | `"INFO"` | str | Python logging level |

---

## 3. PostgreSQL Database Schemas

### Table: `documents`
| Column | Type | Constraints | Default | Notes |
|--------|------|-------------|---------|-------|
| `id` | VARCHAR(36) | PRIMARY KEY | `uuid4()` | |
| `title` | TEXT | NOT NULL | | |
| `filename` | VARCHAR(255) | | | Original filename |
| `doc_type` | VARCHAR(50) | | `"circular"` | `circular \| note \| contract \| kyc_dossier \| credit_dossier` |
| `number` | VARCHAR(50) | UNIQUE, NULLABLE | | BCT circular number (e.g. `2024-01`) |
| `circular_reference` | VARCHAR(100) | NULLABLE | | v2 compatibility alias for `number` |
| `date_issued` | DATE | NULLABLE | | |
| `category` | VARCHAR(100) | NULLABLE | | |
| `source` | VARCHAR(100) | | `"BCT Portal"` | `BCT Portal \| OFAC \| EU Commission \| UN Security Council \| GAFI / FATF` |
| `source_url` | VARCHAR(500) | | | |
| `content_hash` | VARCHAR(64) | | | SHA-256 deduplication |
| `status` | VARCHAR(50) | | `"ACTIVE"` | `ACTIVE \| MODIFIED \| ABROGATED` |
| `indexation_state` | VARCHAR(50) | | `"PENDING"` | `PENDING \| PROCESSING \| INDEXED \| FAILED` |
| `language` | VARCHAR(10) | | `"fr"` | `fr \| ar \| fr-ar` |
| `raw_text` | TEXT | | | Full extracted text |
| `created_at` | DATETIME | | `now(utc)` | |
| `updated_at` | DATETIME | | `now(utc)` | Auto-updated on change |

### Table: `chunks`
| Column | Type | Constraints | Default | Notes |
|--------|------|-------------|---------|-------|
| `id` | VARCHAR(100) | PRIMARY KEY | `"{doc_id}_{idx}"` | |
| `document_id` | VARCHAR(36) | FK→documents.id, CASCADE | NOT NULL | |
| `content` | TEXT | NOT NULL | | Chunk text (≤800 words) |
| `section_title` | VARCHAR(300) | | | Structural section heading |
| `chunk_index` | INTEGER | NOT NULL | `0` | Position in document |
| `page_number` | INTEGER | NULLABLE | `1` | |
| `token_count` | INTEGER | | | Approximate word count |
| `embedding_id` | VARCHAR(255) | NULLABLE | | ChromaDB vector ID |
| `created_at` | DATETIME | | `now(utc)` | |

### Table: `users`
| Column | Type | Constraints | Default | Notes |
|--------|------|-------------|---------|-------|
| `id` | VARCHAR(36) | PRIMARY KEY | `uuid4()` | |
| `username` | VARCHAR(80) | UNIQUE, NOT NULL | | |
| `email` | VARCHAR(120) | UNIQUE, NOT NULL | | |
| `password_hash` | VARCHAR(255) | NOT NULL | | bcrypt hashed |
| `full_name` | VARCHAR(200) | | `""` | |
| `role` | VARCHAR(20) | NOT NULL | `"user"` | `admin \| compliance \| legal \| credit \| user` |
| `department` | VARCHAR(100) | NULLABLE | | |
| `is_active` | BOOLEAN | | `True` | |
| `created_at` | DATETIME | | `now(utc)` | |
| `updated_at` | DATETIME | | `now(utc)` | |

### Table: `audit_logs`
| Column | Type | Constraints | Default | Notes |
|--------|------|-------------|---------|-------|
| `id` | VARCHAR(36) | PRIMARY KEY | `uuid4()` | |
| `user_id` | VARCHAR(36) | FK→users.id, SET NULL | NULLABLE | |
| `action` | VARCHAR(100) | NOT NULL | | e.g. `DOCUMENT_UPLOADED`, `KYC_CHECK_RUN` |
| `entity_type` | VARCHAR(50) | | | `document \| chat \| kyc \| contract \| credit` |
| `entity_id` | VARCHAR(100) | | | |
| `endpoint` | VARCHAR(200) | | | `POST /api/chat/message` |
| `ip_address` | VARCHAR(45) | | | IPv4 or IPv6 |
| `input_hash` | VARCHAR(64) | NULLABLE | | SHA-256 of request body |
| `output_summary` | TEXT | NULLABLE | | First 500 chars of response |
| `details_json` | TEXT | NULLABLE | | Full JSON audit details |
| `created_at` | DATETIME | | `now(utc)` | |

### Table: `impact_records`
| Column | Type | Constraints | Default | Notes |
|--------|------|-------------|---------|-------|
| `id` | VARCHAR(36) | PRIMARY KEY | `uuid4()` | |
| `source_circular_id` | VARCHAR(36) | FK→documents.id, CASCADE, NOT NULL | | Triggering circular |
| `source_circular_ref` | VARCHAR(100) | NOT NULL | | e.g. `"2025-03"` |
| `affected_entity_type` | VARCHAR(50) | NOT NULL | | `obligation \| process \| contract_template \| circular` |
| `affected_entity_id` | VARCHAR(100) | NOT NULL | | Neo4j node ID |
| `affected_entity_name` | VARCHAR(500) | | | Human-readable name |
| `severity` | VARCHAR(20) | NOT NULL | | `LOW \| MEDIUM \| HIGH \| CRITICAL` |
| `impact_description` | TEXT | | | LLM-generated description |
| `relationship_path` | TEXT | | | JSON-serialized traversal path |
| `is_acknowledged` | BOOLEAN | | `False` | Officer reviewed? |
| `acknowledged_by` | VARCHAR(36) | NULLABLE | | |
| `acknowledged_at` | DATETIME | NULLABLE | | |
| `created_at` | DATETIME | | `now(utc)` | |

### Table: `conversation_sessions`
| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | VARCHAR(36) | PRIMARY KEY | `uuid4()` |
| `user_id` | VARCHAR(36) | FK→users.id, CASCADE, NOT NULL | |
| `title` | VARCHAR(255) | | `"Nouvelle conversation"` |
| `created_at` | DATETIME | | `now(utc)` |
| `updated_at` | DATETIME | | `now(utc)` |

### Table: `conversation_messages`
| Column | Type | Constraints | Default |
|--------|------|-------------|---------|
| `id` | VARCHAR(36) | PRIMARY KEY | `uuid4()` |
| `session_id` | VARCHAR(36) | FK→conversation_sessions.id, CASCADE, NOT NULL | |
| `role` | VARCHAR(20) | NOT NULL | | `user \| assistant` |
| `content` | TEXT | NOT NULL | |
| `sources_json` | TEXT | NULLABLE | | JSON-serialized source citations |
| `confidence` | FLOAT | NULLABLE | |
| `metadata_json` | JSON | | `{}` |
| `created_at` | DATETIME | | `now(utc)` |

---

## 4. Neo4j Knowledge Graph Topology

### Node Labels & Properties

| Label | Key Properties | Created By |
|-------|---------------|------------|
| `:Circular` | `reference` (unique), `title`, `document_id`, `date_issued`, `doc_type`, `status` | `graph_builder.py` during ingestion |
| `:Obligation` | `id` (e.g. `"ob_{doc_id}_{hex}"`), `text`, `obligation_type`, `circular_id`, `article_id`, `created_at` | `obligation_extractor.py` |
| `:Process` | `name` (e.g. `"Octroi de crédit"`, `"Ouverture de compte"`) | `seed_processes.py` (6 seeded) |
| `:ContractTemplate` | `name` (e.g. `"Convention de compte"`) | `seed_processes.py` (5 seeded) |

### Relationship Types

**ALL relationships carry temporal attributes**: `valid_from` (date) and `valid_until` (date | null)

| Pattern | Type | Meaning |
|---------|------|---------|
| `(:Circular)-[:INTRODUCES]->(:Obligation)` | Regulatory creation | Circular introduces a new obligation |
| `(:Obligation)-[:AFFECTS]->(:Process)` | Impact propagation | Obligation impacts a banking process |
| `(:Obligation)-[:CONSTRAINS]->(:ContractTemplate)` | Contract constraint | Obligation constrains a contract clause |
| `(:Circular)-[:AMENDS]->(:Circular)` | Modification | Source modifies target (sets `MODIFIED`) |
| `(:Circular)-[:REPLACES]->(:Circular)` | Abrogation | Source replaces target (sets `ABROGATED`, closes `valid_until`) |
| `(:Circular)-[:REFERENCES]->(:Circular)` | Cross-reference | Non-modifying citation link |

### Temporal Point-in-Time Query Pattern
```cypher
MATCH (c:Circular)-[r:INTRODUCES]->(o:Obligation)
WHERE r.valid_from <= date($as_of_date)
  AND (r.valid_until IS NULL OR r.valid_until >= date($as_of_date))
RETURN c, o
```

---

## 5. ChromaDB Vector Store Schema

| Property | Value |
|----------|-------|
| **Collection Name** | `kusor_v3_docs` |
| **Embedding Model** | `nomic-embed-text` (768 dimensions) |
| **Distance Metric** | Cosine (score = `1.0 - distance`) |
| **Current Count** | ~1,905 vectors |

### Per-Vector Metadata Fields
```json
{
  "document_id": "uuid-string",
  "title": "Circulaire BCT N° 2024-01",
  "circular_reference": "2024-01",
  "doc_type": "circular",
  "section_title": "Article 5 - Provisions",
  "chunk_index": 3
}
```

---

## 6. Complete REST API Reference

**Base URL**: `http://localhost:5000/api`  
**Auth**: JWT Bearer token in `Authorization` header (unless noted)  
**Swagger UI**: `http://localhost:5000/api/docs`

### 6.1 Auth (`/api/auth`)
| Method | Path | Auth | Request | Response |
|--------|------|------|---------|----------|
| POST | `/auth/login` | None | `{"username", "password"}` | `{"access_token", "user": {id, username, email, role, full_name, department}}` |
| POST | `/auth/register` | None | `{"username", "email", "password", "role", "full_name", "department"}` | `{"message", "access_token", "user"}` |
| GET | `/auth/me` | JWT | — | `{id, username, email, role, full_name, department, created_at}` |

### 6.2 Documents (`/api/documents`)
| Method | Path | Auth | Request | Response |
|--------|------|------|---------|----------|
| GET | `/documents/` | JWT | Query: `source`, `doc_type`, `status`, `indexation_state`, `search` | `[{id, title, filename, doc_type, source, circular_reference, date_issued, status, indexation_state, chunk_count, created_at}]` |
| POST | `/documents/` | JWT + Admin | Multipart: `file`, `title`, `doc_type`, `source`, `circular_reference` | `{message, document: {id, title, doc_type, source, circular_reference, indexation_state}}` |
| GET | `/documents/<id>` | JWT | — | `{id, title, ..., raw_text, chunks: [{id, section_title, content, chunk_index}]}` |
| PUT | `/documents/<id>` | JWT + Admin | `{"title"?, "circular_reference"?, "doc_type"?, "source"?, "status"?}` | `{message, document}` |
| DELETE | `/documents/<id>` | JWT + Admin | — | `{message}` |

### 6.3 Search (`/api/search`)
| Method | Path | Auth | Request | Response |
|--------|------|------|---------|----------|
| POST | `/search/hybrid` | JWT | `{"query", "question_type"?, "as_of_date"?}` | `{query, total_candidates, channels_used, results: [{chunk_id, content, score, source, metadata}]}` |
| POST | `/search/classic` | JWT | `{"query", "top_k"?}` | `{results: [{chunk_id, content, score}]}` |
| POST | `/search/vector` | JWT | `{"query", "top_k"?}` | `{results: [{chunk_id, content, score}]}` |
| POST | `/search/graph` | JWT | `{"query", "top_k"?, "as_of_date"?}` | `{results: [{chunk_id, content, score}]}` |

### 6.4 Chat (`/api/chat`)
| Method | Path | Auth | Request | Response |
|--------|------|------|---------|----------|
| POST | `/chat/message` | JWT | `{"message", "session_id"?, "stream"?}` | JSON: `{session_id, message, confidence_score, sources}` — OR SSE stream: `token`/`sources`/`done` events |
| GET | `/chat/sessions` | JWT | — | `[{id, title, created_at, updated_at}]` |
| GET | `/chat/sessions/<id>/history` | JWT | — | `[{id, role, content, confidence, sources, created_at}]` |

### 6.5 Graph (`/api/graph`)
| Method | Path | Auth | Request | Response |
|--------|------|------|---------|----------|
| GET | `/graph/overview` | JWT | — | `{node_counts: {Label: int}, relationship_counts: {Type: int}}` |
| GET | `/graph/subgraph` | JWT | Query: `label`, `limit` | `{records: [{n_id, n_labels, n_props, rel_type, m_id, m_labels, m_props}]}` |
| GET | `/graph/temporal` | JWT | Query: `as_of_date` | `{as_of_date, records: [...]}` |

### 6.6 KYC (`/api/kyc`)
| Method | Path | Auth | Response Schema |
|--------|------|------|----------------|
| POST | `/kyc/check` | JWT + compliance/admin | `KYCReport`: `{client_name, verdict, overall_risk, document_checks[], completeness_score, sanctions_results[], sanctions_hit, recommendations[]}` |

### 6.7 Contract (`/api/contract`)
| Method | Path | Auth | Response Schema |
|--------|------|------|----------------|
| POST | `/contract/analyze` | JWT + legal/admin | `ContractReport`: `{contract_title, total_clauses, clauses[{clause_type, conformity_status, severity, regulatory_basis_still_valid}], non_conformity_count, overall_risk}` |

### 6.8 Credit (`/api/credit`)
| Method | Path | Auth | Response Schema |
|--------|------|------|----------------|
| POST | `/credit/prescreen` | JWT + credit/admin | `CreditReport`: `{dossier_id, document_completeness, numerical_validation{debt_ratio, debt_ratio_compliant}, identity_cross_reference, overall_verdict: APPROVE\|REVIEW\|REJECT}` |

### 6.9 Impact (`/api/impact`)
| Method | Path | Auth | Response Schema |
|--------|------|------|----------------|
| GET | `/impact/<circular_id>` | JWT + compliance/admin | `ImpactPropagationReport`: `{source_circular_ref, total_affected, critical_count, high_count, affected_items[{entity_type, severity, impact_description, relationship_path}]}` |

### 6.10 Admin (`/api/admin`)
| Method | Path | Auth | Response |
|--------|------|------|----------|
| GET | `/admin/stats` | None | `{users_total, documents_total, circulars_total, sanctions_total, guidance_total, audit_logs_total, chromadb_vectors, neo4j_nodes, neo4j_relationships}` |
| POST | `/admin/sync` | None | `{status, message, totals, sources[{source_id, source_name, data_type, items_scraped, items_added}]}` |
| GET | `/admin/digest` | None | `{recent_activity: [{id, action, user_id, endpoint, timestamp}]}` |
| GET | `/admin/digest/generate` | None | `{digest_text, documents_count, critical_impacts, high_impacts}` |

---

## 7. Document Ingestion Pipeline

**File**: `backend/processing/document_processor.py`

```
┌───────────────────┐
│  1. FILE UPLOAD   │  PDF / DOCX / TXT received via POST /api/documents/
└────────┬──────────┘
         ▼
┌───────────────────┐
│  2. TEXT EXTRACT  │  PyMuPDF (fitz) for PDF, python-docx for DOCX
│                   │  OCR fallback: Tesseract (pytesseract) at 300 DPI
│                   │  if page text < 50 chars (scanned pages)
│                   │  Language: lang="fra" (French)
└────────┬──────────┘
         ▼
┌───────────────────┐
│  3. METADATA      │  Regex extraction:
│     EXTRACTION    │  • Circular ref: /[Cc]irculaire\s+[Nn]°?\s*(\d{4}-\d{1,2})/
│                   │  • Date: French month dict → ISO date
│                   │  • SHA-256 content hash (deduplication)
└────────┬──────────┘
         ▼
┌───────────────────┐
│  4. STRUCTURAL    │  Regex markers: Titre, Chapitre, Section, Article
│     SEGMENTATION  │  → Ordered list of (section_title, section_content)
│                   │  Preamble extracted separately if present
└────────┬──────────┘
         ▼
┌───────────────────┐
│  5. OVERLAPPING   │  Window: chunk_size=800 words, overlap=100 words
│     CHUNKING      │  ID format: "{doc_uuid}_{chunk_index}"
│                   │  Preserves section_title per chunk
└────────┬──────────┘
         ▼
┌─────────────────────────────────────────────────────────┐
│  6. PARALLEL TRIPLE WRITE                                │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │ PostgreSQL   │  │  ChromaDB    │  │  Neo4j         │ │
│  │             │  │              │  │                │ │
│  │ Document    │  │ nomic-embed  │  │ (:Circular)    │ │
│  │ + Chunk     │  │ -text vectors│  │ (:Obligation)  │ │
│  │ rows        │  │ + metadata   │  │ [:INTRODUCES]  │ │
│  └─────────────┘  └──────────────┘  └────────────────┘ │
└────────┬────────────────────────────────────────────────┘
         ▼
┌───────────────────┐
│  7. OBLIGATION    │  Regex patterns: PROHIBITION, REQUIREMENT,
│     EXTRACTION    │  THRESHOLD, DEADLINE
│                   │  Optional LLM pass via Instructor + ChatOllama
│                   │  Creates (:Obligation) nodes linked to (:Circular)
└────────┬──────────┘
         ▼
┌───────────────────┐
│  8. CHANGE        │  ChangePropagationAgent auto-invoked
│     PROPAGATION   │  Traverses graph → maps impacted Processes
│                   │  and ContractTemplates → writes ImpactRecord
│                   │  rows to PostgreSQL
└────────┬──────────┘
         ▼
┌───────────────────┐
│  9. FINALIZE      │  doc.indexation_state = "INDEXED"
│                   │  db.session.commit()
└───────────────────┘
```

---

## 8. 4-Channel Hybrid Retrieval Architecture

**File**: `backend/retrieval/hybrid_retriever.py`

### Channel Descriptions

| # | Channel | File | Engine | Scoring |
|---|---------|------|--------|---------|
| 1 | Vector | `vector_searcher.py` | ChromaDB nearest-neighbor (`nomic-embed-text`) | `1.0 - cosine_distance` |
| 2 | BM25 | `bm25_searcher.py` | Okapi BM25 keyword ranking (persisted `bm25_index.pkl`) | Normalized BM25 score |
| 3 | Graph | `graph_searcher.py` | spaCy NER entity extraction → Neo4j Cypher match | Temporal-filtered, scored by hop distance |
| 4 | Obligation | `obligation_searcher.py` | Cypher text search in `:Obligation` nodes, traverses `:Process` and `:ContractTemplate` | Match relevance scoring |

### Fusion: 4-Way Reciprocal Rank Fusion (RRF)

$$\text{RRF\_Score}(d) = \sum_{i=1}^{4} \frac{w_i}{k + \text{rank}_i(d)} \quad \text{where } k = 60$$

### Dynamic Weight Matrix by Question Type

| Question Type | Vector | BM25 | Graph | Obligation |
|---------------|--------|------|-------|------------|
| `factual` | 0.40 | 0.30 | 0.15 | 0.15 |
| `relational` | 0.20 | 0.15 | 0.45 | 0.20 |
| `temporal` | 0.25 | 0.15 | 0.40 | 0.20 |
| `point_in_time` | 0.20 | 0.15 | 0.45 | 0.20 |
| `propagation` | 0.15 | 0.15 | 0.35 | 0.35 |
| `comparative` | 0.35 | 0.25 | 0.25 | 0.15 |
| default | 0.35 | 0.25 | 0.25 | 0.15 |

### Reranking Stage

Top 20 RRF candidates → `Reranker` (CrossEncoder `cross-encoder/ms-marco-MiniLM-L-6-v2`) → Final top 5

---

## 9. LangGraph Agent State Machine

**File**: `backend/agent/agent_graph.py`

### AgentState Fields (TypedDict)
```python
{
    "question": str,
    "session_id": Optional[str],
    "chat_history": List[Dict],
    "question_type": str,        # factual|relational|temporal|comparative|propagation|point_in_time
    "as_of_date": Optional[str], # YYYY-MM-DD
    "retrieved_chunks": List,
    "recalled_facts": List,
    "answer": str,
    "citations": List[Dict],
    "confidence_score": float,   # 0.0 - 1.0
}
```

### Graph Node Execution Flow

```
[START]
   │
   ▼
┌─────────────────────┐
│  classify_question   │  Keyword-based classifier → sets question_type
└──────────┬──────────┘
           │
     ┌─────┴────────────────┐
     │ point_in_time?       │
     ▼ YES                  ▼ NO
┌──────────────────┐   ┌─────────────────┐
│resolve_point_in_ │   │ recall_past_    │
│time              │   │ facts           │
│(extract date)    │   │(Graphiti memory)│
└────────┬─────────┘   └────────┬────────┘
         │                      │
         └──────────┬───────────┘
                    ▼
          ┌──────────────────┐
          │ parallel_retrieve │  4-channel hybrid retrieval + RRF fusion
          └────────┬─────────┘
                   ▼
          ┌──────────────────┐
          │ generate_answer   │  LLM (Ollama qwen2.5:7b) with system prompt
          │                   │  + system metadata injection for meta-queries
          └────────┬─────────┘
                   ▼
          ┌──────────────────┐
          │compute_confidence │  Multi-signal scoring:
          │                   │  top_score×0.35 + source_coverage×0.20
          │                   │  + method_diversity×0.15 + chunk_sufficiency×0.20
          │                   │  + graph_bonus×0.10
          └────────┬─────────┘
                   ▼
          ┌──────────────────┐
          │persist_fact_     │  Graphiti episodic memory persistence
          │memory            │
          └────────┬─────────┘
                   ▼
                 [END]
```

### Confidence Score Formula
```
confidence = (top_score_norm × 0.35) + (source_coverage × 0.20)
           + (method_diversity × 0.15) + (chunk_sufficiency × 0.20)
           + (graph_bonus × 0.10)
```
Where:
- `top_score_norm` = clamped [0, 1] score of best chunk
- `source_coverage` = `min(unique_sources / 3, 1.0)`
- `method_diversity` = `unique_sources / 4`
- `chunk_sufficiency` = `min(chunk_count / 10, 1.0)`
- `graph_bonus` = 1.0 if graph or obligation channel contributed, else 0.0

---

## 10. Specialized Banking Agents

### 10.1 KYC Agent (`backend/agent/kyc_agent.py`)
- **Input**: Client name, type (individual/corporate), dossier files list
- **Steps**: (1) Dynamic checklist validation using `kyc_checklist.json` → (2) PEP escalation keyword check → (3) Fuzzy sanctions screening across OFAC/EU/UN (`difflib.SequenceMatcher`, threshold 0.85) → (4) Document expiry date verification
- **Output**: `KYCReport` (verdict, risk, completeness_score, sanctions_results)
- **Accuracy**: 29/30 (96.7%)

### 10.2 Credit Agent (`backend/agent/credit_agent.py`)
- **Architecture**: Multi-subagent supervisor pattern
  - `CompletenessSubAgent`: Loan-category-specific document checklist
  - `NumericalSubAgent`: Income verification, **BCT 40% debt ratio threshold**, anomaly detection
  - `IdentitySubAgent`: Cross-reference name/ID/address consistency, KYC risk profile
- **Output**: `CreditReport` (overall_verdict: `APPROVE|REVIEW|REJECT`)
- **Accuracy**: 24/25 (96.0%)

### 10.3 Contract Agent (`backend/agent/contract_agent.py`)
- **Steps**: (1) Text segmentation into clauses → (2) 7-type taxonomy classification (`OBJET`, `DUREE`, `TAUX`, `GARANTIE`, `RESILIATION`, `OBLIGATION_REPORTING`, `PENALITE`) → (3) Circular reference extraction → (4) Neo4j temporal validity check
- **Output**: `ContractReport` (per-clause conformity, temporal issues, overall risk)

### 10.4 Propagation Agent (`backend/agent/propagation_agent.py`)
- **Trigger**: Auto-invoked after every document ingestion
- **Steps**: (1) Cypher traversal from `:Circular` → `:Obligation` → `:Process` / `:ContractTemplate` → (2) Severity mapping based on hop distance and obligation type → (3) `ImpactRecord` persistence to PostgreSQL
- **Output**: `ImpactPropagationReport`

---

## 11. Multi-Source Scraping Engine

**File**: `backend/collector/multi_source_scraper.py`

| Source | Target URL | Method | Output |
|--------|-----------|--------|--------|
| **BCT Portal** | `bct.gov.tn/.../tableau_circulaires.jsp` | HTML table parse → PDF download | PDFs → `backend/data/uploads/` → full ingestion pipeline |
| **OFAC SDN** | `treasury.gov/ofac/downloads/sdn.csv` | Direct CSV download | `backend/data/sanctions/ofac_sdn.csv` (5.4 MB) |
| **EU Sanctions** | `webgate.ec.europa.eu/.../xmlFullSanctionsList` | XML download (`verify=False`) | `backend/data/sanctions/eu_sanctions.xml` (~25 MB) |
| **UN Sanctions** | `scsanctions.un.org/.../consolidated.xml` | XML download | `backend/data/sanctions/un_sanctions.xml` (~2 MB) |
| **GAFI/FATF** | `fatf-gafi.org/en/publications.html` | HTML parse for publications | Regulatory guidance monitoring |

---

## 12. Frontend Architecture

**Framework**: Angular 21 (standalone components, signals, lazy routing)  
**Styling**: TailwindCSS + custom glassmorphism design system  
**State**: Angular Signals (`signal<T>()`, `computed()`)

### Route Map

| Path | Guard | Component | Role |
|------|-------|-----------|------|
| `/login` | None | `LoginComponent` | JWT authentication |
| `/dashboard` | `authGuard` | `DashboardComponent` | Executive stats overview |
| `/chat` | `authGuard` | `ChatComponent` | RAG chat with SSE streaming |
| `/graph` | `authGuard` | `GraphComponent` | Neo4j vis-network graph explorer |
| `/temporal-explorer` | `authGuard` | `TemporalExplorerComponent` | Point-in-time regulatory time-travel |
| `/kyc` | `authGuard` + `roleGuard(['compliance'])` | `KycComponent` | AML/KYC compliance check |
| `/contract` | `authGuard` + `roleGuard(['legal'])` | `ContractComponent` | Contract risk analysis |
| `/credit` | `authGuard` + `roleGuard(['credit'])` | `CreditComponent` | Credit dossier pre-screening |
| `/impact-viewer/:circularId` | `authGuard` + `roleGuard(['compliance'])` | `ImpactViewerComponent` | Change propagation viewer |
| `/admin/documents` | `authGuard` + `roleGuard(['admin'])` | `DocumentsComponent` | Full CRUD + scraping console |

### Key Frontend Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| `@angular/core` | ^21.2.0 | Framework core |
| `@auth0/angular-jwt` | ^5.2.0 | JWT token management |
| `@swimlane/ngx-graph` | ^12.0.0 | Graph visualization components |
| `marked` | ^18.0.6 | Markdown rendering in chat |
| `rxjs` | ~7.8.0 | Reactive streams |

---

## 13. Authentication & Authorization Flow

```
┌──────────┐   POST /auth/login     ┌──────────┐   bcrypt.check   ┌──────────┐
│  Browser │ ────────────────────►  │  Flask   │ ──────────────► │PostgreSQL│
│          │   {username, password}  │  Backend │                  │  users   │
│          │ ◄──────────────────── │          │ ◄────────────── │  table   │
│          │   {access_token, user}  │          │   user record   │          │
└──────────┘                        └──────────┘                  └──────────┘
     │
     │  localStorage.setItem('kusor_token', jwt)
     │  localStorage.setItem('kusor_user', JSON.stringify(user))
     │
     ▼
┌──────────────────────────────────────────────────────────┐
│  jwtInterceptor (HttpInterceptorFn)                      │
│                                                          │
│  Every HTTP request:                                     │
│  1. Read token from localStorage                         │
│  2. Clone request with Authorization: Bearer <token>     │
│  3. If response = 401 → clear storage → redirect /login  │
└──────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────────┐
│  Route Guards                                            │
│                                                          │
│  authGuard: checks auth.isAuthenticated() signal         │
│  roleGuard(['admin']): checks user.role matches          │
│    → admin role gets superuser override on ALL routes     │
└──────────────────────────────────────────────────────────┘
```

### RBAC Role Matrix

| Role | Dashboard | Chat | Graph | KYC | Contract | Credit | Impact | Admin |
|------|-----------|------|-------|-----|----------|--------|--------|-------|
| `admin` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `compliance` | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| `legal` | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| `credit` | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| `user` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## 14. Docker Compose Production Stack

**File**: `docker-compose.yml` — Version `3.9`, Network: `kusor_network`

| Service | Image | Container | Ports | Volumes | Health Check |
|---------|-------|-----------|-------|---------|-------------|
| `postgres` | `postgres:16-alpine` | `kusor-postgres` | `5432:5432` | `kusor_pgdata` | `pg_isready` |
| `neo4j` | `neo4j:5-community` | `kusor-neo4j` | `7474:7474`, `7687:7687` | `kusor_neo4j_data`, `kusor_neo4j_logs` | bolt check |
| `chromadb` | `chromadb/chroma:latest` | `kusor-chromadb` | `8001:8000` | `kusor_chroma_data` | `/api/v2/heartbeat` |
| `ollama` | `ollama/ollama:latest` | `kusor-ollama` | `11435:11434` | `kusor_ollama_data` | `/api/tags` |
| `backend` | Build `./backend` | `kusor-backend` | `5000:5000` | — | depends: postgres, neo4j |
| `frontend` | Build `./frontend` | `kusor-frontend` | `4200:80` | — | depends: backend |
| `n8n` | `docker.n8n.io/n8nio/n8n` | `kusor-n8n` | `5678:5678` | `kusor_n8n_data`, `./n8n/workflows` | — |

---

## 15. Key Dependencies & Their Roles

### Python Backend (`requirements.txt`)

| Package | Version | Role |
|---------|---------|------|
| `flask` | 3.1.3 | Web framework |
| `flask-restx` | 1.3.2 | Swagger API namespaces |
| `flask-cors` | 6.0.5 | Cross-origin request handling |
| `flask-jwt-extended` | 4.7.4 | JWT authentication |
| `flask-sqlalchemy` | 3.1.1 | PostgreSQL ORM |
| `flask-migrate` | 4.1.0 | Alembic database migrations |
| `sqlalchemy` | 2.0.51 | SQL ORM engine |
| `psycopg2-binary` | 2.9.12 | PostgreSQL driver |
| `neo4j` | 6.2.0 | Neo4j Python driver |
| `chromadb` | 1.5.9 | Vector database client |
| `langchain` | 1.3.13 | LLM orchestration framework |
| `langchain-ollama` | 1.1.0 | Ollama LLM integration |
| `langgraph` | 1.2.9 | Agent state machine graphs |
| `graphiti-core` | 0.29.2 | Temporal episodic memory |
| `spacy` | 3.8.14 | French NLP entity extraction |
| `rank-bm25` | 0.2.2 | BM25 keyword search |
| `sentence-transformers` | 5.6.0 | CrossEncoder reranker |
| `instructor` | 1.15.4 | Structured LLM output extraction |
| `pymupdf` | 1.28.0 | PDF text extraction |
| `pytesseract` | 0.3.13 | OCR fallback for scanned PDFs |
| `beautifulsoup4` | 4.15.0 | Web scraping HTML parser |
| `apscheduler` | 3.11.3 | Background task scheduler |
| `bcrypt` | 5.0.0 | Password hashing |

---

## 16. Design Decisions & Rationale

### Why 4-Channel Hybrid Retrieval (not just vector search)?
BCT regulatory circulars are highly structured legal texts. Pure vector search misses exact terminology matches (`"Circulaire N° 2024-01"`) and graph relationships (`"which obligations affect the credit process?"`). The 4 channels cover complementary failure modes:
- **Vector**: Semantic similarity (paraphrased questions)
- **BM25**: Exact keyword match (reference numbers, legal terms)
- **Graph**: Structural relationships (which circular introduced which obligation?)
- **Obligation**: Direct obligation text search + downstream traversal

### Why Reciprocal Rank Fusion (RRF) over simple score averaging?
Different channels produce scores on incomparable scales (cosine similarity [0,1] vs BM25 [0, ∞] vs graph match [binary]). RRF normalizes via rank position, making fusion scale-invariant.

### Why `qwen2.5:7b` over Llama 3 or Mistral?
Qwen 2.5 7B has superior multilingual performance for French legal text compared to Llama 3 8B at equivalent parameter counts. It also runs within 8GB VRAM constraints for local Ollama deployment.

### Why 800-word chunks with 100-word overlap?
BCT circulars contain long articles (500-1500 words). 800-word chunks preserve article-level coherence while fitting within the LLM context window. The 100-word overlap prevents information loss at chunk boundaries.

### Why `nomic-embed-text` for embeddings?
It's the highest-performing open-source embedding model that runs locally via Ollama, producing 768-dimension vectors with strong multilingual (French) support, eliminating dependency on external APIs.

### Why Neo4j temporal edges (`valid_from`/`valid_until`) instead of versioned nodes?
BCT regulations evolve: a circular can AMEND or REPLACE another. Temporal edges allow a single graph query to answer "what was the rule on date X?" without maintaining duplicate node versions. This is the standard approach in regulatory knowledge graphs.

### Why PostgreSQL + Neo4j + ChromaDB (3 databases)?
Each serves a distinct retrieval paradigm that cannot be efficiently replicated by the others:
- **PostgreSQL**: Transactional CRUD, audit logging, user management, relational joins
- **Neo4j**: Graph traversal, temporal path queries, obligation-process-contract topology
- **ChromaDB**: High-dimensional vector similarity search at scale

### Why `setsid` + `disown` in `start.sh` (not systemd)?
This is a development/PoC environment. `systemd` services require root privileges and system-level configuration. `setsid` + `disown` fully detaches daemons from the parent shell without requiring root.

---

## 17. Known Gotchas, Traps & Anti-Patterns

### 🔴 Critical: Always Run Database Migrations After Model Changes
If you add a column to any SQLAlchemy model (e.g., `Document.source`), you MUST run `ALTER TABLE` on PostgreSQL. The ORM will silently crash with `psycopg2.errors.UndefinedColumn` otherwise. Either use Flask-Migrate or manual SQL:
```sql
ALTER TABLE documents ADD COLUMN IF NOT EXISTS source VARCHAR(100) DEFAULT 'BCT Portal';
```

### 🔴 Critical: CORS Must Be Explicitly Configured
`CORS()` initialized without arguments defaults to blocking all cross-origin requests. The Angular frontend at `:4200` will silently fail to reach the Flask backend at `:5000`. The fix is in `app.py`:
```python
cors.init_app(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
```

### 🟡 Warning: Flask Debug Reloader Kills Background Processes
`app.run(debug=True)` spawns a child reloader process. If you `pkill -f "app.py"`, it kills both parent and child. Always use `use_reloader=False` when running as a background daemon:
```python
app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
```

### 🟡 Warning: `nohup` Processes Die When Parent Shell Exits
Standard `nohup ... &` background processes are terminated when the tool shell session ends. Use `setsid` + `disown` instead:
```bash
setsid bash -c "PYTHONPATH=... python -u backend/app.py >> backend.log 2>&1" &
disown
```

### 🟡 Warning: BM25 Index Requires Manual Rebuild
The BM25 index is persisted to `bm25_index.pkl`. After bulk document ingestion, you may see `"BM25 index empty or not built"`. The index rebuilds automatically on the next `BM25Searcher()` initialization, but only if chunks exist in PostgreSQL.

### 🟡 Warning: ChromaDB Port Mapping (8001 → 8000)
Docker Compose maps ChromaDB's internal port 8000 to external port **8001**. The `CHROMA_PORT` config default is `8001`. If running ChromaDB natively (not Docker), it listens on port 8000 — update `CHROMA_PORT` accordingly.

### 🟡 Warning: Neo4j APOC Plugin Required
The `docker-compose.yml` sets `NEO4J_PLUGINS='["apoc"]'`. If running Neo4j without Docker, you must manually install the APOC plugin or some graph queries will fail.

### 🟢 Info: spaCy `fr_core_news_lg` Is Optional
The system falls back to regex entity extraction if spaCy's French model isn't installed. Install it for better NER:
```bash
python -m spacy download fr_core_news_lg
```

### 🟢 Info: System Meta-Questions Get Special Handling
Questions like "how many circulars do you have?" bypass normal RAG retrieval. The `generate_answer()` function in `agent_graph.py` detects these via keyword matching and injects live database counts directly. If you add new meta-question patterns, update the keyword list there.

### 🟢 Info: Admin Role Has Superuser Override
The `roleGuard` in the frontend grants admin users access to ALL routes regardless of the route's required role. The backend `@role_required()` decorator also exempts admin. Don't rely on route guards alone for security — the backend decorator is the true access control layer.

---

## 18. File Quick-Reference Index

| What You Need To Change | File(s) |
|--------------------------|---------|
| Add a new API endpoint | `backend/routes/<namespace>.py` + register in `backend/app.py` |
| Modify database schema | `backend/models/<model>.py` + run ALTER TABLE migration |
| Change RAG retrieval weights | `backend/retrieval/hybrid_retriever.py` → `WEIGHT_MATRIX` dict |
| Update system prompt / AI persona | `backend/agent/prompts.py` → `SYSTEM_PROMPT` |
| Add a new agent graph node | `backend/agent/agent_graph.py` → `build_main_agent_graph()` |
| Modify KYC checklist rules | `backend/data/reference/kyc_checklist.json` |
| Modify credit rules | `backend/data/reference/credit_checklist.json` |
| Add a new scraping source | `backend/collector/multi_source_scraper.py` → `run_full_sync()` |
| Add a new frontend page | Create `frontend/.../pages/<name>/<name>.component.ts` + add route to `app.routes.ts` |
| Change API base URL | `frontend/.../environments/environment.ts` |
| Add a new n8n workflow | Create JSON in `n8n/workflows/` + import in n8n UI |
| Change document chunk size | `backend/processing/document_processor.py` → `chunk_size` param |
| Change LLM model | `.env` → `LLM_MODEL=new-model-name` |
| Change embedding model | `.env` → `EMBEDDING_MODEL=new-model` (requires re-indexing all vectors) |
| Debug auth issues | Check `backend/middleware/auth.py` + `frontend/.../interceptors/jwt.interceptor.ts` |
| View audit trail | Query `audit_logs` table or `GET /api/admin/digest` |

---

*End of Technical Handoff Document*
