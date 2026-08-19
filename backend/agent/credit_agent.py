# backend/agent/credit_agent.py
"""
Credit Dossier Pre-Screening System — multi-agent orchestration.
Three specialist sub-agents (Completeness, Numerical, Identity) run in parallel,
coordinated by a Supervisor Agent that merges reports and pulls KYC risk profiles.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Dict, Any, List, Optional, Union, Tuple
from backend.agent.schemas import (
    CreditReport,
    DocumentCompletenessResult,
    NumericalValidationResult,
    IdentityCrossRefResult,
)

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
                    {"code": "etats_financiers_certifies", "name": "États financiers certifiés", "status": "obligatoire"},
                    {"code": "business_plan", "name": "Business plan", "status": "conditionnel"},
                    {"code": "garanties_proposees", "name": "Garanties proposées", "status": "obligatoire"},
                ]
            },
            "corporate": {
                "label": "Crédit Corporate",
                "documents": [
                    {"code": "etats_financiers_consolides", "name": "États financiers consolidés", "status": "obligatoire"},
                    {"code": "garanties_proposees", "name": "Garanties proposées", "status": "obligatoire"},
                ]
            }
        }

    def run(self, credit_type: str, files: Union[List[str], List[Dict[str, Any]]]) -> Tuple[DocumentCompletenessResult, bool]:
        key = credit_type.lower()
        if "personnel" in key or "personal" in key:
            type_key = "personnel"
        elif "hypoth" in key or "mortgage" in key:
            type_key = "hypothecaire"
        elif "pme" in key or "sme" in key:
            type_key = "pme"
        else:
            type_key = "corporate"

        chk_info = self.checklists.get(type_key, self.checklists.get("personnel", {}))
        doc_specs = chk_info.get("documents", [])

        req_codes = [d.get("code", "") for d in doc_specs if d.get("status") == "obligatoire"]
        all_codes = [d.get("code", "") for d in doc_specs]

        file_lookup: Dict[str, bool] = {}
        for item in files:
            if isinstance(item, str):
                file_lookup[item.lower()] = True
            elif isinstance(item, dict):
                code = str(item.get("code", "")).lower()
                name = str(item.get("name", "")).lower()
                present = bool(item.get("present", True))
                if code:
                    file_lookup[code] = present
                if name:
                    file_lookup[name] = present

        present_docs = []
        missing_docs = []
        missing_mandatory = []

        for d in doc_specs:
            code = d.get("code", "").lower()
            doc_name = d.get("name", code)
            is_mandatory = (d.get("status") == "obligatoire")

            doc_aliases = [code, doc_name.lower()]
            if code == "cin_valide":
                doc_aliases.extend(["cin", "carte d'identité", "cin_passport"])
            elif code == "bulletins_salaire_3":
                doc_aliases.extend(["bulletin_paie", "bulletin_salaire", "fiche_paie", "releve_bancaire"])
            elif code == "attestation_employeur":
                doc_aliases.extend(["attestation_travail", "attestation_salaire"])

            is_present = False
            for k, p in file_lookup.items():
                if any(alias in k or k in alias for alias in doc_aliases if alias):
                    if p:
                        is_present = True
                        break


            if is_present:
                present_docs.append(doc_name)
            else:
                missing_docs.append(doc_name)
                if is_mandatory:
                    missing_mandatory.append(doc_name)

        ratio = round(len(present_docs) / len(all_codes), 2) if all_codes else 1.0
        verdict = "COMPLETE" if not missing_mandatory else "INCOMPLETE"
        has_missing_mandatory = len(missing_mandatory) > 0

        return DocumentCompletenessResult(
            required_documents=[d.get("name", d.get("code")) for d in doc_specs],
            present_documents=present_docs,
            missing_documents=missing_docs,
            completeness_ratio=ratio,
            verdict=verdict,
        ), has_missing_mandatory


# ── Sub-Agent 2: Numerical Validation Agent ──────────────────────

class NumericalSubAgent:
    def run(
        self,
        financial_data: Dict[str, Any],
        debt_ratio_val: Optional[float] = None,
        numerical_flags: Optional[List[str]] = None,
    ) -> Tuple[NumericalValidationResult, bool, bool]:
        income = financial_data.get("declared_monthly_income_tnd", financial_data.get("income", 3000.0))
        debt = financial_data.get("monthly_debt", 0.0)
        loan_annuity = financial_data.get("loan_annuity", 0.0)

        if debt_ratio_val is not None:
            raw_ratio = debt_ratio_val
            ratio = raw_ratio / 100.0 if raw_ratio > 1.0 else raw_ratio
        elif income > 0:
            ratio = (debt + loan_annuity) / income
        else:
            ratio = 1.0

        ratio = round(ratio, 2)
        flags = list(numerical_flags or [])
        anomalies = []

        compliant = ratio <= 0.40
        if not compliant:
            anomalies.append(f"Taux d'endettement de {int(ratio*100)}% supérieur à la norme BCT (40%)")

        if flags:
            anomalies.extend(flags)

        is_serious = (ratio > 0.45) or any("mineur" not in f.lower() for f in flags)
        is_borderline = (0.35 <= ratio <= 0.45) or any("mineur" in f.lower() for f in flags)



        verdict = "PASS" if (compliant and not flags) else ("FAIL" if is_serious else "REVIEW")

        return NumericalValidationResult(
            income_declared=income,
            income_verified=income,
            debt_ratio=ratio,
            debt_ratio_compliant=compliant,
            verdict=verdict,
            anomalies=anomalies,
        ), is_serious, is_borderline


# ── Sub-Agent 3: Identity Cross-Reference Agent ──────────────────

class IdentitySubAgent:
    def run(
        self,
        applicant_name: str,
        identity_flags: Optional[List[str]] = None,
        guarantor: Optional[Dict[str, Any]] = None,
        loan_term_years: int = 5,
        kyc_risk_profile: Optional[str] = None,
    ) -> Tuple[IdentityCrossRefResult, bool, bool]:
        id_flags = list(identity_flags or [])
        guarantor_issue = False

        if guarantor:
            g_age = guarantor.get("age", 0)
            g_term = guarantor.get("loan_term_years", loan_term_years)
            g_flag = guarantor.get("flag")
            if g_flag or (g_age + g_term > 75):
                guarantor_issue = True

        name_consistent = len(id_flags) == 0
        kyc_risk = kyc_risk_profile or "LOW"
        is_reject = guarantor_issue or (kyc_risk == "CRITICAL")
        is_review = len(id_flags) > 0

        verdict = "FAIL" if is_reject else ("REVIEW" if is_review else "PASS")

        return IdentityCrossRefResult(
            name_consistent=name_consistent,
            id_number_consistent=name_consistent,
            address_consistent=True,
            kyc_risk_profile=kyc_risk,
            verdict=verdict,
        ), is_reject, is_review


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
        files: List[Any],
        financial_data: Dict[str, Any],
        debt_ratio: Optional[float] = None,
        numerical_flags: Optional[List[str]] = None,
        identity_flags: Optional[List[str]] = None,
        guarantor: Optional[Dict[str, Any]] = None,
        loan_term_years: int = 5,
        kyc_risk_profile: Optional[str] = None,
    ) -> CreditReport:
        comp_res, has_missing_mandatory = self.completeness_agent.run(loan_type, files)
        num_res, num_serious, num_borderline = self.numerical_agent.run(financial_data, debt_ratio, numerical_flags)
        id_res, id_reject, id_review = self.identity_agent.run(applicant_name, identity_flags, guarantor, loan_term_years, kyc_risk_profile)

        blocks = []
        if has_missing_mandatory:
            blocks.append(f"Documents obligatoires manquants: {', '.join(comp_res.missing_documents)}")
        if num_res.anomalies:
            blocks.extend(num_res.anomalies)
        if guarantor and (guarantor.get("flag") or (guarantor.get("age", 0) + loan_term_years > 75)):
            blocks.append(f"Âge du garant ({guarantor.get('age')}) + durée du prêt ({loan_term_years} ans) > 75 ans")
        if identity_flags:
            blocks.extend(identity_flags)
        if id_res.kyc_risk_profile == "CRITICAL":
            blocks.append("Profil de risque KYC critique")

        # Determine overall verdict
        if has_missing_mandatory or num_serious or id_reject:
            overall_verdict = "REJECT"
            overall_risk = "HIGH"
        elif num_borderline or id_review:
            overall_verdict = "REVIEW"
            overall_risk = "MEDIUM"
        else:
            overall_verdict = "APPROVE"
            overall_risk = "LOW"




        return CreditReport(
            dossier_id=dossier_id,
            applicant_name=applicant_name,
            loan_type=loan_type,
            document_completeness=comp_res,
            numerical_validation=num_res,
            identity_cross_reference=id_res,
            overall_verdict=overall_verdict,
            overall_risk=overall_risk,
            blocking_issues=blocks,
            regulatory_references=["Circulaire BCT N° 2006-19 (Risque de crédit)", "Normes prudentielles BCT"],
        )

