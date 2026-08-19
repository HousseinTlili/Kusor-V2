# backend/processing/tests/test_obligation_extractor.py
"""
Unit tests for ObligationExtractor regex classification.
"""

from backend.models.document import Document
from backend.processing.obligation_extractor import ObligationExtractor


def test_regex_prohibition_extraction():
    extractor = ObligationExtractor()
    doc = Document(id="doc_test_1", number="2024-01")
    sections = [
        ("Article 1", "Il est interdit aux établissements de crédit d'accorder des prêts sans garantie.")
    ]
    obs = extractor.extract_obligations(doc, sections)
    assert len(obs) == 1
    assert obs[0].obligation_type == "PROHIBITION"
    assert "interdit" in obs[0].text


def test_regex_threshold_extraction():
    extractor = ObligationExtractor()
    doc = Document(id="doc_test_2", number="2024-02")
    sections = [
        ("Article 2", "Le ratio de solvabilité ne doit pas dépasser le seuil de 15 %.")
    ]
    obs = extractor.extract_obligations(doc, sections)
    assert len(obs) >= 1
    types = [o.obligation_type for o in obs]
    assert "THRESHOLD" in types
