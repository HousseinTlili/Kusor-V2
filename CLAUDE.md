# KUSOR — AI-Powered Regulatory Intelligence Assistant

## Project Specification & Build Plan

---

## 1. Project Overview

KUSOR is an AI-powered assistant that enables Attijari Bank Tunisia compliance staff to query BCT (Banque Centrale de Tunisie) regulatory circulars in natural language. It combines **GraphRAG** (a Neo4j knowledge graph capturing inter-circular relationships), **Hybrid RAG** (vector + BM25 + graph traversal fused with Reciprocal Rank Fusion and cross-encoder reranking), and a **LangGraph agentic layer** that classifies questions and selects the optimal retrieval path. All answers are grounded in source documents with exact citations, confidence scores, and graph-aware staleness detection.

---

## 2. Architecture Summary

### 2.1 Seven Layers

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

### 2.2 Three Databases

| Database     | Port(s)     | Stores                                                                              |
|-------------|-------------|--------------------------------------------------------------------------------------|
| **Neo4j 5.18**   | 7474, 7687  | Knowledge graph: `Circular` and `Entity` nodes; `MODIFIES`, `ABROGATES`, `REFERENCES`, `COMPLEMENTS`, `CONCERNS` relationships |
| **ChromaDB**     | 8001        | Vector embeddings of document chunks (collection: `kusor_documents`)                 |
| **PostgreSQL 16**| 5432        | Metadata (documents, chunks, users, sessions, messages), audit logs, application state |

### 2.3 Hybrid RAG Pipeline Flow

```
Question
  │
  ├──→ [Vector Search] ChromaDB cosine similarity → top-k chunks + scores
  ├──→ [BM25 Search] rank-bm25 keyword match → top-k chunks + BM25 scores
  └──→ [Graph Search] spaCy NER + regex → Cypher query → Neo4j → chunks
          │
          ▼
  ┌─────────────────┐
  │  RRF Fusion     │  score(chunk) = Σ 1/(60 + rank_i)
  │  (merge all 3)  │
  └────────┬────────┘
           ▼
  ┌─────────────────┐
  │ Cross-Encoder   │  ms-marco-MiniLM-L-6-v2
  │ Reranker        │  re-score top-20 → return top-5
  └────────┬────────┘
           ▼
     Retrieved Chunks (with scores, sources, graph context)
```

### 2.4 LangGraph Agent Graph

```
┌──────────────┐
│  START        │
└──────┬───────┘
       ▼
┌──────────────────┐
│ classify_question │  → factual | relational | temporal | comparative
└──────┬───────────┘
       ▼
┌──────────────────┐
│ select_tools      │  → choose retrieval strategy based on type
└──────┬───────────┘
       ▼
┌──────────────────┐
│ execute_retrieval │  → parallel tool execution
└──────┬───────────┘
       ▼
┌──────────────────┐
│ rerank_results    │  → CrossEncoderReranker
└──────┬───────────┘
       ▼
┌──────────────────┐
│ generate_answer   │  → LLM with citation-enforcing system prompt
└──────┬───────────┘
       ▼
┌──────────────────┐
│ format_output     │  → Instructor + Pydantic schema enforcement
└──────┬───────────┘
       ▼
┌──────────────┐
│  END          │
└──────────────┘
```

---

## 3. Imposed Technical Constraints

These are **non-negotiable** — set by the bank. Do not substitute any of these.

| Component            | Required Technology                     | Notes                        |
|---------------------|-----------------------------------------|------------------------------|
| Backend framework    | Flask + Flask-RESTX                     | NOT FastAPI                  |
| Frontend framework   | Angular 17+ (currently v21)             | NOT React                    |
| Graph database       | Neo4j 5.18                              | APOC plugin enabled          |
| Vector database      | ChromaDB                                | NOT Qdrant, NOT Weaviate     |
| Metadata + audit DB  | PostgreSQL 16                           | Via SQLAlchemy + Alembic     |
| Agent orchestration  | LangGraph                               |                              |
| RAG framework        | LangChain                               |                              |
| Containerisation     | Docker + Docker Compose                 | GPU passthrough configured   |
| API documentation    | OpenAPI via Flask-RESTX Swagger UI      | Accessible at `/api/docs`    |
| Local LLM            | Qwen2.5-7B via Ollama                   | Already pulled               |
| Embedding model      | nomic-embed-text via Ollama             | Already pulled               |

---

## 4. Current State (What Is Already Done)

### 4.1 Infrastructure — DO NOT RE-IMPLEMENT

- [x] Python 3.11 venv at `backend/.venv` with all pip packages installed (see §4.2)
- [x] Node.js 20 via nvm, Angular CLI installed globally
- [x] Docker Compose running with Neo4j (7474/7687), ChromaDB (8001), PostgreSQL (5432) — all healthy
- [x] Ollama serving `qwen2.5:7b` and `nomic-embed-text` on port 11434
- [x] Project folder structure: `backend/`, `frontend/`, `docs/`, `docker/`
- [x] `backend/.env` configured (see §4.3)
- [x] Angular project scaffolded at `frontend/kusor-ui/` with `ngx-graph`, `@auth0/angular-jwt`, `marked` installed
- [x] Angular uses SCSS for styling

### 4.2 Key Installed Python Packages

| Package               | Version  | Purpose                              |
|-----------------------|----------|--------------------------------------|
| Flask                 | 3.1.3    | Web framework                        |
| flask-restx           | 1.3.2    | REST API + Swagger                   |
| Flask-JWT-Extended    | 4.7.4    | JWT authentication                   |
| flask-cors            | 6.0.5    | CORS handling                        |
| SQLAlchemy            | 2.0.51   | ORM                                  |
| alembic               | 1.18.5   | Database migrations                  |
| psycopg2-binary       | 2.9.12   | PostgreSQL driver                    |
| neo4j                 | 6.2.0    | Neo4j Python driver                  |
| chromadb              | 1.5.9    | ChromaDB client                      |
| langchain             | 1.3.13   | RAG framework                        |
| langchain-chroma      | 1.1.0    | LangChain ChromaDB integration       |
| langchain-ollama      | 1.1.0    | LangChain Ollama integration         |
| langchain-community   | 0.4.2    | LangChain community integrations     |
| langchain-text-splitters | 1.1.2 | Text splitting utilities             |
| langgraph             | 1.2.9    | Agent orchestration                  |
| langgraph-prebuilt    | 1.1.0    | Prebuilt agent components            |
| instructor            | 1.15.4   | Structured LLM output extraction     |
| pydantic              | 2.13.4   | Data validation / schemas            |
| pymupdf               | 1.28.0   | PDF text extraction                  |
| pytesseract           | 0.3.13   | OCR fallback                         |
| rank-bm25             | 0.2.2    | BM25 keyword search                  |
| sentence-transformers | 5.6.0    | Cross-encoder reranker               |
| beautifulsoup4        | 4.15.0   | HTML parsing (scraper)               |
| requests              | 2.34.2   | HTTP client                          |
| APScheduler           | 3.11.3   | Task scheduling                      |
| bcrypt                | 5.0.0    | Password hashing                     |
| python-dotenv         | 1.2.2    | Env file loading                     |
| torch                 | 2.13.0   | PyTorch (GPU)                        |
| transformers          | 5.13.0   | Hugging Face transformers            |
| ollama                | 0.6.2    | Ollama Python client                 |
| pytest                | 9.1.1    | Testing                              |

### 4.3 Missing Package (Must Install Before Module 3)

```bash
cd ~/kusor && source backend/.venv/bin/activate
pip install spacy
python -m spacy download fr_core_news_lg
```

### 4.4 Environment Variables (`backend/.env`)

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

### 4.5 Docker Compose (`docker/docker-compose.yml`)

Services running: `kusor_neo4j`, `kusor_chroma`, `kusor_postgres` on network `kusor_net`.

### 4.6 Hardware

- GPU: NVIDIA RTX 4060 8GB VRAM
- RAM: 24GB system RAM
- OS: Ubuntu 24.04 on external SSD (USB-C, ~1000 MB/s)
- Docker GPU passthrough: configured

---

## 5. Implementation Plan

### Build Order

Modules are implemented in dependency order, **not numerical order**:

```
Module 3 (Document Processing) → Module 4 (GraphRAG) → Module 5 (Hybrid RAG)
→ Module 6 (LangGraph Agent) → Module 1 (BCT Collector) → Module 2 (Flask API)
→ Module 7 (Angular Frontend)
```

---

### Module 3 — Document Pre-Processing Pipeline

**Why first**: Every other module depends on its output.

**Dependencies**: None (first module).

#### Files to Create

##### `backend/processing/__init__.py`

```python
# Empty init — marks processing as a package.
```

##### `backend/processing/document_processor.py`

```python
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import re
import pickle
from pathlib import Path

@dataclass
class ChunkMetadata:
    document_id: str
    chunk_index: int
    page_number: int
    source_filename: str
    circular_number: Optional[str]

@dataclass
class ExtractedEntity:
    text: str
    label: str  # "ORG", "LAW", or "CIRCULAR_REF"
    start_char: int
    end_char: int

@dataclass
class ProcessingResult:
    document_id: str
    source_filename: str
    total_pages: int
    total_chunks: int
    chunks: List[Dict[str, Any]]  # [{content, metadata: ChunkMetadata}]
    entities: List[ExtractedEntity]
    circular_references: List[str]  # List of referenced circular numbers
    bm25_updated: bool
    chroma_updated: bool
    errors: List[str]


class DocumentProcessor:
    """
    Processes BCT circular PDFs into indexed, searchable chunks.
    
    Pipeline:
    1. Text extraction (PyMuPDF primary, Tesseract OCR fallback)
    2. Structural pre-segmentation (detect BCT headings/articles)
    3. Semantic chunking (LangChain SemanticChunker + nomic-embed-text)
    4. NER extraction (spaCy fr_core_news_lg + regex)
    5. Embedding generation + ChromaDB storage
    6. BM25 index update
    """

    # Regex patterns for BCT circular structure detection
    ARTICLE_PATTERN: str = r"(?i)(?:^|\n)\s*(article\s+\d+[\s\S]*?)(?=\n\s*article\s+\d+|\Z)"
    CIRCULAR_HEADER_PATTERN: str = r"(?i)circulaire\s+(?:aux\s+\w+\s+)?n[°o]\s*(\d{4}-\d+)"
    SECTION_PATTERN: str = r"(?i)(?:^|\n)\s*((?:titre|chapitre|section|sous-section)\s+[IVXLCDM\d]+[^\n]*)"
    
    # Regex for circular reference extraction from text
    CIRCULAR_REF_PATTERN: str = r"(?i)circulaire\s+n[°o]\s*(\d{4}-\d+)"

    def __init__(
        self,
        chroma_host: str = "localhost",
        chroma_port: int = 8001,
        ollama_base_url: str = "http://localhost:11434",
        embedding_model: str = "nomic-embed-text",
        collection_name: str = "kusor_documents",
        bm25_index_path: str = "backend/data/bm25_index.pkl",
        spacy_model: str = "fr_core_news_lg",
    ) -> None: ...

    def process_document(
        self,
        pdf_path: str,
        document_id: str,
        circular_number: Optional[str] = None,
    ) -> ProcessingResult:
        """Main entry point. Processes a single PDF end-to-end."""
        ...

    def _extract_text(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract text from PDF using PyMuPDF.
        Falls back to Tesseract OCR for pages with < 50 chars extracted.
        Returns: [{page_number: int, text: str}]
        """
        ...

    def _structural_presegment(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Pre-segment text by BCT structural markers (articles, sections, titles).
        Ensures legal articles are never split across semantic chunks.
        Returns: [{content: str, page_number: int, segment_type: str}]
        """
        ...

    def _semantic_chunk(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply LangChain SemanticChunker with nomic-embed-text to each segment.
        Oversized segments (>512 tokens) are further split with 60-token overlap.
        Returns: [{content: str, page_number: int, chunk_index: int}]
        """
        ...

    def _extract_entities(self, text: str) -> List[ExtractedEntity]:
        """
        Extract entities using spaCy fr_core_news_lg (ORG, LAW labels)
        and regex for BCT circular references.
        """
        ...

    def _store_in_chromadb(
        self,
        chunks: List[Dict[str, Any]],
        document_id: str,
        source_filename: str,
        circular_number: Optional[str],
    ) -> bool:
        """
        Generate embeddings via nomic-embed-text and store in ChromaDB
        collection 'kusor_documents' with metadata per chunk.
        """
        ...

    def _update_bm25_index(self, chunks: List[Dict[str, Any]]) -> bool:
        """
        Update the persisted BM25 index at backend/data/bm25_index.pkl.
        If index exists, append new chunks. Otherwise, create new index.
        Uses rank_bm25.BM25Okapi.
        """
        ...

    def _generate_document_id(self, filename: str) -> str:
        """Generate deterministic document ID from filename."""
        ...
```

**Key implementation details**:

- **Structural pre-segmentation** runs BEFORE semantic chunking. Use the regex patterns to split the raw text at `Article X`, `Titre X`, `Chapitre X`, `Section X` boundaries. Each segment becomes an independent unit for semantic chunking. This guarantees a legal article is never split across two chunks.
- **SemanticChunker** from `langchain_experimental.text_splitter` with `OllamaEmbeddings(model="nomic-embed-text")` as the embedding function. Set `breakpoint_threshold_type="percentile"` and `breakpoint_threshold_amount=80`.
- **Oversized segments**: After semantic chunking, any chunk exceeding 512 tokens is further split using `RecursiveCharacterTextSplitter` with `chunk_size=400`, `chunk_overlap=60` (in tokens).
- **ChromaDB metadata** per chunk: `document_id`, `chunk_index`, `page_number`, `source_filename`, `circular_number`.
- **BM25 index**: Tokenize chunk content by whitespace + lowercasing. Persist the corpus list and the `BM25Okapi` object together in a pickle file at `backend/data/bm25_index.pkl`.
- **OCR fallback**: If PyMuPDF extracts fewer than 50 characters from a page, render the page as an image with `page.get_pixmap(dpi=300)` and run `pytesseract.image_to_string(image, lang='fra')`.

##### `backend/processing/tests/__init__.py`

```python
# Empty init
```

##### `backend/processing/tests/test_document_processor.py`

```python
import pytest
from backend.processing.document_processor import DocumentProcessor, ProcessingResult

class TestDocumentProcessor:
    def test_process_real_circular(self) -> None:
        """Process a real BCT circular PDF and verify complete pipeline."""
        ...

    def test_chunks_stored_in_chromadb(self) -> None:
        """After processing, chunks must exist in ChromaDB with correct metadata."""
        ...

    def test_entities_extracted(self) -> None:
        """NER must extract ORG and LAW entities, plus circular references."""
        ...

    def test_bm25_index_updated(self) -> None:
        """BM25 index file must exist and contain the processed document's chunks."""
        ...

    def test_structural_presegmentation(self) -> None:
        """Articles must not be split across chunks."""
        ...

    def test_ocr_fallback(self) -> None:
        """Scanned PDFs trigger OCR and still produce valid chunks."""
        ...

    def test_idempotent_reprocessing(self) -> None:
        """Processing the same document twice doesn't create duplicate chunks."""
        ...
```

#### Acceptance Criteria

- [ ] `DocumentProcessor` can process a BCT circular PDF end-to-end
- [ ] Text extraction works for both text-based and scanned PDFs
- [ ] Structural pre-segmentation detects `Article`, `Titre`, `Chapitre`, `Section` boundaries
- [ ] Semantic chunks respect structural boundaries (no cross-article splits)
- [ ] Chunks are stored in ChromaDB collection `kusor_documents` with all 5 metadata fields
- [ ] spaCy extracts `ORG` and `LAW` entities from French text
- [ ] Regex extracts circular references matching `circulaire n° YYYY-NNN`
- [ ] BM25 index is persisted to `backend/data/bm25_index.pkl`
- [ ] Reprocessing the same document does not create duplicate chunks
- [ ] All tests pass

#### Verification Commands

```bash
cd ~/kusor
source backend/.venv/bin/activate

# Install spaCy if not already done
pip install spacy
python -m spacy download fr_core_news_lg

# Create data directories
mkdir -p backend/data/circulars

# Run tests
python -m pytest backend/processing/tests/test_document_processor.py -v

# Manual verification: process a sample PDF
python -c "
from backend.processing.document_processor import DocumentProcessor
dp = DocumentProcessor()
result = dp.process_document('backend/data/circulars/sample.pdf', 'test-001')
print(f'Chunks: {result.total_chunks}, Entities: {len(result.entities)}')
print(f'ChromaDB updated: {result.chroma_updated}, BM25 updated: {result.bm25_updated}')
"

# Verify ChromaDB has data
python -c "
import chromadb
client = chromadb.HttpClient(host='localhost', port=8001)
col = client.get_collection('kusor_documents')
print(f'ChromaDB chunk count: {col.count()}')
"
```

---

### Module 4 — GraphRAG Knowledge Graph (Neo4j)

**Why second**: Must exist before retrieval can use graph traversal.

**Dependencies**: Module 3 (needs `ProcessingResult` and extracted entities).

#### Files to Create

##### `backend/graph/__init__.py`

```python
# Empty init
```

##### `backend/graph/cypher_queries.py`

All Cypher queries as named constants. **Never build Cypher strings inline anywhere else.**

```python
"""All Cypher queries used by the GraphRAG module."""

# --- Node creation ---
CREATE_CIRCULAR_NODE: str = """
MERGE (c:Circular {number: $number})
SET c.id = $id,
    c.title = $title,
    c.date = $date,
    c.category = $category,
    c.url = $url,
    c.status = $status
RETURN c
"""

CREATE_ENTITY_NODE: str = """
MERGE (e:Entity {name: $name, type: $type})
RETURN e
"""

LINK_ENTITY_TO_CIRCULAR: str = """
MATCH (c:Circular {number: $circular_number})
MERGE (e:Entity {name: $entity_name, type: $entity_type})
MERGE (c)-[:MENTIONS]->(e)
"""

# --- Relationship creation ---
CREATE_ABROGATES_REL: str = """
MATCH (source:Circular {number: $source_number})
MATCH (target:Circular {number: $target_number})
MERGE (source)-[:ABROGATES]->(target)
SET target.status = 'ABROGATED'
"""

CREATE_MODIFIES_REL: str = """
MATCH (source:Circular {number: $source_number})
MATCH (target:Circular {number: $target_number})
MERGE (source)-[r:MODIFIES]->(target)
SET r.article = $article
"""

CREATE_REFERENCES_REL: str = """
MATCH (source:Circular {number: $source_number})
MATCH (target:Circular {number: $target_number})
MERGE (source)-[:REFERENCES]->(target)
"""

CREATE_COMPLEMENTS_REL: str = """
MATCH (source:Circular {number: $source_number})
MATCH (target:Circular {number: $target_number})
MERGE (source)-[:COMPLEMENTS]->(target)
"""

CREATE_CONCERNS_REL: str = """
MATCH (source:Circular {number: $source_number})
MATCH (target:Circular {number: $target_number})
MERGE (source)-[:CONCERNS]->(target)
"""

# --- Graph queries ---
GET_CIRCULAR_BY_NUMBER: str = """
MATCH (c:Circular {number: $number})
RETURN c
"""

GET_CIRCULAR_RELATIONS: str = """
MATCH (c:Circular {number: $number})-[r]->(related:Circular)
RETURN c, type(r) AS relationship, r, related
UNION
MATCH (c:Circular {number: $number})<-[r]-(related:Circular)
RETURN c, type(r) AS relationship, r, related
"""

GET_MODIFICATION_CHAIN: str = """
MATCH path = (c:Circular {number: $number})-[:MODIFIES|ABROGATES*1..5]->(target:Circular)
RETURN path
"""

SUBGRAPH_BY_CIRCULAR: str = """
MATCH (c:Circular {number: $number})
CALL apoc.path.subgraphAll(c, {maxLevel: $max_hops})
YIELD nodes, relationships
RETURN nodes, relationships
"""

SEARCH_BY_ENTITIES: str = """
UNWIND $entity_names AS ename
MATCH (e:Entity)
WHERE toLower(e.name) CONTAINS toLower(ename)
MATCH (e)<-[:MENTIONS]-(c:Circular)
RETURN DISTINCT c
LIMIT $limit
"""

SEARCH_BY_CIRCULAR_NUMBERS: str = """
UNWIND $numbers AS num
MATCH (c:Circular {number: num})-[r*0..2]-(related)
RETURN DISTINCT c, related, r
"""

TWO_HOP_TRAVERSAL: str = """
UNWIND $start_numbers AS num
MATCH (start:Circular {number: num})
MATCH path = (start)-[*1..2]-(connected:Circular)
RETURN DISTINCT connected.number AS number,
       connected.title AS title,
       connected.id AS id
"""

GET_ALL_CIRCULARS: str = """
MATCH (c:Circular)
RETURN c
ORDER BY c.date DESC
"""

GET_GRAPH_STATS: str = """
MATCH (c:Circular) WITH count(c) AS circulars
MATCH (e:Entity) WITH circulars, count(e) AS entities
MATCH ()-[r]->() WITH circulars, entities, count(r) AS relationships
RETURN circulars, entities, relationships
"""

# --- Subgraph for visualization ---
GET_SUBGRAPH_FOR_VIS: str = """
MATCH (c:Circular {number: $number})
OPTIONAL MATCH (c)-[r]-(related)
RETURN c, r, related
"""

FULLTEXT_SEARCH_CIRCULARS: str = """
MATCH (c:Circular)
WHERE toLower(c.title) CONTAINS toLower($query)
   OR c.number CONTAINS $query
RETURN c
LIMIT $limit
"""
```

##### `backend/graph/neo4j_manager.py`

```python
from typing import Any, Dict, List, Optional
from neo4j import GraphDatabase, Driver, Session

class Neo4jManager:
    """
    Manages Neo4j connection pool and Cypher execution.
    Thread-safe — uses neo4j driver's built-in connection pooling.
    """

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "kusor_password",
    ) -> None: ...

    def close(self) -> None:
        """Close the driver and release all connections."""
        ...

    def health_check(self) -> bool:
        """Returns True if Neo4j is reachable and responsive."""
        ...

    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        write: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results as list of dicts.
        Uses read or write transaction based on `write` flag.
        """
        ...

    def execute_write(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Shorthand for execute_query with write=True."""
        ...
```

##### `backend/graph/graph_builder.py`

```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re

@dataclass
class CircularNode:
    id: str
    number: str
    title: str
    date: str  # ISO 8601 format: "YYYY-MM-DD"
    category: str
    url: str
    status: str  # "ACTIVE", "ABROGATED", "MODIFIED"

@dataclass
class ExtractedRelationship:
    source_number: str
    target_number: str
    relationship_type: str  # MODIFIES, ABROGATES, REFERENCES, COMPLEMENTS, CONCERNS
    article: Optional[str]  # For MODIFIES: which article is modified
    confidence: float  # 0.0-1.0 — 1.0 for regex, lower for LLM-extracted
    extraction_method: str  # "regex" or "llm"


class GraphBuilder:
    """
    Builds and maintains the Neo4j knowledge graph from processed documents.
    
    Two extraction methods:
    1. Regex-based: for explicit references in text (high confidence)
    2. LLM-based: via Instructor + Pydantic for implicit relationships
    """

    # Regex patterns for relationship extraction from document text
    ABROGATES_PATTERN: str = r"(?i)abrog[ée](?:e|s|ant)?\s+(?:la\s+)?circulaire\s+n[°o]\s*(\d{4}-\d+)"
    MODIFIES_PATTERN: str = r"(?i)modifi[ée](?:e|s|ant)?\s+(?:l['\u2019]article\s+(\d+[\w.-]*)\s+(?:de\s+)?)?(?:la\s+)?circulaire\s+n[°o]\s*(\d{4}-\d+)"
    REFERENCES_PATTERN: str = r"(?i)(?:en\s+application\s+de|(?:conform[ée]ment|en\s+vertu)\s+(?:de|à)\s+)?(?:la\s+)?circulaire\s+n[°o]\s*(\d{4}-\d+)"
    COMPLEMENTS_PATTERN: str = r"(?i)compl[èeé]t(?:e|ant)\s+(?:la\s+)?circulaire\s+n[°o]\s*(\d{4}-\d+)"

    def __init__(
        self,
        neo4j_manager: "Neo4jManager",
        ollama_base_url: str = "http://localhost:11434",
        llm_model: str = "qwen2.5:7b",
    ) -> None: ...

    def create_circular_node(self, circular: CircularNode) -> None:
        """Create or update a Circular node using MERGE."""
        ...

    def create_entity_nodes(
        self,
        circular_number: str,
        entities: List[Dict[str, str]],
    ) -> None:
        """
        Create Entity nodes and link them to the Circular via MENTIONS.
        Uses MERGE to avoid duplicates.
        """
        ...

    def extract_relationships_regex(
        self,
        source_number: str,
        document_text: str,
    ) -> List[ExtractedRelationship]:
        """
        Extract explicit inter-circular relationships from document text
        using regex patterns. Returns list of extracted relationships.
        """
        ...

    def extract_relationships_llm(
        self,
        source_number: str,
        document_text: str,
    ) -> List[ExtractedRelationship]:
        """
        Extract implicit relationships using LLM via Instructor + Pydantic.
        Uses Qwen2.5-7B through Ollama.
        
        The Pydantic model sent to the LLM:
        
        class CircularRelationship(BaseModel):
            target_circular: str = Field(description="Circular number referenced, format YYYY-NN")
            relationship_type: Literal["MODIFIES", "ABROGATES", "REFERENCES", "COMPLEMENTS", "CONCERNS"]
            article: Optional[str] = Field(description="Article number if applicable")
            justification: str = Field(description="Quote from text supporting this relationship")
        
        class RelationshipExtractionResult(BaseModel):
            relationships: List[CircularRelationship]
        """
        ...

    def create_relationships(
        self,
        relationships: List[ExtractedRelationship],
    ) -> int:
        """
        Write extracted relationships to Neo4j.
        Returns count of relationships created.
        """
        ...

    def build_graph_for_document(
        self,
        circular: CircularNode,
        document_text: str,
        entities: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """
        Full graph construction pipeline for one document:
        1. Create/update Circular node
        2. Create Entity nodes + MENTIONS edges
        3. Extract relationships (regex first, then LLM)
        4. Deduplicate relationships (regex wins on conflict)
        5. Create relationship edges
        Returns summary dict.
        """
        ...

    def search_by_entities(
        self,
        entity_names: List[str],
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Find circulars mentioning given entities."""
        ...

    def get_connected_chunks(
        self,
        circular_numbers: List[str],
        max_hops: int = 2,
    ) -> List[Dict[str, Any]]:
        """
        Given a list of circular numbers, perform 2-hop traversal
        and return connected circular data as a chunk-compatible list.
        """
        ...

    def get_subgraph(
        self,
        circular_number: str,
        max_hops: int = 2,
    ) -> Dict[str, Any]:
        """
        Return subgraph centered on a circular for visualization.
        Returns: {nodes: [...], edges: [...]}
        """
        ...
```

##### `backend/graph/tests/__init__.py`

```python
# Empty init
```

##### `backend/graph/tests/test_graph_builder.py`

```python
import pytest
from backend.graph.neo4j_manager import Neo4jManager
from backend.graph.graph_builder import GraphBuilder, CircularNode

class TestGraphBuilder:
    def test_create_circular_node(self) -> None:
        """Verify Circular node is created in Neo4j with all properties."""
        ...

    def test_create_entity_nodes_no_duplicates(self) -> None:
        """MERGE must prevent duplicate Entity nodes."""
        ...

    def test_extract_relationships_regex(self) -> None:
        """Test regex extraction for all 4 relationship types."""
        ...

    def test_abrogates_sets_status(self) -> None:
        """When ABROGATES is created, target circular status should be ABROGATED."""
        ...

    def test_two_hop_traversal(self) -> None:
        """Given A->B->C chain, querying from A should return C."""
        ...

    def test_full_pipeline(self) -> None:
        """build_graph_for_document should create nodes, entities, and relationships."""
        ...

    def test_get_subgraph_for_visualization(self) -> None:
        """Subgraph should return nodes and edges for Angular rendering."""
        ...
```

#### Acceptance Criteria

- [ ] `Neo4jManager` connects to Neo4j and passes health check
- [ ] `Circular` nodes are created with all properties via MERGE (idempotent)
- [ ] `Entity` nodes use MERGE (no duplicates on repeated runs)
- [ ] Regex extraction correctly identifies ABROGATES, MODIFIES, REFERENCES, COMPLEMENTS
- [ ] LLM extraction via Instructor returns valid Pydantic models
- [ ] `ABROGATES` relationship sets target circular `status = "ABROGATED"`
- [ ] 2-hop traversal from circular A finds transitively connected circulars
- [ ] `get_subgraph` returns data in a format suitable for Angular ngx-graph
- [ ] All Cypher queries come from `cypher_queries.py` constants (no inline Cypher)
- [ ] All tests pass

#### Verification Commands

```bash
cd ~/kusor
source backend/.venv/bin/activate

# Run tests
python -m pytest backend/graph/tests/test_graph_builder.py -v

# Manual verification: check Neo4j
python -c "
from backend.graph.neo4j_manager import Neo4jManager
nm = Neo4jManager()
print('Health check:', nm.health_check())
stats = nm.execute_query('MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count')
print('Graph stats:', stats)
nm.close()
"

# Check via Neo4j browser: http://localhost:7474
```

---

### Module 5 — Hybrid RAG Search Engine

**Why third**: The retrieval layer that the agent (Module 6) will call.

**Dependencies**: Module 3 (ChromaDB data + BM25 index), Module 4 (Neo4j graph).

#### Files to Create

##### `backend/retrieval/__init__.py`

```python
# Empty init
```

##### `backend/retrieval/schemas.py`

```python
from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class RetrievedChunk:
    """A single chunk returned from any retrieval method."""
    content: str
    document_id: str
    chunk_index: int
    page_number: int
    source_filename: str
    circular_number: Optional[str]
    score: float  # Normalized score (0.0-1.0)
    retrieval_method: str  # "vector", "bm25", "graph"
    
@dataclass
class RetrievalResult:
    """Complete result from hybrid retrieval."""
    chunks: List[RetrievedChunk]
    query: str
    vector_count: int
    bm25_count: int
    graph_count: int
    fusion_method: str  # "rrf"
    reranked: bool
```

##### `backend/retrieval/vector_searcher.py`

```python
from typing import List, Optional

class VectorSearcher:
    """
    Searches ChromaDB via embedded question for semantically similar chunks.
    Uses nomic-embed-text (via Ollama) to embed the query.
    """

    def __init__(
        self,
        chroma_host: str = "localhost",
        chroma_port: int = 8001,
        collection_name: str = "kusor_documents",
        ollama_base_url: str = "http://localhost:11434",
        embedding_model: str = "nomic-embed-text",
    ) -> None: ...

    def search(
        self,
        query: str,
        top_k: int = 10,
        filter_circular: Optional[str] = None,
    ) -> List["RetrievedChunk"]:
        """
        Embed query with nomic-embed-text, search ChromaDB with cosine similarity.
        Returns top-k chunks with scores.
        Optional: filter by circular_number.
        """
        ...
```

##### `backend/retrieval/bm25_searcher.py`

```python
from typing import List
import pickle
from pathlib import Path

class BM25Searcher:
    """
    BM25 keyword search over the persisted index.
    Loads index from backend/data/bm25_index.pkl.
    """

    def __init__(
        self,
        index_path: str = "backend/data/bm25_index.pkl",
    ) -> None: ...

    def search(
        self,
        query: str,
        top_k: int = 10,
    ) -> List["RetrievedChunk"]:
        """
        Tokenize query (whitespace + lowercase), run BM25Okapi.get_scores(),
        return top-k chunks with normalized BM25 scores.
        """
        ...

    def reload_index(self) -> None:
        """Reload the BM25 index from disk (call after new documents are processed)."""
        ...
```

##### `backend/retrieval/graph_searcher.py`

```python
from typing import List

class GraphSearcher:
    """
    Graph-based retrieval: extracts entities/circular numbers from the question,
    queries Neo4j for related circulars, retrieves their chunks from ChromaDB.
    """

    def __init__(
        self,
        neo4j_manager: "Neo4jManager",
        chroma_host: str = "localhost",
        chroma_port: int = 8001,
        collection_name: str = "kusor_documents",
        spacy_model: str = "fr_core_news_lg",
    ) -> None: ...

    def search(
        self,
        query: str,
        top_k: int = 10,
    ) -> List["RetrievedChunk"]:
        """
        1. Extract entities with spaCy (ORG, LAW) and circular numbers with regex
        2. Query Neo4j: find circulars mentioning those entities / matching numbers
        3. Perform 2-hop traversal from matched circulars
        4. Fetch chunk content from ChromaDB for found circulars
        5. Return top-k chunks scored by graph proximity
        """
        ...

    def _extract_query_entities(self, query: str) -> dict:
        """
        Returns: {
            entity_names: List[str],
            circular_numbers: List[str],
        }
        """
        ...
```

##### `backend/retrieval/reranker.py`

```python
from typing import List

class CrossEncoderReranker:
    """
    Re-ranks chunks using cross-encoder/ms-marco-MiniLM-L-6-v2.
    Takes (query, chunk_content) pairs and produces relevance scores.
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    ) -> None: ...

    def rerank(
        self,
        query: str,
        chunks: List["RetrievedChunk"],
        top_k: int = 5,
    ) -> List["RetrievedChunk"]:
        """
        Re-score each chunk against the query using the cross-encoder.
        Input: top-20 RRF-fused chunks.
        Output: top-5 chunks, re-scored and re-sorted.
        Updates each chunk's score with the cross-encoder score.
        """
        ...
```

##### `backend/retrieval/hybrid_retriever.py`

```python
from typing import List, Dict, Any

class HybridRetriever:
    """
    Orchestrates all three retrieval strategies and fuses results.
    
    Pipeline:
    1. Run VectorSearcher, BM25Searcher, GraphSearcher in parallel
    2. Fuse results with Reciprocal Rank Fusion (RRF)
    3. Re-rank top-20 with CrossEncoderReranker
    4. Return top-5 most relevant chunks
    """

    RRF_K: int = 60  # RRF constant: score = sum(1 / (k + rank))

    def __init__(
        self,
        vector_searcher: "VectorSearcher",
        bm25_searcher: "BM25Searcher",
        graph_searcher: "GraphSearcher",
        reranker: "CrossEncoderReranker",
    ) -> None: ...

    def retrieve(
        self,
        question: str,
        top_k: int = 5,
        use_vector: bool = True,
        use_bm25: bool = True,
        use_graph: bool = True,
    ) -> List["RetrievedChunk"]:
        """
        Single public method. Runs the full hybrid retrieval pipeline.
        
        1. Execute enabled searchers
        2. Fuse with RRF
        3. Re-rank top-20
        4. Return top-k (default 5)
        """
        ...

    def _reciprocal_rank_fusion(
        self,
        ranked_lists: List[List["RetrievedChunk"]],
    ) -> List["RetrievedChunk"]:
        """
        Merge multiple ranked lists using RRF.
        
        For each chunk appearing in any list:
            rrf_score = sum(1 / (RRF_K + rank_in_list_i)) for each list containing it
        
        Chunks are identified by (document_id, chunk_index) tuple.
        Returns merged list sorted by RRF score descending.
        """
        ...
```

##### `backend/retrieval/tests/__init__.py`

```python
# Empty init
```

##### `backend/retrieval/tests/test_hybrid_retriever.py`

```python
import pytest
from backend.retrieval.hybrid_retriever import HybridRetriever

class TestHybridRetriever:
    def test_all_three_paths_contribute(self) -> None:
        """Vector, BM25, and graph searchers must all return results."""
        ...

    def test_rrf_fusion_scores(self) -> None:
        """RRF scores should increase for chunks appearing in multiple lists."""
        ...

    def test_reranked_more_relevant(self) -> None:
        """Cross-encoder reranked output should be more relevant than raw vector."""
        ...

    def test_single_strategy_mode(self) -> None:
        """Setting use_bm25=False should exclude BM25 results."""
        ...

    def test_empty_graph_results_handled(self) -> None:
        """If graph search finds nothing, vector+BM25 still work."""
        ...

    def test_deduplication(self) -> None:
        """Same chunk from multiple searchers should appear once in final output."""
        ...
```

#### Acceptance Criteria

- [ ] `VectorSearcher` returns semantically similar chunks from ChromaDB
- [ ] `BM25Searcher` loads persisted index and returns keyword-matched chunks
- [ ] `GraphSearcher` extracts entities from question, queries Neo4j, returns graph-context chunks
- [ ] `HybridRetriever.retrieve()` fuses results from all three with RRF
- [ ] RRF formula: `score = sum(1 / (60 + rank))` correctly implemented
- [ ] `CrossEncoderReranker` re-scores top-20 fused chunks and returns top-5
- [ ] Chunks appearing in multiple search results get higher RRF scores
- [ ] Deduplication by `(document_id, chunk_index)` works correctly
- [ ] All tests pass

#### Verification Commands

```bash
cd ~/kusor
source backend/.venv/bin/activate

# Run tests
python -m pytest backend/retrieval/tests/test_hybrid_retriever.py -v

# Manual verification: search
python -c "
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.retrieval.vector_searcher import VectorSearcher
from backend.retrieval.bm25_searcher import BM25Searcher
from backend.retrieval.graph_searcher import GraphSearcher
from backend.retrieval.reranker import CrossEncoderReranker
from backend.graph.neo4j_manager import Neo4jManager

nm = Neo4jManager()
vs = VectorSearcher()
bs = BM25Searcher()
gs = GraphSearcher(neo4j_manager=nm)
rr = CrossEncoderReranker()
hr = HybridRetriever(vs, bs, gs, rr)

results = hr.retrieve('Quelles sont les conditions de reserve obligatoire?')
for r in results:
    print(f'[{r.retrieval_method}] Score: {r.score:.4f} | {r.source_filename} p.{r.page_number}')
    print(f'  {r.content[:100]}...')
nm.close()
"
```

---

### Module 6 — LangGraph AI Agent

**Why fourth**: Sits on top of the retrieval layer.

**Dependencies**: Module 5 (HybridRetriever), Module 4 (Neo4j for graph queries).

#### Files to Create

##### `backend/agent/__init__.py`

```python
# Empty init
```

##### `backend/agent/schemas.py`

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class QuestionType(str, Enum):
    FACTUAL = "factual"          # "What are the reserve requirements?"
    RELATIONAL = "relational"    # "Has circular X been modified?"
    TEMPORAL = "temporal"        # "What changed between 2020 and 2023?"
    COMPARATIVE = "comparative"  # "How does circular X differ from Y?"

class SourceCitation(BaseModel):
    circular_number: str = Field(description="BCT circular number, e.g. '2024-01'")
    title: str = Field(description="Title of the circular")
    page: int = Field(description="Page number in the original PDF")
    excerpt: str = Field(description="Exact excerpt from the circular supporting the claim")

class AgentResponse(BaseModel):
    answer: str = Field(description="Complete answer in French, with inline citations")
    sources: List[SourceCitation] = Field(description="All sources cited in the answer")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence in answer completeness")
    related_circulars: List[str] = Field(description="Circular numbers related but not directly cited")
    graph_path_used: bool = Field(description="Whether graph traversal was used for this answer")
    question_type: QuestionType = Field(description="Classified type of the question")

class AgentState(BaseModel):
    """LangGraph state object passed between nodes."""
    question: str = ""
    question_type: Optional[QuestionType] = None
    selected_tools: List[str] = Field(default_factory=list)
    retrieved_chunks: List[dict] = Field(default_factory=list)
    reranked_chunks: List[dict] = Field(default_factory=list)
    graph_path_used: bool = False
    llm_response: Optional[str] = None
    final_response: Optional[AgentResponse] = None
    error: Optional[str] = None
    retry_count: int = 0
```

##### `backend/agent/prompts.py`

```python
"""Prompt templates for the LangGraph agent."""

SYSTEM_PROMPT: str = """Tu es KUSOR, un assistant réglementaire intelligent spécialisé dans les circulaires de la Banque Centrale de Tunisie (BCT). Tu réponds UNIQUEMENT en te basant sur les documents fournis dans le contexte.

RÈGLES STRICTES :
1. Réponds UNIQUEMENT à partir des extraits de circulaires fournis dans le contexte. Ne génère JAMAIS d'information non présente dans le contexte.
2. Cite chaque affirmation avec la source exacte au format [Circulaire N° XXXX-XX, p. Y].
3. Si le contexte ne contient pas suffisamment d'information pour répondre, dis-le explicitement : "Les documents disponibles ne me permettent pas de répondre à cette question."
4. Si une circulaire a été abrogée ou modifiée selon le graphe de connaissances, signale-le clairement : "⚠️ Attention : cette circulaire a été [modifiée/abrogée] par la circulaire N° XXXX-XX."
5. Réponds toujours en français.
6. Structure ta réponse avec des paragraphes clairs. Utilise des listes à puces pour les énumérations.
7. Pour les questions relationnelles (modifications, abrogations), présente la chaîne chronologique complète.
8. Indique ton niveau de confiance : élevé (>0.8) si plusieurs sources convergent, moyen (0.5-0.8) si une seule source, faible (<0.5) si le contexte est partiel.

CONTEXTE :
{context}

INFORMATIONS DU GRAPHE DE CONNAISSANCES :
{graph_context}
"""

CLASSIFICATION_PROMPT: str = """Classifie la question utilisateur dans exactement une de ces catégories :
- "factual" : question sur le contenu d'une circulaire (définitions, conditions, procédures)
- "relational" : question sur les liens entre circulaires (modifications, abrogations, références)
- "temporal" : question sur l'évolution dans le temps (changements, historique)
- "comparative" : question comparant plusieurs circulaires ou dispositions

Question : {question}

Réponds avec UNIQUEMENT le mot de la catégorie, sans explication."""

RELATIONSHIP_EXTRACTION_PROMPT: str = """Analyse le texte suivant d'une circulaire BCT et identifie TOUTES les références à d'autres circulaires.

Pour chaque référence trouvée, identifie :
1. Le numéro de la circulaire référencée (format YYYY-NN)
2. Le type de relation : MODIFIES, ABROGATES, REFERENCES, COMPLEMENTS, ou CONCERNS
3. L'article concerné si applicable
4. La citation exacte du texte justifiant cette relation

Texte de la circulaire N° {source_number} :
{document_text}
"""
```

##### `backend/agent/tools.py`

```python
"""Tool definitions for the LangGraph agent."""
from typing import List, Dict, Any, Optional

def search_hybrid(
    question: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Full hybrid search: vector + BM25 + graph, fused with RRF, reranked.
    Use for: factual questions, general queries.
    """
    ...

def search_graph_only(
    question: str,
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    """
    Graph-only search: entity extraction → Neo4j traversal → chunk retrieval.
    Use for: relational questions about circular connections.
    """
    ...

def search_bm25_only(
    question: str,
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    """
    BM25-only keyword search.
    Use for: exact term lookups, specific article numbers.
    """
    ...

def get_circular_relations(
    circular_number: str,
) -> Dict[str, Any]:
    """
    Get all relationships for a specific circular from Neo4j.
    Returns: incoming and outgoing relationships with types.
    Use for: "has this circular been modified/abrogated?"
    """
    ...

def get_circular_details(
    circular_number: str,
) -> Dict[str, Any]:
    """
    Get full metadata for a circular from Neo4j.
    Returns: number, title, date, category, status, all relationships.
    """
    ...

def generate_answer(
    question: str,
    context_chunks: List[Dict[str, Any]],
    graph_context: Optional[str] = None,
    question_type: str = "factual",
) -> str:
    """
    Generate an answer using Qwen2.5-7B via Ollama.
    Uses format="json" and Instructor for structured output.
    Retries up to 3 times on malformed JSON.
    """
    ...
```

##### `backend/agent/agent_graph.py`

```python
"""LangGraph StateGraph definition for the KUSOR agent."""
from typing import Dict, Any
from langgraph.graph import StateGraph, END

class KusorAgent:
    """
    LangGraph-based agent that classifies questions and selects
    the optimal retrieval strategy.
    """

    def __init__(
        self,
        hybrid_retriever: "HybridRetriever",
        neo4j_manager: "Neo4jManager",
        ollama_base_url: str = "http://localhost:11434",
        llm_model: str = "qwen2.5:7b",
    ) -> None: ...

    def build_graph(self) -> StateGraph:
        """
        Build the LangGraph StateGraph:
        
        START → classify_question → select_tools → execute_retrieval
              → rerank_results → generate_answer → format_output → END
        """
        ...

    def classify_question(self, state: "AgentState") -> "AgentState":
        """
        Node 1: Classify the question type using the LLM.
        Sets state.question_type.
        """
        ...

    def select_tools(self, state: "AgentState") -> "AgentState":
        """
        Node 2: Based on question_type, select which tools to use.
        
        Strategy mapping:
        - factual     → search_hybrid (all 3 paths)
        - relational  → search_graph_only + get_circular_relations
        - temporal    → search_hybrid + get_circular_relations
        - comparative → search_hybrid (emphasize vector similarity)
        
        Sets state.selected_tools.
        """
        ...

    def execute_retrieval(self, state: "AgentState") -> "AgentState":
        """
        Node 3: Execute selected tools. For hybrid, runs all enabled searchers.
        Sets state.retrieved_chunks.
        """
        ...

    def rerank_results(self, state: "AgentState") -> "AgentState":
        """
        Node 4: Apply cross-encoder reranker to retrieved chunks.
        Sets state.reranked_chunks.
        """
        ...

    def generate_answer(self, state: "AgentState") -> "AgentState":
        """
        Node 5: Call Qwen2.5-7B with system prompt and context.
        Uses Ollama with format="json".
        Sets state.llm_response.
        """
        ...

    def format_output(self, state: "AgentState") -> "AgentState":
        """
        Node 6: Parse LLM response through Instructor + Pydantic AgentResponse schema.
        Auto-retries up to 3 times on malformed JSON.
        Sets state.final_response.
        """
        ...

    def invoke(self, question: str) -> "AgentResponse":
        """
        Public method: run the full agent pipeline for a question.
        Returns an AgentResponse.
        """
        ...
```

##### `backend/agent/tests/__init__.py`

```python
# Empty init
```

##### `backend/agent/tests/test_agent.py`

```python
import pytest
from backend.agent.agent_graph import KusorAgent
from backend.agent.schemas import AgentResponse, QuestionType

class TestKusorAgent:
    def test_factual_question_uses_vector(self) -> None:
        """Factual question should use hybrid retrieval (vector path included)."""
        ...

    def test_factual_question_cites_sources(self) -> None:
        """Answer to factual question must include source citations."""
        ...

    def test_relational_question_uses_graph(self) -> None:
        """Relational question about modifications should use graph path."""
        ...

    def test_relational_question_graph_path_flag(self) -> None:
        """graph_path_used should be True for relational questions."""
        ...

    def test_confidence_score_valid(self) -> None:
        """Confidence score must be a float between 0.0 and 1.0."""
        ...

    def test_output_schema_valid(self) -> None:
        """Response must conform to AgentResponse Pydantic schema."""
        ...

    def test_malformed_json_retry(self) -> None:
        """Agent should retry up to 3 times on malformed JSON from LLM."""
        ...

    def test_no_context_response(self) -> None:
        """If no relevant chunks found, agent should indicate insufficient data."""
        ...
```

#### Acceptance Criteria

- [ ] Question classification correctly identifies factual, relational, temporal, comparative
- [ ] Tool selection maps question types to appropriate retrieval strategies
- [ ] Factual questions use all three retrieval paths (vector + BM25 + graph)
- [ ] Relational questions prioritize graph traversal
- [ ] All answers include source citations with circular number, page, excerpt
- [ ] `confidence_score` is always a float between 0.0 and 1.0
- [ ] `graph_path_used` flag is set correctly
- [ ] Output conforms to `AgentResponse` Pydantic schema
- [ ] Instructor auto-retry handles malformed JSON (up to 3 attempts)
- [ ] All LLM calls use `format="json"` via Ollama
- [ ] All tests pass

#### Verification Commands

```bash
cd ~/kusor
source backend/.venv/bin/activate

# Run tests
python -m pytest backend/agent/tests/test_agent.py -v

# Manual verification: ask a question
python -c "
from backend.agent.agent_graph import KusorAgent
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.retrieval.vector_searcher import VectorSearcher
from backend.retrieval.bm25_searcher import BM25Searcher
from backend.retrieval.graph_searcher import GraphSearcher
from backend.retrieval.reranker import CrossEncoderReranker
from backend.graph.neo4j_manager import Neo4jManager

nm = Neo4jManager()
hr = HybridRetriever(VectorSearcher(), BM25Searcher(), GraphSearcher(nm), CrossEncoderReranker())
agent = KusorAgent(hybrid_retriever=hr, neo4j_manager=nm)

response = agent.invoke('Quelles sont les conditions de la réserve obligatoire?')
print(f'Type: {response.question_type}')
print(f'Confidence: {response.confidence_score}')
print(f'Graph used: {response.graph_path_used}')
print(f'Sources: {len(response.sources)}')
print(f'Answer: {response.answer[:200]}...')
nm.close()
"
```

---

### Module 1 — BCT Circular Collector

**Why fifth**: Pipeline (Module 3) and graph (Module 4) must exist before the collector feeds them.

**Dependencies**: Module 3 (DocumentProcessor), Module 4 (GraphBuilder), Module 2 (PostgreSQL models — see note).

> **Note**: Module 1 depends on PostgreSQL models for metadata storage. Implement the SQLAlchemy models from Module 2 first (just `backend/models/`), then build Module 1, then complete the rest of Module 2.

#### Files to Create

##### `backend/collector/__init__.py`

```python
# Empty init
```

##### `backend/collector/bct_scraper.py`

```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CircularMetadata:
    number: str          # e.g., "2024-01"
    title: str
    date: datetime
    category: str        # e.g., "Politique monétaire", "Supervision bancaire"
    pdf_url: str
    source_page_url: str

class BCTScraper:
    """
    Scrapes BCT (bct.gov.tn) publications page for new circulars.
    Downloads PDFs and triggers the processing + graph pipeline.
    """

    BCT_BASE_URL: str = "https://www.bct.gov.tn"
    CIRCULARS_PAGE: str = "/fr/publications/circulaires"  # Adjust to actual URL
    PDF_DOWNLOAD_DIR: str = "backend/data/circulars"

    def __init__(
        self,
        db_session: Any,  # SQLAlchemy session
        document_processor: "DocumentProcessor",
        graph_builder: "GraphBuilder",
    ) -> None: ...

    def scrape_circulars(self) -> List[CircularMetadata]:
        """
        Parse BCT publications page using requests + BeautifulSoup.
        Extract: number, title, date, category, PDF URL.
        Returns list of all circulars found on the page.
        """
        ...

    def get_new_circulars(
        self,
        scraped: List[CircularMetadata],
    ) -> List[CircularMetadata]:
        """
        Compare scraped circulars against PostgreSQL Document table.
        Return only circulars not yet in the database.
        """
        ...

    def download_pdf(
        self,
        circular: CircularMetadata,
    ) -> Optional[str]:
        """
        Download PDF to backend/data/circulars/{number}.pdf.
        Returns local file path on success, None on failure.
        """
        ...

    def ingest_circular(
        self,
        circular: CircularMetadata,
        pdf_path: str,
    ) -> Dict[str, Any]:
        """
        Full ingestion pipeline for one circular:
        1. Run DocumentProcessor
        2. Run GraphBuilder
        3. Update PostgreSQL metadata (Document record + status)
        4. Log to AuditLog table
        Returns ingestion result summary.
        """
        ...

    def run(self) -> Dict[str, Any]:
        """
        Main entry point. Scrape → filter new → download → ingest each.
        Returns summary: {total_found, new_count, ingested, errors}.
        """
        ...
```

##### `backend/collector/scheduler.py`

```python
from apscheduler.schedulers.background import BackgroundScheduler

class CollectorScheduler:
    """
    Runs BCTScraper on a configurable schedule.
    Default: daily at 06:00 Tunis time (UTC+1).
    """

    def __init__(
        self,
        scraper: "BCTScraper",
        hour: int = 6,
        minute: int = 0,
    ) -> None: ...

    def start(self) -> None:
        """Start the APScheduler background scheduler."""
        ...

    def stop(self) -> None:
        """Shut down the scheduler gracefully."""
        ...

    def run_now(self) -> Dict[str, Any]:
        """Trigger an immediate scraping run (for manual sync)."""
        ...
```

##### `backend/collector/tests/__init__.py`

```python
# Empty init
```

##### `backend/collector/tests/test_bct_scraper.py`

```python
import pytest
from unittest.mock import patch, MagicMock
from backend.collector.bct_scraper import BCTScraper, CircularMetadata

class TestBCTScraper:
    def test_parse_circular_metadata(self) -> None:
        """Mock HTTP response, verify metadata (number, title, date, URL) parsed correctly."""
        ...

    def test_skip_known_circulars(self) -> None:
        """Second run should skip already-ingested circulars."""
        ...

    def test_download_pdf(self) -> None:
        """Mock PDF download, verify file saved to correct path."""
        ...

    def test_ingestion_triggers_pipeline(self) -> None:
        """Verify ingest_circular calls DocumentProcessor and GraphBuilder."""
        ...

    def test_error_handling(self) -> None:
        """Network errors should be logged, not crash the scraper."""
        ...
```

#### Acceptance Criteria

- [ ] Scraper parses BCT publications page and extracts circular metadata
- [ ] Duplicate detection: known circulars are skipped on re-run
- [ ] PDFs download to `backend/data/circulars/`
- [ ] Each new circular triggers `DocumentProcessor` then `GraphBuilder`
- [ ] Ingestion results are logged to PostgreSQL `AuditLog` table
- [ ] APScheduler runs daily at 06:00
- [ ] Manual `run_now()` trigger works
- [ ] All tests pass (with mocked HTTP responses)

#### Verification Commands

```bash
cd ~/kusor
source backend/.venv/bin/activate

# Run tests
python -m pytest backend/collector/tests/test_bct_scraper.py -v

# Manual verification: test scraper with mock
python -c "
from backend.collector.bct_scraper import BCTScraper
# Will fail gracefully if BCT site is unreachable
# scraper = BCTScraper(db_session=..., document_processor=..., graph_builder=...)
# result = scraper.run()
# print(result)
"
```

---

### Module 2 — Flask REST API

**Why sixth**: Exposes the working pipeline via HTTP.

**Dependencies**: All backend modules (3, 4, 5, 6, 1).

> **Note**: Implement `backend/models/` first (needed by Module 1), then complete the rest of Module 2 after Module 1.

#### Files to Create

##### `backend/__init__.py`

```python
# Empty init — marks backend as a package.
```

##### `backend/config.py`

```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
    SQLALCHEMY_DATABASE_URI: str = os.getenv("DATABASE_URL", "postgresql://kusor_user:kusor_password@localhost:5432/kusor_db")
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "kusor_password")
    
    CHROMA_HOST: str = os.getenv("CHROMA_HOST", "localhost")
    CHROMA_PORT: int = int(os.getenv("CHROMA_PORT", "8001"))
    
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen2.5:7b")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

class DevelopmentConfig(Config):
    DEBUG: bool = True
    SQLALCHEMY_ECHO: bool = True

class ProductionConfig(Config):
    DEBUG: bool = False

class TestingConfig(Config):
    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"

config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
```

##### `backend/extensions.py`

```python
"""Flask extensions initialized here, imported in app factory."""
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS

db = SQLAlchemy()
jwt = JWTManager()
```

##### `backend/models/__init__.py`

```python
from backend.models.document import Document
from backend.models.chunk import Chunk
from backend.models.user import User
from backend.models.conversation import ConversationSession, ConversationMessage
from backend.models.audit_log import AuditLog
```

##### `backend/models/document.py`

```python
from backend.extensions import db
from datetime import datetime

class Document(db.Model):
    __tablename__ = "documents"

    id: str            # UUID, primary key
    number: str        # Circular number, e.g. "2024-01", unique
    title: str         # Full title
    date: datetime     # Publication date
    category: str      # e.g. "Politique monétaire"
    url: str           # Original BCT URL
    status: str        # "ACTIVE", "ABROGATED", "MODIFIED"
    indexation_state: str  # "PENDING", "PROCESSING", "INDEXED", "FAILED"
    created_at: datetime
    updated_at: datetime

    # Relationship
    chunks = db.relationship("Chunk", backref="document", lazy="dynamic")
```

##### `backend/models/chunk.py`

```python
from backend.extensions import db

class Chunk(db.Model):
    __tablename__ = "chunks"

    id: str            # UUID, primary key
    document_id: str   # FK → documents.id
    chunk_index: int
    page_number: int
    content: str       # Text content
    embedding_id: str  # ChromaDB embedding ID
```

##### `backend/models/user.py`

```python
from backend.extensions import db
from datetime import datetime

class User(db.Model):
    __tablename__ = "users"

    id: str            # UUID, primary key
    username: str      # Unique
    password_hash: str # bcrypt hashed
    role: str          # "admin" or "user"
    created_at: datetime
```

##### `backend/models/conversation.py`

```python
from backend.extensions import db
from datetime import datetime

class ConversationSession(db.Model):
    __tablename__ = "conversation_sessions"

    id: str            # UUID, primary key
    user_id: str       # FK → users.id
    title: str         # Auto-generated from first question
    created_at: datetime

    messages = db.relationship("ConversationMessage", backref="session", lazy="dynamic")

class ConversationMessage(db.Model):
    __tablename__ = "conversation_messages"

    id: str            # UUID, primary key
    session_id: str    # FK → conversation_sessions.id
    role: str          # "user" or "assistant"
    content: str       # Message text (markdown)
    sources_json: str  # JSON string of source citations
    confidence: float  # 0.0-1.0 (null for user messages)
    created_at: datetime
```

##### `backend/models/audit_log.py`

```python
from backend.extensions import db
from datetime import datetime

class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id: str            # UUID, primary key
    user_id: str       # FK → users.id (nullable for system actions)
    action: str        # "DOCUMENT_UPLOADED", "SEARCH_PERFORMED", "SYNC_TRIGGERED", etc.
    entity_type: str   # "Document", "Circular", "User", etc.
    entity_id: str     # ID of the affected entity (nullable)
    details_json: str  # JSON string with additional context
    created_at: datetime
```

##### `backend/app.py`

```python
from flask import Flask
from backend.config import config_map
from backend.extensions import db, jwt

def create_app(config_name: str = "development") -> Flask:
    """
    Flask application factory.
    
    1. Create Flask app
    2. Load config
    3. Initialize extensions (db, jwt, CORS)
    4. Register Flask-RESTX API with all namespaces
    5. Initialize services (Neo4jManager, HybridRetriever, KusorAgent, etc.)
    6. Start collector scheduler (if not testing)
    7. Return app
    """
    ...
```

##### `backend/migrations/` — Alembic

```bash
# Generated via:
cd ~/kusor/backend
source .venv/bin/activate
flask db init    # Creates migrations/ directory
flask db migrate -m "initial schema"
flask db upgrade
```

##### `backend/middleware/__init__.py`

```python
# Empty init
```

##### `backend/middleware/auth.py`

```python
"""JWT authentication middleware and helpers."""
from functools import wraps

def admin_required(fn):
    """Decorator: requires JWT token with role='admin'."""
    ...

def audit_action(action: str, entity_type: str):
    """Decorator: logs the action to AuditLog after execution."""
    ...
```

##### `backend/middleware/error_handlers.py`

```python
"""Global error handlers for the Flask app."""

def register_error_handlers(app):
    """Register error handlers for 400, 401, 403, 404, 500."""
    ...
```

##### `backend/routes/__init__.py`

```python
# Empty init
```

##### `backend/routes/auth.py`

```python
"""Auth namespace: login, current user."""
from flask_restx import Namespace, Resource

api = Namespace("auth", description="Authentication operations")

@api.route("/login")
class Login(Resource):
    @api.doc("user_login", description="Authenticate and receive JWT token")
    def post(self):
        """POST /api/auth/login — returns {access_token, user}"""
        ...

@api.route("/me")
class CurrentUser(Resource):
    @api.doc("current_user", description="Get current authenticated user")
    def get(self):
        """GET /api/auth/me — returns current user profile"""
        ...
```

##### `backend/routes/documents.py`

```python
"""Documents namespace: CRUD + processing."""
from flask_restx import Namespace, Resource

api = Namespace("documents", description="Document management")

@api.route("/")
class DocumentList(Resource):
    @api.doc("list_documents")
    def get(self):
        """GET /api/documents/ — list all documents with pagination"""
        ...

@api.route("/upload")
class DocumentUpload(Resource):
    @api.doc("upload_document")
    def post(self):
        """POST /api/documents/upload — upload a PDF, trigger processing pipeline"""
        ...

@api.route("/<string:id>/status")
class DocumentStatus(Resource):
    @api.doc("document_status")
    def get(self, id: str):
        """GET /api/documents/:id/status — get indexation state"""
        ...

@api.route("/<string:id>")
class DocumentDetail(Resource):
    @api.doc("delete_document")
    def delete(self, id: str):
        """DELETE /api/documents/:id — remove document and its chunks"""
        ...

@api.route("/<string:id>/reindex")
class DocumentReindex(Resource):
    @api.doc("reindex_document")
    def post(self, id: str):
        """POST /api/documents/:id/reindex — re-process and re-index"""
        ...
```

##### `backend/routes/search.py`

```python
"""Search namespace: hybrid, vector-only, graph-only."""
from flask_restx import Namespace, Resource

api = Namespace("search", description="Search operations")

@api.route("/hybrid")
class HybridSearch(Resource):
    @api.doc("hybrid_search")
    def post(self):
        """POST /api/search/hybrid — full hybrid search (vector + BM25 + graph + reranker)"""
        ...

@api.route("/vector")
class VectorSearch(Resource):
    @api.doc("vector_search")
    def post(self):
        """POST /api/search/vector — vector-only search"""
        ...

@api.route("/graph")
class GraphSearch(Resource):
    @api.doc("graph_search")
    def post(self):
        """POST /api/search/graph — graph-only search"""
        ...
```

##### `backend/routes/chat.py`

```python
"""Chat namespace: messaging and session management."""
from flask_restx import Namespace, Resource

api = Namespace("chat", description="Chat operations")

@api.route("/message")
class ChatMessage(Resource):
    @api.doc("send_message")
    def post(self):
        """
        POST /api/chat/message
        Body: {session_id?: str, message: str}
        Returns: AgentResponse + session_id (creates new session if not provided)
        Calls KusorAgent.invoke() internally.
        """
        ...

@api.route("/history/<string:session_id>")
class ChatHistory(Resource):
    @api.doc("chat_history")
    def get(self, session_id: str):
        """GET /api/chat/history/:session_id — returns all messages in a session"""
        ...

@api.route("/sessions")
class ChatSessions(Resource):
    @api.doc("list_sessions")
    def get(self):
        """GET /api/chat/sessions — list all sessions for current user"""
        ...
```

##### `backend/routes/admin.py`

```python
"""Admin namespace: stats and manual sync."""
from flask_restx import Namespace, Resource

api = Namespace("admin", description="Admin operations")

@api.route("/stats")
class AdminStats(Resource):
    @api.doc("admin_stats")
    def get(self):
        """
        GET /api/admin/stats
        Returns: {document_count, circular_count, chunk_count,
                  last_sync_at, neo4j_stats, chroma_stats}
        """
        ...

@api.route("/sync")
class AdminSync(Resource):
    @api.doc("manual_sync")
    def post(self):
        """POST /api/admin/sync — trigger immediate BCT scraper run"""
        ...
```

##### `backend/routes/graph.py`

```python
"""Graph namespace: subgraph visualization data."""
from flask_restx import Namespace, Resource

api = Namespace("graph", description="Knowledge graph operations")

@api.route("/subgraph")
class GraphSubgraph(Resource):
    @api.doc("graph_subgraph", params={"circular": "Circular number to center the subgraph on"})
    def get(self):
        """
        GET /api/graph/subgraph?circular=2024-01
        Returns: {nodes: [{id, label, type, properties}], edges: [{source, target, type}]}
        Formatted for Angular ngx-graph consumption.
        """
        ...
```

#### Acceptance Criteria

- [ ] `create_app()` factory creates Flask app with all extensions
- [ ] All SQLAlchemy models create corresponding PostgreSQL tables via Alembic
- [ ] `POST /api/auth/login` returns JWT token for valid credentials
- [ ] `GET /api/auth/me` returns current user with valid JWT
- [ ] `POST /api/documents/upload` accepts PDF and triggers processing pipeline
- [ ] `POST /api/chat/message` calls KusorAgent and returns AgentResponse
- [ ] `POST /api/search/hybrid` returns search results
- [ ] `GET /api/graph/subgraph?circular=X` returns ngx-graph compatible data
- [ ] `GET /api/admin/stats` returns system statistics
- [ ] `POST /api/admin/sync` triggers BCT scraper
- [ ] All endpoints documented in Swagger UI at `/api/docs`
- [ ] JWT auth required on all endpoints except `/api/auth/login`
- [ ] Admin-only endpoints (`/api/admin/*`) check role
- [ ] Audit logging middleware records all actions
- [ ] CORS configured for Angular dev server (`localhost:4200`)

#### Verification Commands

```bash
cd ~/kusor
source backend/.venv/bin/activate

# Set up database
export FLASK_APP=backend.app:create_app
flask db init
flask db migrate -m "initial schema"
flask db upgrade

# Run the app
flask run --port 5000

# In another terminal:
# Test Swagger UI
curl http://localhost:5000/api/docs

# Test login (after creating initial admin user)
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Test stats
curl http://localhost:5000/api/admin/stats \
  -H "Authorization: Bearer <token>"

# Test chat
curl -X POST http://localhost:5000/api/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"message": "Quelles sont les conditions de reserve obligatoire?"}'
```

---

### Module 7 — Angular Frontend

**Why last**: Consumes the completed API.

**Dependencies**: Module 2 (Flask API must be running).

**Project location**: `frontend/kusor-ui/`

**Angular version**: v21 (already scaffolded, uses standalone components, SCSS)

#### Files to Create

All paths relative to `frontend/kusor-ui/src/app/`.

##### Core Services

###### `core/services/auth.service.ts`

```typescript
@Injectable({ providedIn: 'root' })
export class AuthService {
  login(username: string, password: string): Observable<LoginResponse>;
  logout(): void;
  getToken(): string | null;
  getCurrentUser(): Observable<User>;
  isAuthenticated(): boolean;
  isAdmin(): boolean;
}
```

###### `core/services/api.service.ts`

```typescript
@Injectable({ providedIn: 'root' })
export class ApiService {
  // Documents
  getDocuments(page?: number, limit?: number): Observable<PaginatedResponse<Document>>;
  uploadDocument(file: File): Observable<UploadResponse>;
  getDocumentStatus(id: string): Observable<DocumentStatus>;
  deleteDocument(id: string): Observable<void>;
  reindexDocument(id: string): Observable<void>;
  
  // Search
  searchHybrid(query: string): Observable<SearchResponse>;
  searchVector(query: string): Observable<SearchResponse>;
  searchGraph(query: string): Observable<SearchResponse>;
  
  // Chat
  sendMessage(message: string, sessionId?: string): Observable<ChatResponse>;
  getChatHistory(sessionId: string): Observable<ChatMessage[]>;
  getChatSessions(): Observable<ChatSession[]>;
  
  // Admin
  getStats(): Observable<AdminStats>;
  triggerSync(): Observable<SyncResult>;
  
  // Graph
  getSubgraph(circularNumber: string): Observable<GraphData>;
}
```

###### `core/guards/auth.guard.ts`

```typescript
export const authGuard: CanActivateFn = (route, state) => { ... };
export const adminGuard: CanActivateFn = (route, state) => { ... };
```

###### `core/interceptors/jwt.interceptor.ts`

```typescript
export const jwtInterceptor: HttpInterceptorFn = (req, next) => { ... };
```

###### `core/models/` — TypeScript interfaces

```typescript
// models/user.model.ts
export interface User { id: string; username: string; role: 'admin' | 'user'; }

// models/document.model.ts
export interface Document { id: string; number: string; title: string; date: string; category: string; status: string; indexation_state: string; }

// models/chat.model.ts
export interface ChatMessage { id: string; role: 'user' | 'assistant'; content: string; sources: SourceCitation[]; confidence: number; created_at: string; }
export interface SourceCitation { circular_number: string; title: string; page: number; excerpt: string; }
export interface ChatSession { id: string; title: string; created_at: string; }

// models/graph.model.ts
export interface GraphNode { id: string; label: string; type: 'Circular' | 'Entity'; properties: Record<string, any>; }
export interface GraphEdge { source: string; target: string; type: string; }
export interface GraphData { nodes: GraphNode[]; edges: GraphEdge[]; }
```

##### Pages / Screens

Build in this order:

###### 1. Auth — `pages/login/`

- `login.component.ts` — Login form with username/password
- `login.component.html` — Styled login page with KUSOR branding
- `login.component.scss` — Dark theme, glassmorphism card

###### 2. Dashboard — `pages/dashboard/`

- `dashboard.component.ts` — Main dashboard view
- `dashboard.component.html` — Layout:
  - Stat cards: document count, circular count, chunk count, last sync time
  - Recent activity feed (from AuditLog)
  - Sync status indicator (green/yellow/red)
- `dashboard.component.scss`

###### 3. Chat — `pages/chat/`

- `chat.component.ts` — Main chat view
- `chat.component.html` — Layout:
  - Left sidebar: session list (chat history)
  - Center: message thread with markdown rendering (via `marked`)
  - Right panel: source citation cards (circular number, title, page, excerpt)
  - Bottom: message input with send button
  - Confidence badge on each assistant message
  - Related circulars as clickable chips
- `chat.component.scss`

###### 4. Admin/Documents — `pages/admin/`

- `documents.component.ts` — Document management
- `documents.component.html` — Layout:
  - Document list table (sortable, filterable)
  - Upload dialog (drag-and-drop file zone)
  - Manual sync button
  - Document detail view (click to expand: entity list, chunk count, status)
- `documents.component.scss`

###### 5. Graph — `pages/graph/`

- `graph.component.ts` — Graph visualization
- `graph.component.html` — Layout:
  - ngx-graph force-directed visualization
  - Node styling: Circular = navy (#1a237e), Entity = gold (#ffc107)
  - Edge colours by relationship type:
    - MODIFIES = orange (#ff9800)
    - ABROGATES = red (#f44336)
    - REFERENCES = blue (#2196f3)
    - COMPLEMENTS = green (#4caf50)
    - CONCERNS = purple (#9c27b0)
    - MENTIONS = grey (#9e9e9e)
  - Click-to-detail side panel (shows circular properties)
  - Filters: by relationship type (checkboxes), by date range
- `graph.component.scss`

##### Shared Components

###### `shared/components/navbar/navbar.component.ts`

- Top navigation bar with KUSOR logo, page links, user menu, logout

###### `shared/components/loading-spinner/loading-spinner.component.ts`

- Reusable loading state indicator

###### `shared/components/confidence-badge/confidence-badge.component.ts`

- Color-coded badge: green (≥0.8), yellow (0.5-0.79), red (<0.5)

##### Routing — `app.routes.ts`

```typescript
export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: '', canActivate: [authGuard], children: [
    { path: 'dashboard', component: DashboardComponent },
    { path: 'chat', component: ChatComponent },
    { path: 'admin', component: DocumentsComponent, canActivate: [adminGuard] },
    { path: 'graph', component: GraphComponent },
    { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  ]},
  { path: '**', redirectTo: 'login' },
];
```

##### App Configuration — `app.config.ts`

```typescript
export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    provideHttpClient(withInterceptors([jwtInterceptor])),
  ],
};
```

##### Environment — `environments/`

```typescript
// environment.ts
export const environment = {
  production: false,
  apiUrl: 'http://localhost:5000/api',
};

// environment.prod.ts
export const environment = {
  production: true,
  apiUrl: '/api',
};
```

#### Acceptance Criteria

- [ ] Login page authenticates against Flask API and stores JWT
- [ ] Auth guard redirects unauthenticated users to login
- [ ] Admin guard blocks non-admin users from admin routes
- [ ] JWT token is sent in Authorization header on all API requests
- [ ] Dashboard shows live stats from `/api/admin/stats`
- [ ] Chat sends messages to `/api/chat/message` and renders markdown responses
- [ ] Source citations display as cards with circular number, page, excerpt
- [ ] Confidence badge color-codes correctly
- [ ] Document list loads from API, upload triggers processing
- [ ] Graph visualization renders ngx-graph with correct node/edge colours
- [ ] Click-to-detail side panel shows circular properties
- [ ] Graph filters work (relationship type, date range)
- [ ] SCSS styling: dark theme, glassmorphism, smooth animations
- [ ] Responsive layout (desktop-first, usable on tablet)

#### Verification Commands

```bash
cd ~/kusor/frontend/kusor-ui

# Install dependencies (already done, but just in case)
npm install

# Run dev server
npm run start
# → opens http://localhost:4200

# Build production bundle (validation)
npm run build
```

---

## 6. Key Design Decisions

### 6.1 Why structural pre-segmentation before semantic chunking

BCT circulars have a rigid legal structure: Article 1, Article 2, etc. Semantic chunking alone (which splits on embedding distance) may cut an article in the middle, producing chunks that reference "the conditions above" without including them. Pre-segmenting at structural boundaries (Article, Titre, Chapitre, Section) ensures each article is an atomic unit. Semantic chunking then operates *within* segments only, splitting further only where meaning boundaries exist inside a long article. This guarantees that legal articles are never split across chunks and every chunk is self-contained.

### 6.2 Why Reciprocal Rank Fusion (RRF) over simple score averaging

Scores from vector search (cosine similarity, 0-1), BM25 (unbounded positive), and graph search (hop distance) are on incomparable scales. Simple averaging or weighted sum would require ad-hoc normalization that breaks when score distributions shift. RRF uses only **rank positions** (not raw scores), making it scale-invariant. The formula `score = Σ 1/(k + rank)` with k=60 is well-studied (Cormack et al., 2009) and outperforms all score normalization methods in heterogeneous fusion scenarios. k=60 dampens the influence of very high ranks, giving a balanced blend.

### 6.3 Why cross-encoder reranker after fusion

Bi-encoder embeddings (nomic-embed-text) independently encode query and document, losing fine-grained token interactions. A cross-encoder (ms-marco-MiniLM-L-6-v2) takes the (query, document) pair as a single input, enabling full attention between query and document tokens. This captures nuances like negation, conditional clauses, and multi-hop reasoning that bi-encoders miss. Applying it after RRF fusion means we rerank only the top-20 candidates (not the full corpus), keeping latency under 200ms on the RTX 4060.

### 6.4 Why MERGE in Cypher for entity nodes

Entity names like "BCT" or "Ministère des Finances" will appear across many circulars. Using `CREATE` would produce thousands of duplicate nodes. `MERGE` performs an upsert: create the node only if it doesn't already exist (matching on `name` + `type`), otherwise reuse the existing node. This is critical for graph queries: searching for "BCT" should find one node connected to all its circulars, not thousands of disconnected duplicates.

### 6.5 Why Instructor + Pydantic on top of format="json"

Ollama's `format="json"` constrains the LLM to output valid JSON syntax, but does not guarantee the JSON matches our expected schema. The LLM might output `{"réponse": "..."}` instead of `{"answer": "..."}`. Instructor wraps the LLM call, validates the response against a Pydantic model, and auto-retries (up to 3 times) with the validation error message injected into the prompt. This creates a reliable structured output pipeline: `format="json"` ensures syntactic validity, Instructor+Pydantic ensures semantic validity.

### 6.6 Why NEFTune + mixed dataset if fine-tuning is pursued

NEFTune (Noise-Enhanced Fine-Tuning) adds small uniform noise to embedding vectors during training, acting as a regularizer that reduces overfitting on small datasets. BCT circulars are a niche domain with limited training data. A mixed dataset (regulatory Q&A + general French text) prevents catastrophic forgetting. This is noted here as a future enhancement — the current system uses the base Qwen2.5-7B without fine-tuning.

### 6.7 Why Flask-RESTX over plain Flask

Flask-RESTX provides: (1) automatic Swagger/OpenAPI documentation from `@api.doc()` decorators — a bank requirement, (2) request/response marshalling with `api.model()`, (3) namespace-based route organization, (4) built-in input validation. Plain Flask would require separate libraries for each of these. Flask-RESTX is a maintained fork of Flask-RESTPlus with Python 3.11 support.

---

## 7. Neo4j Graph Schema

### Node Types

```cypher
(:Circular {
    id: STRING,           -- UUID
    number: STRING,       -- e.g., "2024-01" (UNIQUE)
    title: STRING,
    date: STRING,         -- ISO 8601: "2024-01-15"
    category: STRING,     -- e.g., "Politique monétaire"
    url: STRING,          -- Original BCT URL
    status: STRING        -- "ACTIVE" | "ABROGATED" | "MODIFIED"
})

(:Entity {
    name: STRING,         -- e.g., "BCT", "Ministère des Finances" (UNIQUE with type)
    type: STRING          -- "ORG" | "LAW" | "CIRCULAR_REF"
})
```

### Relationship Types

```cypher
-- A circular abrogates another (repeals it entirely)
(:Circular)-[:ABROGATES]->(:Circular)

-- A circular modifies a specific article of another
(:Circular)-[:MODIFIES {article: STRING}]->(:Circular)

-- A circular references another (cites it)
(:Circular)-[:REFERENCES]->(:Circular)

-- A circular complements another (extends it)
(:Circular)-[:COMPLEMENTS]->(:Circular)

-- A circular concerns the same subject as another
(:Circular)-[:CONCERNS]->(:Circular)

-- A circular mentions an entity
(:Circular)-[:MENTIONS]->(:Entity)
```

### Indexes to Create

```cypher
CREATE CONSTRAINT circular_number_unique IF NOT EXISTS
FOR (c:Circular) REQUIRE c.number IS UNIQUE;

CREATE INDEX circular_date_index IF NOT EXISTS
FOR (c:Circular) ON (c.date);

CREATE INDEX circular_status_index IF NOT EXISTS
FOR (c:Circular) ON (c.status);

CREATE INDEX entity_name_index IF NOT EXISTS
FOR (e:Entity) ON (e.name);

CREATE CONSTRAINT entity_unique IF NOT EXISTS
FOR (e:Entity) REQUIRE (e.name, e.type) IS UNIQUE;
```

---

## 8. PostgreSQL Schema

### Table: `documents`

| Column           | Type          | Constraints                    |
|-----------------|---------------|-------------------------------|
| id              | UUID          | PRIMARY KEY, DEFAULT gen_random_uuid() |
| number          | VARCHAR(50)   | UNIQUE, NOT NULL              |
| title           | TEXT          | NOT NULL                      |
| date            | TIMESTAMP     |                               |
| category        | VARCHAR(100)  |                               |
| url             | TEXT          |                               |
| status          | VARCHAR(20)   | DEFAULT 'ACTIVE'              |
| indexation_state| VARCHAR(20)   | DEFAULT 'PENDING'             |
| created_at      | TIMESTAMP     | DEFAULT NOW()                 |
| updated_at      | TIMESTAMP     | DEFAULT NOW()                 |

### Table: `chunks`

| Column       | Type        | Constraints                          |
|-------------|-------------|--------------------------------------|
| id          | UUID        | PRIMARY KEY, DEFAULT gen_random_uuid() |
| document_id | UUID        | FK → documents.id, ON DELETE CASCADE |
| chunk_index | INTEGER     | NOT NULL                             |
| page_number | INTEGER     |                                      |
| content     | TEXT        | NOT NULL                             |
| embedding_id| VARCHAR(255)|                                      |

### Table: `users`

| Column        | Type         | Constraints                          |
|--------------|--------------|--------------------------------------|
| id           | UUID         | PRIMARY KEY, DEFAULT gen_random_uuid() |
| username     | VARCHAR(100) | UNIQUE, NOT NULL                     |
| password_hash| VARCHAR(255) | NOT NULL                             |
| role         | VARCHAR(20)  | NOT NULL, DEFAULT 'user'             |
| created_at   | TIMESTAMP    | DEFAULT NOW()                        |

### Table: `conversation_sessions`

| Column     | Type        | Constraints                          |
|-----------|-------------|--------------------------------------|
| id        | UUID        | PRIMARY KEY, DEFAULT gen_random_uuid() |
| user_id   | UUID        | FK → users.id                        |
| title     | VARCHAR(255)|                                      |
| created_at| TIMESTAMP   | DEFAULT NOW()                        |

### Table: `conversation_messages`

| Column       | Type        | Constraints                                 |
|-------------|-------------|---------------------------------------------|
| id          | UUID        | PRIMARY KEY, DEFAULT gen_random_uuid()       |
| session_id  | UUID        | FK → conversation_sessions.id, ON DELETE CASCADE |
| role        | VARCHAR(20) | NOT NULL ('user' or 'assistant')            |
| content     | TEXT        | NOT NULL                                    |
| sources_json| TEXT        | JSON string, nullable                       |
| confidence  | FLOAT       | Nullable (null for user messages)           |
| created_at  | TIMESTAMP   | DEFAULT NOW()                               |

### Table: `audit_logs`

| Column       | Type         | Constraints                          |
|-------------|--------------|--------------------------------------|
| id          | UUID         | PRIMARY KEY, DEFAULT gen_random_uuid() |
| user_id     | UUID         | FK → users.id, NULLABLE              |
| action      | VARCHAR(100) | NOT NULL                             |
| entity_type | VARCHAR(50)  |                                      |
| entity_id   | VARCHAR(255) |                                      |
| details_json| TEXT         | JSON string                          |
| created_at  | TIMESTAMP    | DEFAULT NOW()                        |

---

## 9. ChromaDB Collections

### Collection: `kusor_documents`

| Metadata Field    | Type   | Description                              |
|------------------|--------|------------------------------------------|
| document_id      | string | UUID of the parent document              |
| chunk_index      | int    | Position of chunk within the document    |
| page_number      | int    | PDF page number where chunk content starts |
| source_filename  | string | Original PDF filename                    |
| circular_number  | string | BCT circular number (e.g., "2024-01")    |

**Embedding model**: `nomic-embed-text` via Ollama (768 dimensions)

**Distance metric**: Cosine similarity (default)

---

## 10. Environment Variables Reference

| Variable          | Description                                        | Default / Example                                           |
|------------------|----------------------------------------------------|-------------------------------------------------------------|
| `FLASK_ENV`      | Flask environment mode                             | `development`                                               |
| `SECRET_KEY`     | Flask secret key for session signing               | Generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `JWT_SECRET_KEY` | Secret key for JWT token signing                   | Generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `NEO4J_URI`      | Neo4j Bolt protocol URI                            | `bolt://localhost:7687`                                     |
| `NEO4J_USER`     | Neo4j username                                     | `neo4j`                                                     |
| `NEO4J_PASSWORD` | Neo4j password                                     | `kusor_password`                                            |
| `CHROMA_HOST`    | ChromaDB server hostname                           | `localhost`                                                 |
| `CHROMA_PORT`    | ChromaDB server port                               | `8001`                                                      |
| `DATABASE_URL`   | PostgreSQL connection string                       | `postgresql://kusor_user:kusor_password@localhost:5432/kusor_db` |
| `OLLAMA_BASE_URL`| Ollama API base URL                                | `http://localhost:11434`                                    |
| `LLM_MODEL`     | Ollama model name for text generation              | `qwen2.5:7b`                                               |
| `EMBEDDING_MODEL`| Ollama model name for embeddings                   | `nomic-embed-text`                                          |

**Variables to add to `.env` (not yet present)**:

| Variable                  | Description                              | Value                                   |
|--------------------------|------------------------------------------|-----------------------------------------|
| `CROSS_ENCODER_MODEL`    | Cross-encoder model for reranking        | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| `BM25_INDEX_PATH`        | Path to persisted BM25 index             | `backend/data/bm25_index.pkl`           |
| `CIRCULARS_DIR`          | Directory for downloaded circular PDFs   | `backend/data/circulars`                |
| `SPACY_MODEL`            | spaCy model for French NER              | `fr_core_news_lg`                       |
| `CHROMA_COLLECTION`      | ChromaDB collection name                 | `kusor_documents`                       |
| `SCHEDULER_HOUR`         | Hour for daily scraper run (0-23)        | `6`                                     |
| `SCHEDULER_MINUTE`       | Minute for daily scraper run (0-59)      | `0`                                     |

---

## 11. Common Failure Modes and Fixes

### Module 3 — Document Processing

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: No module named 'spacy'` | spaCy not installed | `pip install spacy && python -m spacy download fr_core_news_lg` |
| `OSError: [E050] Can't find model 'fr_core_news_lg'` | spaCy model not downloaded | `python -m spacy download fr_core_news_lg` |
| `TesseractNotFoundError` | Tesseract OCR not installed system-wide | `sudo apt-get install tesseract-ocr tesseract-ocr-fra` |
| `chromadb.errors.InvalidCollectionException` | Collection doesn't exist | First call to `_store_in_chromadb` should use `get_or_create_collection()` |
| `FileNotFoundError: bm25_index.pkl` | First run, no index yet | `_update_bm25_index` should create a new index if file doesn't exist |
| `RuntimeError: CUDA out of memory` during embedding | Too many chunks embedded at once | Batch embeddings in groups of 32 |

### Module 4 — GraphRAG

| Error | Cause | Fix |
|-------|-------|-----|
| `neo4j.exceptions.ServiceUnavailable` | Neo4j not running | `cd docker && docker-compose up -d neo4j` |
| `neo4j.exceptions.AuthError` | Wrong password | Check `NEO4J_AUTH` in docker-compose matches `NEO4J_PASSWORD` in `.env` |
| `neo4j.exceptions.ClientError: ... APOC not found` | APOC plugin not loaded | Verify `NEO4J_PLUGINS: '["apoc"]'` in docker-compose and restart container |
| `ConstraintValidationFailedError` | Duplicate circular number | Use `MERGE` not `CREATE` for all node creation |
| Instructor returns empty relationships | LLM hallucinating or not understanding French legal text | Improve `RELATIONSHIP_EXTRACTION_PROMPT`, increase temperature to 0.3 |

### Module 5 — Hybrid RAG

| Error | Cause | Fix |
|-------|-------|-----|
| `chromadb.errors.NoDatapointsException` | Empty collection | Process at least one document first (Module 3) |
| `FileNotFoundError: bm25_index.pkl` | No BM25 index built | Process at least one document first (Module 3) |
| `torch.cuda.OutOfMemoryError` in cross-encoder | Reranking too many chunks | Reduce reranker input from top-20 to top-10 |
| `ValueError: Inconsistent BM25 corpus` | Index corrupted after partial update | Delete `bm25_index.pkl` and reprocess all documents |
| All results come from one searcher only | Other searchers returning empty | Verify all three data stores have data; check logs |

### Module 6 — LangGraph Agent

| Error | Cause | Fix |
|-------|-------|-----|
| `ollama.ResponseError: model not found` | Wrong model name | Verify `LLM_MODEL=qwen2.5:7b` matches `ollama list` output |
| `instructor.exceptions.InstructorRetryException` | LLM consistently produces invalid schema | Simplify `AgentResponse` schema or increase retry count |
| `pydantic.ValidationError: confidence_score > 1.0` | LLM outputs score > 1 | Add `Field(ge=0.0, le=1.0)` constraint and let Instructor retry |
| Agent classifies all questions as "factual" | Classification prompt too weak | Add few-shot examples to `CLASSIFICATION_PROMPT` |
| Very slow responses (>30s) | Sequential tool execution | Ensure `execute_retrieval` runs searchers in parallel (asyncio/threading) |
| `ConnectionRefusedError: Ollama` | Ollama not running | `ollama serve` or `systemctl start ollama` |

### Module 1 — BCT Collector

| Error | Cause | Fix |
|-------|-------|-----|
| `requests.exceptions.SSLError` | BCT site SSL certificate issues | Set `verify=False` or update certifi |
| `AttributeError: 'NoneType' ... find` | BCT page structure changed | Update BeautifulSoup selectors to match new HTML |
| `psycopg2.OperationalError: connection refused` | PostgreSQL not running | `cd docker && docker-compose up -d postgres` |
| Duplicate circulars ingested | Race condition in duplicate check | Use `INSERT ... ON CONFLICT DO NOTHING` or check within transaction |

### Module 2 — Flask API

| Error | Cause | Fix |
|-------|-------|-----|
| `sqlalchemy.exc.OperationalError: connection refused` | PostgreSQL not running | `cd docker && docker-compose up -d postgres` |
| `flask_jwt_extended.exceptions.NoAuthorizationError` | Missing or invalid JWT | Include `Authorization: Bearer <token>` header |
| `werkzeug.exceptions.RequestEntityTooLarge` | PDF upload too large | Set `app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024` (50MB) |
| CORS errors from Angular | Missing CORS config | Ensure `CORS(app, origins=["http://localhost:4200"])` |
| Swagger UI blank page | Flask-RESTX blueprint not registered | Verify `api.init_app(app)` in `create_app()` |

### Module 7 — Angular Frontend

| Error | Cause | Fix |
|-------|-------|-----|
| `HttpErrorResponse: 0 Unknown Error` | CORS not configured on backend | Add `flask-cors` with `localhost:4200` origin |
| `NullInjectorError: No provider for HttpClient` | Missing `provideHttpClient()` | Add to `app.config.ts` providers |
| ngx-graph `Cannot read property 'nodes' of undefined` | API returns null graph data | Add null check in component, show empty state |
| JWT token expired | Token lifetime too short | Set `JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=24)` on backend |
| SCSS compilation error | Missing Angular Material / wrong import | Use vanilla CSS variables, avoid `@angular/material` unless added |

---

## 12. Prompt Templates

### 12.1 System Prompt for Answer Generation

```text
Tu es KUSOR, un assistant réglementaire intelligent spécialisé dans les circulaires de la Banque Centrale de Tunisie (BCT). Tu réponds UNIQUEMENT en te basant sur les documents fournis dans le contexte.

RÈGLES STRICTES :
1. Réponds UNIQUEMENT à partir des extraits de circulaires fournis dans le contexte. Ne génère JAMAIS d'information non présente dans le contexte.
2. Cite chaque affirmation avec la source exacte au format [Circulaire N° XXXX-XX, p. Y].
3. Si le contexte ne contient pas suffisamment d'information pour répondre, dis-le explicitement : "Les documents disponibles ne me permettent pas de répondre à cette question."
4. Si une circulaire a été abrogée ou modifiée selon le graphe de connaissances, signale-le clairement : "⚠️ Attention : cette circulaire a été [modifiée/abrogée] par la circulaire N° XXXX-XX."
5. Réponds toujours en français.
6. Structure ta réponse avec des paragraphes clairs. Utilise des listes à puces pour les énumérations.
7. Pour les questions relationnelles (modifications, abrogations), présente la chaîne chronologique complète.
8. Indique ton niveau de confiance : élevé (>0.8) si plusieurs sources convergent, moyen (0.5-0.8) si une seule source, faible (<0.5) si le contexte est partiel.

CONTEXTE :
{context}

INFORMATIONS DU GRAPHE DE CONNAISSANCES :
{graph_context}
```

### 12.2 Question Classification Prompt

```text
Classifie la question utilisateur dans exactement une de ces catégories :
- "factual" : question sur le contenu d'une circulaire (définitions, conditions, procédures)
- "relational" : question sur les liens entre circulaires (modifications, abrogations, références)
- "temporal" : question sur l'évolution dans le temps (changements, historique)
- "comparative" : question comparant plusieurs circulaires ou dispositions

Question : {question}

Réponds avec UNIQUEMENT le mot de la catégorie, sans explication.
```

### 12.3 Relationship Extraction Prompt (for LLM-based extraction in GraphBuilder)

```text
Analyse le texte suivant d'une circulaire BCT et identifie TOUTES les références à d'autres circulaires.

Pour chaque référence trouvée, identifie :
1. Le numéro de la circulaire référencée (format YYYY-NN)
2. Le type de relation : MODIFIES, ABROGATES, REFERENCES, COMPLEMENTS, ou CONCERNS
3. L'article concerné si applicable
4. La citation exacte du texte justifiant cette relation

Texte de la circulaire N° {source_number} :
{document_text}
```

### 12.4 Pydantic Output Schema

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class QuestionType(str, Enum):
    FACTUAL = "factual"
    RELATIONAL = "relational"
    TEMPORAL = "temporal"
    COMPARATIVE = "comparative"

class SourceCitation(BaseModel):
    circular_number: str = Field(
        description="BCT circular number, e.g. '2024-01'"
    )
    title: str = Field(
        description="Title of the circular"
    )
    page: int = Field(
        description="Page number in the original PDF"
    )
    excerpt: str = Field(
        description="Exact excerpt from the circular supporting the claim"
    )

class AgentResponse(BaseModel):
    answer: str = Field(
        description="Complete answer in French, with inline citations [Circulaire N° XXXX-XX, p. Y]"
    )
    sources: List[SourceCitation] = Field(
        description="All source citations referenced in the answer"
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in the completeness and accuracy of the answer"
    )
    related_circulars: List[str] = Field(
        default_factory=list,
        description="Circular numbers that are related but not directly cited"
    )
    graph_path_used: bool = Field(
        description="Whether Neo4j graph traversal was used to answer this question"
    )
    question_type: QuestionType = Field(
        description="The classified type of the original question"
    )
```

---

## 13. Project File Tree (Target State)

```
~/kusor/
├── CLAUDE.md                          ← This file
├── backend/
│   ├── __init__.py
│   ├── .env
│   ├── .venv/
│   ├── app.py                         ← Flask application factory
│   ├── config.py                      ← Config classes
│   ├── extensions.py                  ← Flask extensions (db, jwt)
│   ├── data/
│   │   ├── circulars/                 ← Downloaded PDFs
│   │   └── bm25_index.pkl            ← Persisted BM25 index
│   ├── models/
│   │   ├── __init__.py
│   │   ├── document.py
│   │   ├── chunk.py
│   │   ├── user.py
│   │   ├── conversation.py
│   │   └── audit_log.py
│   ├── migrations/                    ← Alembic migrations
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── document_processor.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       └── test_document_processor.py
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── neo4j_manager.py
│   │   ├── graph_builder.py
│   │   ├── cypher_queries.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       └── test_graph_builder.py
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── schemas.py
│   │   ├── vector_searcher.py
│   │   ├── bm25_searcher.py
│   │   ├── graph_searcher.py
│   │   ├── reranker.py
│   │   ├── hybrid_retriever.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       └── test_hybrid_retriever.py
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── schemas.py
│   │   ├── prompts.py
│   │   ├── tools.py
│   │   ├── agent_graph.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       └── test_agent.py
│   ├── collector/
│   │   ├── __init__.py
│   │   ├── bct_scraper.py
│   │   ├── scheduler.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       └── test_bct_scraper.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── documents.py
│   │   ├── search.py
│   │   ├── chat.py
│   │   ├── admin.py
│   │   └── graph.py
│   └── middleware/
│       ├── __init__.py
│       ├── auth.py
│       └── error_handlers.py
├── frontend/
│   └── kusor-ui/
│       ├── src/
│       │   ├── app/
│       │   │   ├── core/
│       │   │   │   ├── services/
│       │   │   │   │   ├── auth.service.ts
│       │   │   │   │   └── api.service.ts
│       │   │   │   ├── guards/
│       │   │   │   │   └── auth.guard.ts
│       │   │   │   ├── interceptors/
│       │   │   │   │   └── jwt.interceptor.ts
│       │   │   │   └── models/
│       │   │   │       ├── user.model.ts
│       │   │   │       ├── document.model.ts
│       │   │   │       ├── chat.model.ts
│       │   │   │       └── graph.model.ts
│       │   │   ├── pages/
│       │   │   │   ├── login/
│       │   │   │   │   ├── login.component.ts
│       │   │   │   │   ├── login.component.html
│       │   │   │   │   └── login.component.scss
│       │   │   │   ├── dashboard/
│       │   │   │   │   ├── dashboard.component.ts
│       │   │   │   │   ├── dashboard.component.html
│       │   │   │   │   └── dashboard.component.scss
│       │   │   │   ├── chat/
│       │   │   │   │   ├── chat.component.ts
│       │   │   │   │   ├── chat.component.html
│       │   │   │   │   └── chat.component.scss
│       │   │   │   ├── admin/
│       │   │   │   │   ├── documents.component.ts
│       │   │   │   │   ├── documents.component.html
│       │   │   │   │   └── documents.component.scss
│       │   │   │   └── graph/
│       │   │   │       ├── graph.component.ts
│       │   │   │       ├── graph.component.html
│       │   │   │       └── graph.component.scss
│       │   │   ├── shared/
│       │   │   │   └── components/
│       │   │   │       ├── navbar/
│       │   │   │       ├── loading-spinner/
│       │   │   │       └── confidence-badge/
│       │   │   ├── app.config.ts
│       │   │   ├── app.routes.ts
│       │   │   ├── app.ts
│       │   │   └── app.html
│       │   ├── environments/
│       │   │   ├── environment.ts
│       │   │   └── environment.prod.ts
│       │   ├── main.ts
│       │   ├── index.html
│       │   └── styles.scss
│       ├── angular.json
│       ├── package.json
│       └── tsconfig.json
├── docker/
│   └── docker-compose.yml
└── docs/
```

---

## 14. Quick Reference — Running the Project

### Prerequisites

```bash
# Verify all services are running
cd ~/kusor/docker && docker-compose ps
# Expected: kusor_neo4j, kusor_chroma, kusor_postgres all "Up"

# Verify Ollama
curl http://localhost:11434/api/tags
# Expected: qwen2.5:7b and nomic-embed-text in list

# Activate Python venv
cd ~/kusor && source backend/.venv/bin/activate
```

### Starting the Backend

```bash
cd ~/kusor
source backend/.venv/bin/activate
export FLASK_APP=backend.app:create_app
flask run --port 5000
```

### Starting the Frontend

```bash
cd ~/kusor/frontend/kusor-ui
npm run start
# → http://localhost:4200
```

### Running All Tests

```bash
cd ~/kusor
source backend/.venv/bin/activate
python -m pytest backend/ -v --tb=short
```

### Creating Initial Admin User

```bash
cd ~/kusor
source backend/.venv/bin/activate
python -c "
from backend.app import create_app
from backend.extensions import db
from backend.models.user import User
import bcrypt, uuid

app = create_app()
with app.app_context():
    hashed = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode('utf-8')
    admin = User(id=str(uuid.uuid4()), username='admin', password_hash=hashed, role='admin')
    db.session.add(admin)
    db.session.commit()
    print('Admin user created: admin / admin123')
"
```

---

*End of specification. This document is self-contained — an implementing agent with access to this file and the codebase should be able to build the entire KUSOR system module by module.*
