# backend/agent/tests/test_kyc_agent.py
"""
Unit tests for KYCAgent completeness & risk assessment.
"""

from backend.agent.kyc_agent import KYCAgent


def test_kyc_completeness_complete():
    agent = KYCAgent()
    dossier = ["cin_passport.pdf", "justificatif_domicile.pdf", "fiche_signaletique.pdf", "declaration_patrimoine.pdf"]
    report = agent.run_kyc_check("Societe Test", "individual", dossier)

    assert report.completeness_score == 1.0
    assert report.overall_risk == "LOW"
    assert not report.sanctions_hit


def test_kyc_completeness_missing():
    agent = KYCAgent()
    dossier = ["cin_passport.pdf"]
    report = agent.run_kyc_check("Client Incomplet", "individual", dossier)

    assert report.completeness_score < 0.5
    assert report.overall_risk in ["HIGH", "MEDIUM"]
    assert len(report.recommendations) >= 1
