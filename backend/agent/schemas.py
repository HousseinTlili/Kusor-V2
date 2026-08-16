# backend/agent/schemas.py
"""
Data schemas and Pydantic models for KUSOR v3 compliance agents.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional, TypedDict
from pydantic import BaseModel, Field


# ── RAG Agent State ────────────────────────────────────────────────

class AgentState(TypedDict, total=False):
    """State dict carried through every node in the main agent graph."""
    question: str
    session_id: Optional[str]
    chat_history: List[Dict[str, Any]]
    question_type: str
    as_of_date: Optional[str]
    retrieval_result: Any
    retrieved_chunks: List[Dict[str, Any]]
    reranked_chunks: List[Dict[str, Any]]
    past_facts: List[Dict[str, Any]]
    answer: str
    sources: List[Dict[str, Any]]
    confidence_score: float
    error: Optional[str]


# ── Module 2: AML/KYC Models ───────────────────────────────────────

class DocumentCheckResult(BaseModel):
    document_name: str
    is_present: bool
    is_valid: bool
    notes: str = ""


class SanctionsScreeningResult(BaseModel):
    list_name: str
    match_found: bool
    matched_name: Optional[str] = None
    match_score: float = 0.0
    match_type: str = "none"


class KYCReport(BaseModel):
    client_name: str
    client_type: str
    dossier_id: str
    verdict: str = "Conforme"  # Conforme | Non conforme | Escaladé
    overall_risk: str  # LOW | MEDIUM | HIGH | CRITICAL
    document_checks: List[DocumentCheckResult]
    completeness_score: float
    sanctions_results: List[SanctionsScreeningResult]
    sanctions_hit: bool
    regulatory_references: List[str]
    recommendations: List[str]
    agent_confidence: float = 0.95



# ── Module 3: Contract Risk Models ─────────────────────────────────

class ClauseAnalysis(BaseModel):
    clause_number: int
    clause_text: str
    clause_type: str
    conformity_status: str  # CONFORMING | NON_CONFORMING | AMBIGUOUS
    severity: str = "LOW"   # LOW | MEDIUM | HIGH | CRITICAL
    regulatory_basis_ref: Optional[str] = None
    regulatory_basis_still_valid: bool = True
    superseding_circular: Optional[str] = None


class ContractReport(BaseModel):
    contract_title: str
    contract_date: Optional[date] = None
    total_clauses: int
    clauses: List[ClauseAnalysis]
    non_conformity_count: int
    critical_issues: int
    high_issues: int
    overall_risk: str
    temporal_issues: int
    recommendations: List[str]
    note: str = "Comparaison contre texte BCT standard — modèles de contrats banque en attente"



# ── Module 4: Credit Pre-Screening Models ──────────────────────────

class DocumentCompletenessResult(BaseModel):
    required_documents: List[str]
    present_documents: List[str]
    missing_documents: List[str]
    completeness_ratio: float
    verdict: str


class NumericalValidationResult(BaseModel):
    income_declared: float
    income_verified: float
    debt_ratio: float
    debt_ratio_compliant: bool
    verdict: str
    anomalies: List[str] = Field(default_factory=list)


class IdentityCrossRefResult(BaseModel):
    name_consistent: bool
    id_number_consistent: bool
    address_consistent: bool
    kyc_risk_profile: str
    verdict: str


class CreditReport(BaseModel):
    dossier_id: str
    applicant_name: str
    loan_type: str
    document_completeness: DocumentCompletenessResult
    numerical_validation: NumericalValidationResult
    identity_cross_reference: IdentityCrossRefResult
    overall_verdict: str  # APPROVE | REVIEW | REJECT
    overall_risk: str     # LOW | MEDIUM | HIGH | CRITICAL
    blocking_issues: List[str]
    regulatory_references: List[str]


# ── Module 5: Change Propagation Models ───────────────────────────

class ImpactItem(BaseModel):
    entity_type: str  # obligation | process | contract_template
    entity_id: str
    entity_name: str
    severity: str     # LOW | MEDIUM | HIGH | CRITICAL
    impact_description: str
    relationship_path: List[str]


class ImpactPropagationReport(BaseModel):
    source_circular_ref: str
    source_circular_title: str
    total_affected: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    affected_items: List[ImpactItem]
    summary: str
