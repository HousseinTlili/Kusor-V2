# backend/processing/tests/test_document_processor.py
"""
Unit tests for DocumentProcessor text processing and segmentation.
"""

from backend.app import create_app
from backend.processing.document_processor import DocumentProcessor


def test_document_processor_text_segmentation():
    processor = DocumentProcessor()
    raw_text = """
    Circulaire N° 2024-05 du 15 janvier 2024
    
    Article 1
    Les banques sont tenues de vérifier l'identité de leurs clients.
    
    Article 2
    Il est interdit d'ouvrir un compte sans pièce d'identité valide.
    """
    sections = processor._segment_text(raw_text)
    assert len(sections) >= 2
    titles = [s[0] for s in sections]
    assert any("Article 1" in t for t in titles)
    assert any("Article 2" in t for t in titles)


def test_document_processor_process_text_content():
    app = create_app()
    with app.app_context():
        processor = DocumentProcessor()
        raw_text = """
        Circulaire N° 2024-10
        Article 1
        Les établissements financiers doivent transmettre un rapport trimestriel.
        """
        doc = processor.process_text_content(
            raw_text=raw_text,
            title="Circulaire 2024-10 Test",
            doc_type="circular",
        )
        assert doc.number == "2024-10"
        assert doc.indexation_state == "INDEXED"
        assert doc.chunks.count() >= 1
