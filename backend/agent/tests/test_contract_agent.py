# backend/agent/tests/test_contract_agent.py
"""
Unit tests for ContractAgent clause segmentation and analysis.
"""

from backend.agent.contract_agent import ContractAgent


def test_contract_agent_segmentation():
    agent = ContractAgent()
    contract_text = """
    CONVENTION DE PRÊT IMMOBILIER
    
    Article 1
    Le prêteur accorde un prêt d'un montant de 100 000 TND au taux d'intérêt de 7%.
    
    Article 2
    En cas de retard, des pénalités de retard de 2% seront appliquées.
    """
    report = agent.analyze_contract(contract_text, "Prêt Immobilier Test")
    assert report.total_clauses >= 2
    assert report.overall_risk in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
