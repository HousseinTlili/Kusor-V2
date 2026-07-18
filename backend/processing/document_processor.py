from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import re
import pickle
import os
from pathlib import Path
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import chromadb
from langchain_experimental.text_splitter import SemanticChunker
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import spacy
import docx


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
    ) -> None:
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.ollama_base_url = ollama_base_url
        self.embedding_model = embedding_model
        self.collection_name = collection_name
        self.bm25_index_path = bm25_index_path
        self.spacy_model = spacy_model

    def process_document(
        self,
        pdf_path: str,
        document_id: str,
        circular_number: Optional[str] = None,
    ) -> ProcessingResult:
        """Main entry point. Processes a PDF, DOCX, or TXT file end-to-end."""
        errors = []
        chroma_updated = False
        bm25_updated = False
        
        file_obj = Path(pdf_path)
        source_filename = file_obj.name
        ext = file_obj.suffix.lower()
        
        try:
            # 1. Extract text based on file extension
            if ext == ".pdf":
                pages = self._extract_text_pdf(pdf_path)
            elif ext == ".docx":
                pages = self._extract_text_docx(pdf_path)
            elif ext == ".txt":
                pages = self._extract_text_txt(pdf_path)
            else:

                raise ValueError(f"Unsupported file format: {ext}. Supported: .pdf, .docx, .txt")
                
            total_pages = len(pages)
            if total_pages == 0:
                raise ValueError("No text or pages could be extracted from file.")
        except Exception as e:
            return ProcessingResult(
                document_id=document_id,
                source_filename=source_filename,
                total_pages=0,
                total_chunks=0,
                chunks=[],
                entities=[],
                circular_references=[],
                bm25_updated=False,
                chroma_updated=False,
                errors=[f"Text extraction failed: {str(e)}"]
            )
            
        full_text = "\n".join([page["text"] for page in pages])
        
        # Determine circular number if not passed
        if not circular_number:
            match = re.search(self.CIRCULAR_HEADER_PATTERN, full_text)
            if match:
                circular_number = match.group(1)
                
        # 2. Structural pre-segmentation
        try:
            segments = self._structural_presegment(pages)
        except Exception as e:
            errors.append(f"Structural presegmentation failed: {str(e)}")
            segments = [{"content": page["text"], "page_number": page["page_number"], "segment_type": "preamble"} for page in pages]

        # 3. Semantic chunking
        try:
            chunks = self._semantic_chunk(segments)
            # Add metadata to chunks
            for chunk in chunks:
                chunk["document_id"] = document_id
                chunk["source_filename"] = source_filename
                chunk["circular_number"] = circular_number
        except Exception as e:
            # Fallback to simple chunking if semantic fails
            errors.append(f"Semantic chunking failed: {str(e)}")
            chunks = []
            chunk_index = 0
            for seg in segments:
                chunks.append({
                    "content": seg["content"],
                    "page_number": seg["page_number"],
                    "chunk_index": chunk_index,
                    "document_id": document_id,
                    "source_filename": source_filename,
                    "circular_number": circular_number
                })
                chunk_index += 1

        # 4. Extract entities and circular references
        try:
            entities = self._extract_entities(full_text)
        except Exception as e:
            errors.append(f"Entity extraction failed: {str(e)}")
            entities = []
            
        circular_references = []
        for ent in entities:
            if ent.label == "CIRCULAR_REF":
                match = re.search(r"(\d{4}-\d+)", ent.text)
                if match:
                    ref_num = match.group(1)
                    if ref_num != circular_number and ref_num not in circular_references:
                        circular_references.append(ref_num)

        # 5. Store in ChromaDB
        if chunks:
            try:
                chroma_updated = self._store_in_chromadb(
                    chunks=chunks,
                    document_id=document_id,
                    source_filename=source_filename,
                    circular_number=circular_number
                )
            except Exception as e:
                errors.append(f"ChromaDB storage failed: {str(e)}")
                
            # 6. Update BM25 Index
            try:
                bm25_updated = self._update_bm25_index(chunks)
            except Exception as e:
                errors.append(f"BM25 index update failed: {str(e)}")
                
        return ProcessingResult(
            document_id=document_id,
            source_filename=source_filename,
            total_pages=total_pages,
            total_chunks=len(chunks),
            chunks=chunks,
            entities=entities,
            circular_references=circular_references,
            bm25_updated=bm25_updated,
            chroma_updated=chroma_updated,
            errors=errors
        )

    def _extract_text_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract text from PDF using PyMuPDF.
        Falls back to Tesseract OCR for pages with < 50 chars extracted.
        Returns: [{page_number: int, text: str}]
        """
        doc = fitz.open(pdf_path)

        pages = []
        
        for page_idx, page in enumerate(doc):
            page_num = page_idx + 1
            text = page.get_text()
            
            if len(text.strip()) < 50:
                # Render page as image for OCR fallback
                pix = page.get_pixmap(dpi=300)
                image_bytes = pix.tobytes("png")
                img = Image.open(io.BytesIO(image_bytes))
                text = pytesseract.image_to_string(img, lang='fra')
                
            pages.append({
                "page_number": page_num,
                "text": text
            })
            
        doc.close()
        return pages

    def _extract_text_docx(self, docx_path: str) -> List[Dict[str, Any]]:
        """
        Extract text from DOCX using python-docx.
        Each paragraph is assigned an incrementing page number (DOCX has no
        native page concept). We group paragraphs into ~3000-char logical pages.
        """
        document = docx.Document(docx_path)
        pages = []
        current_text = []
        current_length = 0
        page_number = 1

        for para in document.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            current_text.append(text)
            current_length += len(text)

            # Group into logical pages of ~3000 chars
            if current_length >= 3000:
                pages.append({
                    "page_number": page_number,
                    "text": "\n".join(current_text)
                })
                current_text = []
                current_length = 0
                page_number += 1

        # Flush remaining text
        if current_text:
            pages.append({
                "page_number": page_number,
                "text": "\n".join(current_text)
            })

        return pages

    def _extract_text_txt(self, txt_path: str) -> List[Dict[str, Any]]:
        """
        Extract text from a plain TXT file.
        Groups lines into ~3000-char logical pages.
        """
        with open(txt_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        if not content.strip():
            return []

        # Split into logical pages of ~3000 chars at line boundaries
        pages = []
        lines = content.split("\n")
        current_text = []
        current_length = 0
        page_number = 1

        for line in lines:
            current_text.append(line)
            current_length += len(line)

            if current_length >= 3000:
                pages.append({
                    "page_number": page_number,
                    "text": "\n".join(current_text)
                })
                current_text = []
                current_length = 0
                page_number += 1

        if current_text:
            pages.append({
                "page_number": page_number,
                "text": "\n".join(current_text)
            })

        return pages


    def _structural_presegment(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Pre-segment text by BCT structural markers (articles, sections, titles).
        Ensures legal articles are never split across semantic chunks.
        Returns: [{content: str, page_number: int, segment_type: str}]
        """
        # Reconstruct full text and map char indices to page numbers
        full_text = ""
        char_to_page = []
        
        for page in pages:
            start_idx = len(full_text)
            text_to_append = page["text"] + "\n"
            full_text += text_to_append
            end_idx = len(full_text)
            
            for _ in range(start_idx, end_idx):
                char_to_page.append(page["page_number"])
                
        # Find structural boundary matches
        # A boundary is a line starting with Article, Titre, Chapitre, Section, or Sous-section
        boundary_pattern = re.compile(
            r"(?i)(?:^|\n)\s*((?:article\s+\d+|(?:titre|chapitre|section|sous-section)\s+[ivxlcdm\d]+)[^\n]*)"
        )
        
        matches = list(boundary_pattern.finditer(full_text))
        
        if not matches:
            return [{"content": full_text.strip(), "page_number": pages[0]["page_number"] if pages else 1, "segment_type": "preamble"}]
            
        segments = []
        
        # Preamble segment (before first match)
        first_start = 0
        first_end = matches[0].start(1)
        first_content = full_text[first_start:first_end].strip()
        if first_content:
            segments.append({
                "content": first_content,
                "page_number": char_to_page[first_start] if first_start < len(char_to_page) else 1,
                "segment_type": "preamble"
            })
            
        # Segments for each structural marker
        for i in range(len(matches)):
            start = matches[i].start(1)
            end = matches[i+1].start(1) if i + 1 < len(matches) else len(full_text)
            content = full_text[start:end].strip()
            
            match_text = matches[i].group(1).lower()
            if match_text.startswith("article"):
                segment_type = "article"
            else:
                segment_type = "section"
                
            if content:
                page_num = char_to_page[start] if start < len(char_to_page) else char_to_page[-1]
                segments.append({
                    "content": content,
                    "page_number": page_num,
                    "segment_type": segment_type
                })
                
        return segments

    def _semantic_chunk(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply LangChain SemanticChunker with nomic-embed-text to each segment.
        Oversized segments (>512 tokens) are further split with 60-token overlap.
        Returns: [{content: str, page_number: int, chunk_index: int}]
        """
        chunks = []
        chunk_index = 0
        
        embeddings_model = OllamaEmbeddings(
            base_url=self.ollama_base_url,
            model=self.embedding_model
        )
        
        semantic_splitter = SemanticChunker(
            embeddings_model,
            breakpoint_threshold_type="percentile",
            breakpoint_threshold_amount=80
        )
        
        nlp = spacy.load(self.spacy_model)
        token_splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=60,
            length_function=lambda x: len(nlp.tokenizer(x))
        )
        
        for segment in segments:
            content = segment["content"]
            page_number = segment["page_number"]
            
            # Optimization: Skip semantic splitting for small segments to save Ollama API calls.
            # 1500 characters is roughly 250-350 tokens, which easily fits within the 512-token chunk limit.
            if len(content) < 1500:
                chunks.append({
                    "content": content,
                    "page_number": page_number,
                    "chunk_index": chunk_index
                })
                chunk_index += 1
                continue
                
            try:
                sub_chunks = semantic_splitter.split_text(content)
            except Exception:
                # Fallback to token splitter if semantic splitter fails
                sub_chunks = token_splitter.split_text(content)
                
            for sub_chunk in sub_chunks:
                num_tokens = len(nlp.tokenizer(sub_chunk))
                
                # Oversized segments (>512 tokens) split further
                if num_tokens > 512:
                    further_chunks = token_splitter.split_text(sub_chunk)
                    for fc in further_chunks:
                        chunks.append({
                            "content": fc,
                            "page_number": page_number,
                            "chunk_index": chunk_index
                        })
                        chunk_index += 1
                else:
                    chunks.append({
                        "content": sub_chunk,
                        "page_number": page_number,
                        "chunk_index": chunk_index
                    })
                    chunk_index += 1
                    
        return chunks

    def _extract_entities(self, text: str) -> List[ExtractedEntity]:
        """
        Extract entities using spaCy fr_core_news_lg (ORG, LAW labels)
        and regex for BCT circular references.
        """
        nlp = spacy.load(self.spacy_model)
        entities = []
        
        # 1. Circular references regex
        pattern_circ = re.compile(self.CIRCULAR_REF_PATTERN)
        for m in pattern_circ.finditer(text):
            entities.append(ExtractedEntity(
                text=m.group(0),
                label="CIRCULAR_REF",
                start_char=m.start(),
                end_char=m.end()
            ))
            
        # 2. Laws regex
        pattern_law = re.compile(
            r"(?i)\b(?:loi|décret|décret-loi|code|arrêté)\s+(?:n[°o]\s*\d+(?:-\d+)?|des\s+\w+|de\s+la\s+\w+|portant\s+\w+)[^\n,.]*"
        )
        for m in pattern_law.finditer(text):
            entities.append(ExtractedEntity(
                text=m.group(0),
                label="LAW",
                start_char=m.start(),
                end_char=m.end()
            ))
            
        # 3. spaCy entities
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ == "ORG":
                entities.append(ExtractedEntity(
                    text=ent.text,
                    label="ORG",
                    start_char=ent.start_char,
                    end_char=ent.end_char
                ))
            elif ent.label_ == "MISC":
                lower_text = ent.text.lower()
                if any(k in lower_text for k in ["loi", "décret", "code", "arrêté", "circulaire"]):
                    entities.append(ExtractedEntity(
                        text=ent.text,
                        label="LAW",
                        start_char=ent.start_char,
                        end_char=ent.end_char
                    ))
                else:
                    entities.append(ExtractedEntity(
                        text=ent.text,
                        label="ORG",
                        start_char=ent.start_char,
                        end_char=ent.end_char
                    ))
                    
        # 4. Deduplicate overlapping entities
        def label_priority(label):
            if label == "CIRCULAR_REF":
                return 3
            if label == "LAW":
                return 2
            return 1
            
        sorted_entities = sorted(
            entities,
            key=lambda x: (x.start_char, -label_priority(x.label), -(x.end_char - x.start_char))
        )
        
        deduped = []
        last_end = -1
        for ent in sorted_entities:
            if ent.start_char >= last_end:
                deduped.append(ent)
                last_end = ent.end_char
                
        return deduped

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
        client = chromadb.HttpClient(host=self.chroma_host, port=self.chroma_port)
        collection = client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        # Clear existing chunks for this document (idempotency)
        collection.delete(where={"document_id": document_id})
        
        # Prepare data lists
        ids = []
        documents = []
        metadatas = []
        
        for chunk in chunks:
            chunk_idx = chunk["chunk_index"]
            chunk_id = f"{document_id}_{chunk_idx}"
            
            ids.append(chunk_id)
            documents.append(chunk["content"])
            metadatas.append({
                "document_id": document_id,
                "chunk_index": chunk_idx,
                "page_number": chunk["page_number"],
                "source_filename": source_filename,
                "circular_number": circular_number or ""
            })
            
        # Batch embeddings in groups of 32 to prevent CUDA OOM
        embeddings_model = OllamaEmbeddings(
            base_url=self.ollama_base_url,
            model=self.embedding_model
        )
        
        embeddings = []
        for i in range(0, len(documents), 32):
            batch = documents[i:i+32]
            batch_embeddings = embeddings_model.embed_documents(batch)
            embeddings.extend(batch_embeddings)
            
        # Add to ChromaDB
        collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
        return True

    def _update_bm25_index(self, chunks: List[Dict[str, Any]]) -> bool:
        """
        Update the persisted BM25 index at backend/data/bm25_index.pkl.
        If index exists, append new chunks. Otherwise, create new index.
        Uses rank_bm25.BM25Okapi.
        """
        os.makedirs(os.path.dirname(self.bm25_index_path), exist_ok=True)
        
        corpus = []
        existing_chunks = []
        
        if os.path.exists(self.bm25_index_path):
            try:
                with open(self.bm25_index_path, "rb") as f:
                    data = pickle.load(f)
                corpus = data.get("corpus", [])
                existing_chunks = data.get("chunks", [])
            except Exception:
                corpus = []
                existing_chunks = []
                
        # Filter out existing chunks for this document_id (idempotency)
        if chunks:
            doc_id = chunks[0].get("document_id")
            if doc_id:
                filtered_corpus = []
                filtered_chunks = []
                for corp_item, chunk_item in zip(corpus, existing_chunks):
                    if chunk_item.get("document_id") != doc_id:
                        filtered_corpus.append(corp_item)
                        filtered_chunks.append(chunk_item)
                corpus = filtered_corpus
                existing_chunks = filtered_chunks
                
        # Append new chunks
        for chunk in chunks:
            tokens = chunk["content"].lower().split()
            corpus.append(tokens)
            existing_chunks.append(chunk)
            
        # Re-create BM25 index
        from rank_bm25 import BM25Okapi
        if corpus:
            bm25 = BM25Okapi(corpus)
        else:
            bm25 = None
            
        # Save back
        with open(self.bm25_index_path, "wb") as f:
            pickle.dump({
                "corpus": corpus,
                "chunks": existing_chunks,
                "bm25": bm25
            }, f)
            
        return True

    def _generate_document_id(self, filename: str) -> str:
        """Generate deterministic document ID from filename."""
        import uuid
        namespace = uuid.NAMESPACE_DNS
        return str(uuid.uuid5(namespace, filename))
