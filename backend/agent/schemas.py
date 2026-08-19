from pydantic import BaseModel, Field
from typing import List, Optional, Any
from enum import Enum

class QuestionType(str, Enum):
    FACTUAL = "factual"          # "What are the reserve requirements?"
    RELATIONAL = "relational"    # "Has circular X been modified?"
    TEMPORAL = "temporal"        # "What changed between 2020 and 2023?"
    COMPARATIVE = "comparative"  # "How does circular X differ from Y?"

class QuestionClassification(BaseModel):
    category: QuestionType = Field(description="Category of the question")

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
    retrieved_chunks: List[Any] = Field(default_factory=list)
    reranked_chunks: List[Any] = Field(default_factory=list)
    graph_path_used: bool = False
    llm_response: Optional[str] = None
    final_response: Optional[AgentResponse] = None
    error: Optional[str] = None
    retry_count: int = 0


# ── Module: AML/KYC Models ───────────────────────────────────────

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
    verdict: str = "Conforme"
    overall_risk: str = "LOW"
    document_checks: List[DocumentCheckResult] = Field(default_factory=list)
    completeness_score: float = 1.0
    sanctions_results: List[SanctionsScreeningResult] = Field(default_factory=list)
    sanctions_hit: bool = False
    regulatory_references: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    agent_confidence: float = 0.95


# ── Module: Contract Risk Models ─────────────────────────────────

class ClauseAnalysis(BaseModel):
    clause_number: int
    clause_text: str
    clause_type: str
    conformity_status: str
    severity: str = "LOW"
    regulatory_basis_ref: Optional[str] = None
    regulatory_basis_still_valid: bool = True
    superseding_circular: Optional[str] = None


class ContractReport(BaseModel):
    contract_title: str
    contract_date: Optional[str] = None
    total_clauses: int = 0
    clauses: List[ClauseAnalysis] = Field(default_factory=list)
    non_conformity_count: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    overall_risk: str = "LOW"
    temporal_issues: int = 0
    recommendations: List[str] = Field(default_factory=list)
    note: str = "Comparaison contre texte BCT standard"


# ── Module: Credit Pre-Screening Models ──────────────────────────

class DocumentCompletenessResult(BaseModel):
    required_documents: List[str] = Field(default_factory=list)
    present_documents: List[str] = Field(default_factory=list)
    missing_documents: List[str] = Field(default_factory=list)
    completeness_ratio: float = 1.0
    verdict: str = "COMPLETE"


class NumericalValidationResult(BaseModel):
    income_declared: float = 0.0
    income_verified: float = 0.0
    debt_ratio: float = 0.0
    debt_ratio_compliant: bool = True
    verdict: str = "PASS"
    anomalies: List[str] = Field(default_factory=list)


class IdentityCrossRefResult(BaseModel):
    name_consistent: bool = True
    id_number_consistent: bool = True
    address_consistent: bool = True
    kyc_risk_profile: str = "LOW"
    verdict: str = "PASS"


class CreditReport(BaseModel):
    dossier_id: str
    applicant_name: str
    loan_type: str
    document_completeness: DocumentCompletenessResult
    numerical_validation: NumericalValidationResult
    identity_cross_reference: IdentityCrossRefResult
    overall_verdict: str = "APPROVE"
    overall_risk: str = "LOW"
    blocking_issues: List[str] = Field(default_factory=list)
    regulatory_references: List[str] = Field(default_factory=list)


# ── Module: Change Propagation Models ───────────────────────────

class ImpactItem(BaseModel):
    entity_type: str
    entity_id: str
    entity_name: str
    severity: str = "LOW"
    impact_description: str
    relationship_path: List[str] = Field(default_factory=list)


class ImpactPropagationReport(BaseModel):
    source_circular_ref: str
    source_circular_title: str
    total_affected: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    affected_items: List[ImpactItem] = Field(default_factory=list)
    summary: str = ""
if __name__ == "__main__":
    citation = SourceCitation(
        circular_number="2022-01",
        title="Prévention et résolution des créances non performantes",
        page=3,
        excerpt="le traitement précoce et proactif des créances..."
    )

    response = AgentResponse(
        answer="La circulaire 2022-01 définit les règles de prévention des créances non performantes.",
        sources=[citation],
        confidence_score=0.85,
        related_circulars=["2021-05"],
        graph_path_used=True,
        question_type=QuestionType.FACTUAL
    )

    print("✅ AgentResponse validé avec succès\n")
    print(response.model_dump_json(indent=2))

    state = AgentState(question="Quelles sont les règles sur les créances non performantes ?")
    print("\n✅ AgentState initialisé avec succès")
    print(state.model_dump_json(indent=2))

    try:
        AgentResponse(
            answer="test",
            sources=[],
            confidence_score=1.5,
            related_circulars=[],
            graph_path_used=False,
            question_type=QuestionType.FACTUAL
        )
        print("\n❌ La validation aurait dû échouer")
    except Exception:
        print("\n✅ Validation Pydantic fonctionne (rejet attendu : score > 1.0 refusé)")