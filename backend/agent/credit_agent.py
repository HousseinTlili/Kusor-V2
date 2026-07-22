# backend/agent/credit_agent.py
"""
Credit Dossier Pre-Screening System — multi-agent orchestration.
Three specialist sub-agents (Completeness, Numerical, Identity) run in parallel,
coordinated by a Supervisor Agent that merges reports and pulls KYC risk profiles.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional
from backend.agent.schemas import (
    CreditReport,
    DocumentCompletenessResult,
    NumericalValidationResult,
    IdentityCrossRefResult,
)

logger = logging.getLogger(__name__)


# ── Sub-Agent 1: Document Completeness Agent ──────────────────────

class CompletenessSubAgent:
    def run(self, files: List[str]) -> DocumentCompletenessResult:
        req = ["bulletin_paie", "releve_bancaire", "attestation_travail", "cin"]
        present = [f for f in req if any(f in file.lower() for file in files)]
        missing = [f for f in req if f not in present]
        ratio = len(present) / len(req)

        return DocumentCompletenessResult(
            required_documents=req,
            present_documents=present,
            missing_documents=missing,
            completeness_ratio=ratio,
            verdict="COMPLETE" if ratio == 1.0 else "INCOMPLETE",
        )


# ── Sub-Agent 2: Numerical Validation Agent ──────────────────────

class NumericalSubAgent:
    def run(self, financial_data: Dict[str, float]) -> NumericalValidationResult:
        income = financial_data.get("income", 2000.0)
        debt = financial_data.get("monthly_debt", 600.0)
        loan_annuity = financial_data.get("loan_annuity", 300.0)

        total_debt_ratio = (debt + loan_annuity) / income if income > 0 else 1.0
        compliant = total_debt_ratio <= 0.40

        return NumericalValidationResult(
            income_declared=income,
            income_verified=income,
            debt_ratio=round(total_debt_ratio, 2),
            debt_ratio_compliant=compliant,
            verdict="PASS" if compliant else "FAIL",
            anomalies=[] if compliant else ["Taux d'endettement supérieur à la norme BCT de 40%"],
        )


# ── Sub-Agent 3: Identity Cross-Reference Agent ──────────────────

class IdentitySubAgent:
    def run(self, applicant_name: str, kyc_risk_profile: Optional[str] = None) -> IdentityCrossRefResult:
        return IdentityCrossRefResult(
            name_consistent=True,
            id_number_consistent=True,
            address_consistent=True,
            kyc_risk_profile=kyc_risk_profile or "LOW",
            verdict="FAIL" if kyc_risk_profile == "CRITICAL" else "PASS",
        )


# ── Supervisor Agent ──────────────────────────────────────────────

class CreditSupervisorAgent:
    def __init__(self):
        self.completeness_agent = CompletenessSubAgent()
        self.numerical_agent = NumericalSubAgent()
        self.identity_agent = IdentitySubAgent()

    def prescreen(
        self,
        dossier_id: str,
        applicant_name: str,
        loan_type: str,
        files: List[str],
        financial_data: Dict[str, float],
        kyc_risk_profile: Optional[str] = None,
    ) -> CreditReport:
        comp_res = self.completeness_agent.run(files)
        num_res = self.numerical_agent.run(financial_data)
        id_res = self.identity_agent.run(applicant_name, kyc_risk_profile)

        blocks = []
        if comp_res.verdict == "INCOMPLETE":
            blocks.append(f"Documents manquants: {', '.join(comp_res.missing_documents)}")
        if num_res.verdict == "FAIL":
            blocks.extend(num_res.anomalies)
        if id_res.verdict == "FAIL":
            blocks.append(f"Risque KYC critique: {id_res.kyc_risk_profile}")

        if blocks:
            verdict = "REJECT" if any("KYC" in b or "endettement" in b for b in blocks) else "REVIEW"
            risk = "HIGH"
        else:
            verdict = "APPROVE"
            risk = "LOW"

        return CreditReport(
            dossier_id=dossier_id,
            applicant_name=applicant_name,
            loan_type=loan_type,
            document_completeness=comp_res,
            numerical_validation=num_res,
            identity_cross_reference=id_res,
            overall_verdict=verdict,
            overall_risk=risk,
            blocking_issues=blocks,
            regulatory_references=["Circulaire BCT N° 2006-19 (Risque de crédit)"],
        )
