import pytest
import os
import pickle
from pathlib import Path
import fitz  # PyMuPDF
import chromadb
from backend.processing.document_processor import DocumentProcessor, ProcessingResult, ExtractedEntity

@pytest.fixture
def test_dirs(tmp_path):
    """Create temporary directories for testing."""
    circulars_dir = tmp_path / "circulars"
    circulars_dir.mkdir()
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return {
        "circulars": circulars_dir,
        "data": data_dir,
        "bm25_index_path": str(data_dir / "bm25_index.pkl")
    }

@pytest.fixture
def text_pdf_path(test_dirs):
    """Create a mock text-based BCT circular PDF."""
    pdf_path = test_dirs["circulars"] / "circulaire_2024-05.pdf"
    
    doc = fitz.open()
    page = doc.new_page()
    
    content = """BANQUE CENTRALE DE TUNISIE
Circulaire aux banques n° 2024-05

Titre I : Dispositions Générales

Article 1 : Les banques résidentes de la place doivent constituer une réserve obligatoire auprès de la Banque Centrale de Tunisie (BCT).

Article 2 : La BCT suit la situation des réserves au jour le jour conformément à la circulaire n° 2020-10 et à la loi n° 2016-35.
"""
    
    # Use insert_textbox to wrap text automatically and avoid horizontal clipping
    rect = fitz.Rect(50, 50, 550, 750)
    page.insert_textbox(rect, content)
    doc.save(str(pdf_path))
    doc.close()
    
    return str(pdf_path)

@pytest.fixture
def scanned_pdf_path(test_dirs):
    """Create a mock scanned PDF (no searchable text) to trigger OCR fallback."""
    pdf_path = test_dirs["circulars"] / "circulaire_scanned.pdf"
    
    # 1. Create text page in memory
    doc_text = fitz.open()
    page_text = doc_text.new_page()
    rect = fitz.Rect(50, 50, 550, 750)
    page_text.insert_textbox(rect, "Ce texte est scanné.\nArticle 3 : Les conditions d'octroi de crédit aux agents résidentiels.")
    
    # 2. Render to image
    pix = page_text.get_pixmap()
    img_bytes = pix.tobytes("png")
    doc_text.close()
    
    # 3. Insert image into a new PDF
    doc_scanned = fitz.open()
    page_scanned = doc_scanned.new_page()
    page_scanned.insert_image(page_scanned.rect, stream=img_bytes)
    doc_scanned.save(str(pdf_path))
    doc_scanned.close()
    
    return str(pdf_path)

@pytest.fixture
def doc_processor(test_dirs):
    """Initialize DocumentProcessor with test configurations."""
    return DocumentProcessor(
        chroma_host="localhost",
        chroma_port=8001,
        ollama_base_url="http://localhost:11434",
        embedding_model="nomic-embed-text",
        collection_name="test_kusor_documents",
        bm25_index_path=test_dirs["bm25_index_path"],
        spacy_model="fr_core_news_lg"
    )

class TestDocumentProcessor:
    def test_process_real_circular(self, doc_processor, text_pdf_path) -> None:
        """Process a real BCT circular PDF and verify complete pipeline."""
        doc_id = "test-doc-2024-05"
        result = doc_processor.process_document(text_pdf_path, doc_id, "2024-05")
        
        assert isinstance(result, ProcessingResult)
        assert result.document_id == doc_id
        assert result.total_pages == 1
        assert result.total_chunks > 0
        assert result.chroma_updated is True
        assert result.bm25_updated is True
        assert len(result.errors) == 0

    def test_chunks_stored_in_chromadb(self, doc_processor, text_pdf_path) -> None:
        """After processing, chunks must exist in ChromaDB with correct metadata."""
        doc_id = "test-doc-2024-05"
        doc_processor.process_document(text_pdf_path, doc_id, "2024-05")
        
        client = chromadb.HttpClient(host=doc_processor.chroma_host, port=doc_processor.chroma_port)
        collection = client.get_collection(doc_processor.collection_name)
        
        results = collection.get(where={"document_id": doc_id})
        assert len(results["ids"]) > 0
        
        # Verify metadata fields
        metadata = results["metadatas"][0]
        assert metadata["document_id"] == doc_id
        assert "chunk_index" in metadata
        assert metadata["page_number"] == 1
        assert metadata["source_filename"] == "circulaire_2024-05.pdf"
        assert metadata["circular_number"] == "2024-05"

    def test_entities_extracted(self, doc_processor, text_pdf_path) -> None:
        """NER must extract ORG and LAW entities, plus circular references."""
        doc_id = "test-doc-2024-05"
        result = doc_processor.process_document(text_pdf_path, doc_id, "2024-05")
        
        # Verify entities
        labels = [ent.label for ent in result.entities]
        texts = [ent.text.lower() for ent in result.entities]
        
        assert "CIRCULAR_REF" in labels
        assert "LAW" in labels
        assert "ORG" in labels
        
        # Verify circular references list (which extracts the target circular number, not the current one)
        assert "2020-10" in result.circular_references
        assert "2024-05" not in result.circular_references  # current circular shouldn't be in references

    def test_bm25_index_updated(self, doc_processor, text_pdf_path) -> None:
        """BM25 index file must exist and contain the processed document's chunks."""
        doc_id = "test-doc-2024-05"
        doc_processor.process_document(text_pdf_path, doc_id, "2024-05")
        
        assert os.path.exists(doc_processor.bm25_index_path)
        
        with open(doc_processor.bm25_index_path, "rb") as f:
            data = pickle.load(f)
            
        assert "corpus" in data
        assert "chunks" in data
        assert "bm25" in data
        assert len(data["chunks"]) > 0
        assert data["chunks"][0]["document_id"] == doc_id
        assert data["bm25"] is not None

    def test_structural_presegmentation(self, doc_processor, text_pdf_path) -> None:
        """Articles must not be split across chunks."""
        doc_id = "test-doc-2024-05"
        
        # Test structural presegmentation directly
        pages = doc_processor._extract_text(text_pdf_path)
        segments = doc_processor._structural_presegment(pages)
        
        # Ensure we have preamble, article 1 and article 2 segments
        types = [seg["segment_type"] for seg in segments]
        assert "preamble" in types
        assert "article" in types
        
        # Contents should start with structure indicators
        article_contents = [seg["content"] for seg in segments if seg["segment_type"] == "article"]
        assert any(content.startswith("Article 1") for content in article_contents)
        assert any(content.startswith("Article 2") for content in article_contents)

    def test_ocr_fallback(self, doc_processor, scanned_pdf_path) -> None:
        """Scanned PDFs trigger OCR and still produce valid chunks."""
        doc_id = "test-doc-scanned"
        result = doc_processor.process_document(scanned_pdf_path, doc_id, "2024-99")
        
        assert result.total_pages == 1
        assert result.total_chunks > 0
        assert len(result.errors) == 0
        
        # Check if text contains keywords from scanned PDF
        full_extracted_content = " ".join([c["content"] for c in result.chunks])
        assert "scann" in full_extracted_content.lower() or "article" in full_extracted_content.lower()

    def test_idempotent_reprocessing(self, doc_processor, text_pdf_path) -> None:
        """Processing the same document twice doesn't create duplicate chunks."""
        doc_id = "test-doc-2024-05"
        
        # Process first time
        result1 = doc_processor.process_document(text_pdf_path, doc_id, "2024-05")
        count_chroma_1 = result1.total_chunks
        
        # Check index count
        with open(doc_processor.bm25_index_path, "rb") as f:
            bm25_data = pickle.load(f)
        count_bm25_1 = len(bm25_data["chunks"])
        
        # Process second time
        result2 = doc_processor.process_document(text_pdf_path, doc_id, "2024-05")
        count_chroma_2 = result2.total_chunks
        
        # Check index count again
        with open(doc_processor.bm25_index_path, "rb") as f:
            bm25_data2 = pickle.load(f)
        count_bm25_2 = len(bm25_data2["chunks"])
        
        # Counts must be identical, not doubled!
        assert count_chroma_1 == count_chroma_2
        assert count_bm25_1 == count_bm25_2
        
        # Verify collection has exactly count_chroma_1 elements for this doc in Chroma
        client = chromadb.HttpClient(host=doc_processor.chroma_host, port=doc_processor.chroma_port)
        collection = client.get_collection(doc_processor.collection_name)
        results = collection.get(where={"document_id": doc_id})
        assert len(results["ids"]) == count_chroma_1
