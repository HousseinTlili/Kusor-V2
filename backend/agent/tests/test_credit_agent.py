# backend/agent/tests/test_credit_agent.py
"""
Unit tests for CreditSupervisorAgent multi-agent orchestration.
"""

from backend.agent.credit_agent import CreditSupervisorAgent


def test_credit_supervisor_approve():
    supervisor = CreditSupervisorAgent()
    files = ["bulletin_paie.pdf", "releve_bancaire.pdf", "attestation_travail.pdf", "cin.pdf"]
    financials = {"income": 3000.0, "monthly_debt": 400.0, "loan_annuity": 300.0}

    report = supervisor.prescreen("cred_101", "Client Conforme", "personal", files, financials)
    assert report.overall_verdict == "APPROVE"
    assert report.overall_risk == "LOW"


def test_credit_supervisor_reject_high_debt():
    supervisor = CreditSupervisorAgent()
    files = ["bulletin_paie.pdf", "releve_bancaire.pdf", "attestation_travail.pdf", "cin.pdf"]
    financials = {"income": 2000.0, "monthly_debt": 800.0, "loan_annuity": 300.0}

    report = supervisor.prescreen("cred_102", "Client Surendetté", "personal", files, financials)
    assert report.overall_verdict in ["REJECT", "REVIEW"]
    assert report.numerical_validation.verdict == "FAIL"
