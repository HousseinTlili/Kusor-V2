# backend/agent/credit_agent.py
"""
Credit Dossier Pre-Screening System — multi-agent orchestration.
Three specialist sub-agents (Completeness, Numerical, Identity) run in parallel,
coordinated by a Supervisor Agent that merges reports, extracts real PDF dossier data,
and validates against BCT credit prudential standards (40% debt ratio threshold).
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Dict, Any, List, Optional, Union, Tuple
from backend.agent.schemas import (
    CreditReport,
    DocumentCompletenessResult,
    NumericalValidationResult,
    IdentityCrossRefResult,
)
from backend.processing.document_extractor import DocumentExtractor

logger = logging.getLogger(__name__)


# ── Sub-Agent 1: Document Completeness Agent ──────────────────────

class CompletenessSubAgent:
    def __init__(self, checklists: Optional[Dict[str, Any]] = None):
        self.checklists = checklists or self._load_default_checklists()

    def _load_default_checklists(self) -> Dict[str, Any]:
        path = "backend/data/reference/credit_checklist.json"
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("checklists", {})
            except Exception as e:
                logger.warning("Failed to load credit_checklist.json: %s", e)
        return {
            "personnel": {
                "label": "Crédit Personnel",
                "documents": [
                    {"code": "cin_valide", "name": "CIN valide", "status": "obligatoire"},
                    {"code": "bulletins_salaire_3", "name": "3 derniers bulletins de salaire", "status": "obligatoire"},
                    {"code": "attestation_employeur", "name": "Attestation employeur", "status": "obligatoire"},
                ]
            },
            "hypothecaire": {
                "label": "Crédit Hypothécaire",
                "documents": [
                    {"code": "cin_valide", "name": "CIN valide", "status": "obligatoire"},
                    {"code": "bulletins_salaire_3", "name": "3 derniers bulletins de salaire", "status": "obligatoire"},
                    {"code": "compromis_vente", "name": "Compromis de vente", "status": "obligatoire"},
                    {"code": "rapport_expertise_bien", "name": "Rapport d'expertise du bien", "status": "obligatoire"},
                    {"code": "attestation_assurance_vie", "name": "Attestation d'assurance-vie", "status": "conditionnel"},
                ]
            },
            "pme": {
                "label": "Crédit PME",
                "documents": [
                    {"code": "rne", "name": "Registre National des Entreprises (RNE)", "status": "obligatoire"},
                    {"code": "etats_financiers_3ans", "name": "États financiers certifiés (3 ans)", "status": "obligatoire"},
                    {"code": "business_plan", "name": "Business plan prévisionnel", "status": "obligatoire"},
                    {"code": "garanties_proposees", "name": "Garanties réelles ou personnelles", "status": "obligatoire"},
                ]
            },
            "corporate": {
                "label": "Crédit Corporate",
                "documents": [
                    {"code": "rne", "name": "RNE & Statuts à jour", "status": "obligatoire"},
                    {"code": "etats_financiers_audites", "name": "États financiers audités (3 ans)", "status": "obligatoire"},
                    {"code": "rapport_commissaire_comptes", "name": "Rapport général du CAC", "status": "obligatoire"},
                    {"code": "plan_financement", "name": "Plan de financement d'investissement", "status": "obligatoire"},
                ]
            }
        }

    def check(self, loan_type: str, provided_files: List[Union[str, Dict[str, Any]]]) -> DocumentCompletenessResult:
        loan_key = (loan_type or "personnel").lower()
        if "hypo" in loan_key or "immob" in loan_key:
            loan_key = "hypothecaire"
        elif "pme" in loan_key or "sme" in loan_key:
            loan_key = "pme"
        elif "corp" in loan_key:
            loan_key = "corporate"
        else:
            loan_key = "personnel"

        chk = self.checklists.get(loan_key, self.checklists.get("personnel", {}))
        required = [d["name"] for d in chk.get("documents", []) if d.get("status") == "obligatoire"]
        
        file_tokens = []
        for f in provided_files:
            if isinstance(f, str):
                file_tokens.append(f.lower())
            elif isinstance(f, dict):
                code = str(f.get("code", "")).lower()
                name = str(f.get("name", "")).lower()
                path = str(f.get("path", "")).lower()
                file_tokens.extend([code, name, path])

        present = []
        missing = []

        for req in required:
            req_l = req.lower()
            found = False
            for tok in file_tokens:
                if "cin" in req_l and any(k in tok for k in ["cin", "passport", "id_card"]):
                    found = True
                    break
                if "bulletin" in req_l and any(k in tok for k in ["salaire", "paie", "salary", "pay", "bulletin"]):
                    found = True
                    break
                if "compromis" in req_l and any(k in tok for k in ["compromis", "promesse", "vente", "sale", "agreement"]):
                    found = True
                    break
                if "expertise" in req_l and any(k in tok for k in ["expertise", "valuation", "bien", "rapport", "property"]):
                    found = True
                    break
                if "rne" in req_l and any(k in tok for k in ["rne", "registre", "kbis"]):
                    found = True
                    break
                if "financier" in req_l and any(k in tok for k in ["financier", "bilan", "statement", "etats"]):
                    found = True
                    break
                if req_l in tok or tok in req_l:
                    found = True
                    break

            if found:
                present.append(req)
            else:
                missing.append(req)

        ratio = round(len(present) / max(len(required), 1), 2)
        verdict = "COMPLET" if ratio == 1.0 else ("PARTIEL" if ratio >= 0.6 else "INCOMPLET")

        return DocumentCompletenessResult(
            required_documents=required,
            present_documents=present,
            missing_documents=missing,
            completeness_ratio=ratio,
            verdict=verdict,
        )


# ── Sub-Agent 2: Numerical Validation Agent ───────────────────────

class NumericalSubAgent:
    """Computes debt ratio (40% BCT limit), checks salary consistency and guarantor age."""

    def validate(
        self,
        income_declared: float,
        income_verified: float,
        monthly_repayment: float = 0.0,
        existing_debts: float = 0.0,
        guarantor_age: Optional[int] = None,
        loan_term_years: Optional[int] = None,
        property_value: Optional[float] = None,
        loan_amount: Optional[float] = None,
    ) -> NumericalValidationResult:
        anomalies: List[str] = []
        effective_income = income_verified if income_verified > 0 else income_declared

        if effective_income <= 0:
            return NumericalValidationResult(
                income_declared=income_declared,
                income_verified=income_verified,
                debt_ratio=0.0,
                debt_ratio_compliant=False,
                verdict="REJECT",
                anomalies=["Revenu mensuel nul ou non renseigné"],
            )

        # 1. Compare declared vs verified salary
        if income_declared > 0 and income_verified > 0:
            diff_pct = abs(income_declared - income_verified) / income_declared
            if diff_pct > 0.15:
                anomalies.append(
                    f"Écart significatif de revenu : déclaré {income_declared:,.0f} TND vs vérifié {income_verified:,.0f} TND ({diff_pct*100:.1f}%)"
                )

        # 2. Compute Debt Ratio: (monthly debt / monthly income) * 100
        total_monthly_commitment = monthly_repayment + existing_debts
        debt_ratio = (total_monthly_commitment / effective_income) * 100.0 if effective_income > 0 else 100.0

        # BCT circular limit: 40% (up to 45% for high-income tiers)
        compliant = debt_ratio <= 40.0
        if not compliant:
            anomalies.append(f"Taux d'endettement de {debt_ratio:.1f}% dépasse le seuil réglementaire BCT de 40%")

        # 3. Loan-to-Value check for mortgage (max 80% BCT limit)
        if property_value and loan_amount and property_value > 0:
            ltv = (loan_amount / property_value) * 100.0
            if ltv > 80.0:
                anomalies.append(f"Quotité de financement LTV ({ltv:.1f}%) dépasse la limite prudentielle BCT de 80%")

        # 4. Guarantor age limit (Age + Term <= 75)
        if guarantor_age and loan_term_years:
            if (guarantor_age + loan_term_years) > 75:
                anomalies.append(f"Âge garant à l'échéance ({guarantor_age + loan_term_years} ans) dépasse la limite BCT de 75 ans")

        verdict = "APPROVE" if compliant and len(anomalies) == 0 else ("REVIEW" if debt_ratio <= 45.0 else "REJECT")

        return NumericalValidationResult(
            income_declared=round(income_declared, 2),
            income_verified=round(effective_income, 2),
            debt_ratio=round(debt_ratio, 2),
            debt_ratio_compliant=compliant,
            verdict=verdict,
            anomalies=anomalies,
        )


# ── Sub-Agent 3: Identity Cross-Referencing Agent ──────────────────

class IdentityCrossRefAgent:
    def cross_reference(
        self,
        applicant_name: str,
        extracted_names: List[str],
        id_numbers: List[str],
        kyc_risk_profile: str = "LOW",
    ) -> IdentityCrossRefResult:
        app_name_norm = applicant_name.lower().strip()
        name_consistent = True
        for name in extracted_names:
            if name:
                ratio = len(set(app_name_norm.split()) & set(name.lower().split())) / max(len(app_name_norm.split()), 1)
                if ratio < 0.5:
                    name_consistent = False
                    break

        unique_ids = set([i for i in id_numbers if i])
        id_consistent = len(unique_ids) <= 1
        address_consistent = True

        verdict = "VALID" if name_consistent and id_consistent else "WARNING"

        return IdentityCrossRefResult(
            name_consistent=name_consistent,
            id_number_consistent=id_consistent,
            address_consistent=address_consistent,
            kyc_risk_profile=kyc_risk_profile,
            verdict=verdict,
        )


# ── Supervisor Agent ──────────────────────────────────────────────

class CreditSupervisorAgent:
    """Supervises the 3 credit sub-agents and synthesizes final dossier verdict."""

    def __init__(self):
        self.completeness_agent = CompletenessSubAgent()
        self.numerical_agent = NumericalSubAgent()
        self.identity_agent = IdentityCrossRefAgent()
        self.extractor = DocumentExtractor()

    def prescreen(
        self,
        dossier_id: str,
        applicant_name: str,
        loan_type: str,
        files: List[Union[str, Dict[str, Any]]],
        financial_data: Optional[Dict[str, Any]] = None,
        kyc_risk_profile: str = "LOW",
        declared_amount: float = 0.0,
        declared_term_months: int = 0,
    ) -> CreditReport:
        financial_data = financial_data or {}
        declared_income = float(financial_data.get("declared_income", 0.0))
        extracted_entities: Dict[str, Any] = {}

        verified_salaries = []
        extracted_names = []
        extracted_ids = []
        appraised_value = None

        total_expected_fields = 0
        total_extracted_fields = 0

        # 1. Ingest and extract metadata from raw PDF files
        for file_item in files:
            file_path = file_item if isinstance(file_item, str) else file_item.get("path", "")
            doc_type_hint = file_item.get("type", "") if isinstance(file_item, dict) else ""

            if not file_path or not os.path.exists(file_path):
                continue

            file_name = os.path.basename(file_path).lower()
            ext_type = doc_type_hint.upper() if doc_type_hint else ""

            if any(k in file_name for k in ["cin", "passport", "id_card", "identite"]) or ext_type == "CIN":
                cin_data = self.extractor.extract_from_cin(file_path)
                extracted_entities["cin"] = cin_data
                total_expected_fields += 2
                if cin_data.get("full_name"):
                    extracted_names.append(cin_data["full_name"])
                    total_extracted_fields += 1
                if cin_data.get("cin_number"):
                    extracted_ids.append(cin_data["cin_number"])
                    total_extracted_fields += 1

            elif any(k in file_name for k in ["salaire", "paie", "salary", "pay", "bulletin"]) or ext_type in ["SALAIRE", "BULLETIN_SALAIRE"]:
                sal_data = self.extractor.extract_from_salary_slip(file_path)
                extracted_entities[f"salary_{file_name}"] = sal_data
                total_expected_fields += 2
                if sal_data.get("net_monthly_salary"):
                    verified_salaries.append(sal_data["net_monthly_salary"])
                    total_extracted_fields += 1
                if sal_data.get("employee_name"):
                    extracted_names.append(sal_data["employee_name"])
                    total_extracted_fields += 1

            elif any(k in file_name for k in ["expertise", "valuation", "bien", "property"]) or ext_type in ["EXPERTISE", "PROPERTY_VALUATION"]:
                val_data = self.extractor.extract_from_property_valuation(file_path)
                extracted_entities["property_valuation"] = val_data
                total_expected_fields += 1
                if val_data.get("estimated_value_tnd"):
                    appraised_value = val_data["estimated_value_tnd"]
                    total_extracted_fields += 1

        verified_income = sum(verified_salaries) / len(verified_salaries) if verified_salaries else float(financial_data.get("verified_income", declared_income))
        if declared_income == 0.0 and verified_income > 0.0:
            declared_income = verified_income

        if not applicant_name or applicant_name == "Demandeur Inconnu":
            if extracted_names:
                applicant_name = extracted_names[0]

        # 2. Run Completeness Check
        comp_res = self.completeness_agent.check(loan_type, files)

        # 3. Estimate monthly repayment from requested amount and term if not provided
        monthly_repayment = float(financial_data.get("monthly_repayment", 0.0))
        if monthly_repayment == 0.0 and declared_amount > 0 and declared_term_months > 0:
            # Standard French/Tunisian amortized monthly loan installment formula
            monthly_rate = 0.075 / 12.0
            n = declared_term_months
            monthly_repayment = declared_amount * (monthly_rate * (1 + monthly_rate)**n) / ((1 + monthly_rate)**n - 1)

        loan_term_years = declared_term_months // 12 if declared_term_months > 0 else int(financial_data.get("loan_term_years", 15))

        # 4. Run Numerical Validation
        num_res = self.numerical_agent.validate(
            income_declared=declared_income,
            income_verified=verified_income,
            monthly_repayment=monthly_repayment,
            existing_debts=float(financial_data.get("existing_debts", 0.0)),
            guarantor_age=financial_data.get("guarantor_age"),
            loan_term_years=loan_term_years,
            property_value=appraised_value,
            loan_amount=declared_amount,
        )

        # 5. Run Identity Cross-Reference
        id_res = self.identity_agent.cross_reference(
            applicant_name=applicant_name,
            extracted_names=extracted_names,
            id_numbers=extracted_ids,
            kyc_risk_profile=kyc_risk_profile,
        )

        # 6. Synthesize Supervisor Decision
        blocking_issues = []
        if comp_res.verdict == "INCOMPLET":
            blocking_issues.append(f"Dossier incomplet : pièces manquantes ({', '.join(comp_res.missing_documents)})")
        if not num_res.debt_ratio_compliant:
            blocking_issues.append(f"Taux d'endettement non conforme ({num_res.debt_ratio:.1f}% > 40%)")
        blocking_issues.extend(num_res.anomalies)
        if id_res.verdict == "WARNING":
            blocking_issues.append("Incohérence détectée entre les pièces d'identité et les justificatifs de revenus")
        if kyc_risk_profile == "CRITICAL":
            blocking_issues.append("Alerte KYC/Sanctions critique sur le demandeur")

        if len(blocking_issues) == 0 and comp_res.verdict == "COMPLET":
            overall_verdict = "APPROVE"
            overall_risk = "LOW"
        elif any("CTAF" in b or "CRITICAL" in b or num_res.debt_ratio > 50.0 for b in blocking_issues):
            overall_verdict = "REJECT"
            overall_risk = "CRITICAL" if kyc_risk_profile == "CRITICAL" else "HIGH"
        else:
            overall_verdict = "REVIEW"
            overall_risk = "MEDIUM"

        extraction_quality = round(total_extracted_fields / max(total_expected_fields, 1), 2) if total_expected_fields > 0 else 1.0

        return CreditReport(
            dossier_id=dossier_id,
            applicant_name=applicant_name,
            loan_type=loan_type,
            document_completeness=comp_res,
            numerical_validation=num_res,
            identity_cross_reference=id_res,
            overall_verdict=overall_verdict,
            overall_risk=overall_risk,
            blocking_issues=blocking_issues,
            regulatory_references=[
                "Circulaire BCT N° 2016-01 (Protection des usagers des services bancaires)",
                "Normes prudentielles BCT sur le ratio d'endettement des particuliers (Seuil 40%)",
            ],
            extraction_quality_score=extraction_quality,
            extracted_entities=extracted_entities if extracted_entities else None,
        )
