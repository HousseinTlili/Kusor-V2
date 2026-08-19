import os
import io
import re
import pickle
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

import fitz  # PyMuPDF
import requests
import chromadb
from rank_bm25 import BM25Okapi

try:
    import spacy
    _spacy_loaded = True
except ImportError:
    _spacy_loaded = False


@dataclass
class ExtractedEntity:
    text: str
    label: str  # "ORG", "LAW", "CIRCULAR_REF", etc.


@dataclass
class ProcessingResult:
    document_id: str
    circular_number: str
    total_pages: int
    total_chunks: int
    chunks: List[Dict[str, Any]]
    entities: List[ExtractedEntity]
    circular_references: List[str]
    chroma_updated: bool
    bm25_updated: bool
    errors: List[str] = field(default_factory=list)


class DocumentProcessor:
    """
    Module 3 — Document Processing Pipeline:
    1. Text extraction (PyMuPDF with Tesseract OCR fallback).
    2. Structural pre-segmentation (Preamble, Articles, Sections).
    3. Entity & reference extraction (spaCy fr_core_news_lg + Regex).
    4. ChromaDB vector store ingestion (nomic-embed-text via Ollama).
    5. BM25 inverted index generation and persistence.
    """

    def __init__(
        self,
        chroma_host: str = "localhost",
        chroma_port: int = 8001,
        ollama_base_url: str = "http://localhost:11434",
        embedding_model: str = "nomic-embed-text",
        collection_name: str = "kusor_documents",
        bm25_index_path: str = "backend/data/bm25_index.pkl",
        spacy_model: str = "fr_core_news_lg",
        ocr_lang: str = "fra"
    ) -> None:
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.ollama_base_url = ollama_base_url
        self.embedding_model = embedding_model
        self.collection_name = collection_name
        self.bm25_index_path = bm25_index_path
        self.spacy_model_name = spacy_model
        self.ocr_lang = ocr_lang

        # Lazy loaded spaCy
        self._nlp = None

    @property
    def nlp(self):
        if self._nlp is None and _spacy_loaded:
            try:
                self._nlp = spacy.load(self.spacy_model_name)
            except Exception:
                try:
                    self._nlp = spacy.blank("fr")
                except Exception:
                    self._nlp = None
        return self._nlp

    def _extract_text(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract text page by page with OCR fallback if necessary."""
        return self.extract_text(pdf_path)

    def extract_text(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Return list of dicts: [{'page': int, 'text': str}, ...]."""
        p = Path(pdf_path)
        if not p.exists():
            raise FileNotFoundError(f"Fichier introuvable : {pdf_path}")

        doc = fitz.open(str(p))
        pages_content = []

        for i, page in enumerate(doc):
            text = page.get_text().strip()
            if len(text) < 20:
                text = self._ocr_fallback(page)
            pages_content.append({"page": i + 1, "text": text})

        doc.close()
        return pages_content

    def _ocr_fallback(self, page) -> str:
        """OCR via Tesseract for scanned / image-only pages."""
        try:
            import pytesseract
            from PIL import Image

            pix = page.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            return pytesseract.image_to_string(img, lang=self.ocr_lang).strip()
        except Exception as e:
            return ""

    def _structural_presegment(self, pages_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Pre-segment circular into structural units (preamble, articles, sections)."""
        full_text = "\n\n".join([p["text"] for p in pages_content])
        
        # Regex to split on articles, sections, chapters
        article_pattern = r"(?=(?:^|\n)\s*(?:Article\s+\d+|TITRE\s+[IVXLCDM]+|CHAPITRE\s+[IVXLCDM]+|Section\s+\d+))"
        raw_parts = [p.strip() for p in re.split(article_pattern, full_text, flags=re.IGNORECASE) if p.strip()]

        segments = []
        for idx, part in enumerate(raw_parts):
            if re.match(r"^Article\s+\d+", part, flags=re.IGNORECASE):
                seg_type = "article"
            elif re.match(r"^(?:TITRE|CHAPITRE|Section)", part, flags=re.IGNORECASE):
                seg_type = "section"
            else:
                seg_type = "preamble" if idx == 0 else "body"

            segments.append({
                "segment_index": idx,
                "segment_type": seg_type,
                "content": part
            })

        if not segments:
            segments.append({
                "segment_index": 0,
                "segment_type": "preamble",
                "content": full_text
            })

        return segments

    def chunk_text(self, pages_content: List[Dict[str, Any]], min_tokens: int = 100, max_tokens: int = 800) -> List[Dict[str, Any]]:
        """Chunk text respecting structural paragraph boundaries."""
        chunks = []
        chunk_id = 0

        for page_data in pages_content:
            page_num = page_data["page"]
            text = page_data["text"]

            paragraphs = [p.strip() for p in re.split(r"\n\s*\n|\.\s+(?=[A-ZÀ-Ü])", text) if p.strip()]

            current_chunk = ""
            for para in paragraphs:
                word_count = len(current_chunk.split()) + len(para.split())

                if word_count > max_tokens and current_chunk:
                    chunks.append({
                        "chunk_id": chunk_id,
                        "page": page_num,
                        "text": current_chunk.strip(),
                        "content": current_chunk.strip()
                    })
                    chunk_id += 1
                    current_chunk = para
                else:
                    current_chunk = (current_chunk + " " + para).strip()

            if current_chunk.strip():
                chunks.append({
                    "chunk_id": chunk_id,
                    "page": page_num,
                    "text": current_chunk.strip(),
                    "content": current_chunk.strip()
                })
                chunk_id += 1

        return chunks

    def _extract_entities(self, text: str) -> List[ExtractedEntity]:
        """Extract ORG, LAW, and CIRCULAR_REF entities."""
        entities = []
        seen = set()

        # 1. Regex circular references
        circ_pattern = r"(?:circulaire[s]?\s*(?:aux\s+\w+\s+)?n[°o]?\s*|\b)(\d{4}-\d{2,3})\b"
        for match in re.finditer(circ_pattern, text, flags=re.IGNORECASE):
            c_num = match.group(1)
            if c_num not in seen:
                seen.add(c_num)
                entities.append(ExtractedEntity(text=c_num, label="CIRCULAR_REF"))

        # 2. Regex Law references
        law_pattern = r"(?:loi\s+n[°o]?\s*(\d{4}-\d+|\d{2}-\d+))"
        for match in re.finditer(law_pattern, text, flags=re.IGNORECASE):
            l_name = match.group(0)
            if l_name not in seen:
                seen.add(l_name)
                entities.append(ExtractedEntity(text=l_name, label="LAW"))

        # 3. Known organizations & spaCy NER
        org_keywords = ["Banque Centrale de Tunisie", "BCT", "Ministère des Finances", "Gouverneur", "Commission Bancaire"]
        for org in org_keywords:
            if re.search(r"\b" + re.escape(org) + r"\b", text, flags=re.IGNORECASE):
                if org not in seen:
                    seen.add(org)
                    entities.append(ExtractedEntity(text=org, label="ORG"))

        if self.nlp:
            try:
                doc = self.nlp(text[:50000])
                for ent in doc.ents:
                    if ent.label_ in ["ORG", "MISC", "LOC"] and ent.text not in seen and len(ent.text) > 2:
                        seen.add(ent.text)
                        lbl = "ORG" if ent.label_ == "ORG" else ent.label_
                        entities.append(ExtractedEntity(text=ent.text, label=lbl))
            except Exception:
                pass

        return entities

    def extract_circular_references(self, text: str) -> List[str]:
        """Extract circular reference numbers (e.g. '2020-10')."""
        pattern = r"(?:circulaire[s]?\s*(?:aux\s+\w+\s+)?n[°o]?\s*|\b)(\d{4}-\d{2,3})\b"
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        return list(set(matches))

    def process_document(self, pdf_path: str, doc_id: str, circular_number: str) -> ProcessingResult:
        """Complete ingestion pipeline for a document."""
        errors = []
        pages = self.extract_text(pdf_path)
        full_text = " ".join([p["text"] for p in pages])

        # Entities & References
        entities = self._extract_entities(full_text)
        raw_refs = self.extract_circular_references(full_text)
        # Exclude self reference
        circ_refs = [r for r in raw_refs if r != circular_number]

        # Chunking
        raw_chunks = self.chunk_text(pages)
        formatted_chunks = []
        for idx, chk in enumerate(raw_chunks):
            formatted_chunks.append({
                "chunk_id": idx,
                "document_id": doc_id,
                "page_number": chk.get("page", 1),
                "content": chk.get("content") or chk.get("text", ""),
                "circular_number": circular_number,
                "source_filename": f"circulaire_{circular_number}.pdf"
            })

        # ChromaDB Ingestion
        chroma_ok = False
        try:
            client = chromadb.HttpClient(host=self.chroma_host, port=self.chroma_port)
            try:
                collection = client.get_collection(self.collection_name)
            except Exception:
                collection = client.create_collection(self.collection_name)

            # Delete old chunks for idempotent re-processing
            try:
                collection.delete(where={"document_id": doc_id})
            except Exception:
                pass

            ids = [f"{doc_id}_{idx}" for idx in range(len(formatted_chunks))]
            docs = [c["content"] for c in formatted_chunks]
            metas = [{
                "document_id": doc_id,
                "chunk_index": idx,
                "page_number": c["page_number"],
                "source_filename": c["source_filename"],
                "circular_number": circular_number
            } for idx, c in enumerate(formatted_chunks)]

            if ids:
                # Embeddings
                embed_url = f"{self.ollama_base_url}/api/embed"
                try:
                    res = requests.post(embed_url, json={"model": self.embedding_model, "input": docs}, timeout=30)
                    if res.status_code == 200:
                        embeddings = res.json().get("embeddings", [])
                        collection.add(ids=ids, embeddings=embeddings, documents=docs, metadatas=metas)
                        chroma_ok = True
                except Exception:
                    # Fallback without custom embeddings if Ollama unreachable
                    pass
                if not chroma_ok:
                    collection.add(ids=ids, documents=docs, metadatas=metas)
                    chroma_ok = True
        except Exception as e:
            errors.append(f"Chroma error: {e}")

        # BM25 Ingestion
        bm25_ok = False
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.bm25_index_path)), exist_ok=True)
            existing_corpus = []
            existing_chunks = []
            if os.path.exists(self.bm25_index_path):
                try:
                    with open(self.bm25_index_path, "rb") as f:
                        data = pickle.load(f)
                    for c_text, c_dict in zip(data.get("corpus", []), data.get("chunks", [])):
                        if c_dict.get("document_id") != doc_id:
                            existing_corpus.append(c_text)
                            existing_chunks.append(c_dict)
                except Exception:
                    pass

            for c in formatted_chunks:
                tokens = c["content"].lower().split()
                existing_corpus.append(tokens)
                existing_chunks.append(c)

            bm25 = BM25Okapi(existing_corpus) if existing_corpus else None
            with open(self.bm25_index_path, "wb") as f:
                pickle.dump({"corpus": existing_corpus, "chunks": existing_chunks, "bm25": bm25}, f)
            bm25_ok = True
        except Exception as e:
            errors.append(f"BM25 error: {e}")

        return ProcessingResult(
            document_id=doc_id,
            circular_number=circular_number,
            total_pages=len(pages),
            total_chunks=len(formatted_chunks),
            chunks=formatted_chunks,
            entities=entities,
            circular_references=circ_refs,
            chroma_updated=chroma_ok,
            bm25_updated=bm25_ok,
            errors=errors
        )

    def embed_and_store(self, chunks: List[Dict[str, Any]], document_id: str, chroma_host: str = "localhost", chroma_port: int = 8001):
        """Legacy helper for backward compatibility."""
        client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
        collection = client.get_or_create_collection(name="circulars")

        ids, documents, metadatas = [], [], []
        for chunk in chunks:
            ids.append(f"{document_id}_chunk_{chunk.get('chunk_id', 0)}")
            documents.append(chunk.get("text") or chunk.get("content", ""))
            metadatas.append({
                "document_id": document_id,
                "chunk_index": chunk.get("chunk_id", 0),
                "page_number": chunk.get("page", 1),
            })

        if ids:
            collection.add(ids=ids, documents=documents, metadatas=metadatas)
        return len(ids)