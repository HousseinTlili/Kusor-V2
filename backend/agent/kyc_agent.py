# backend/agent/kyc_agent.py
"""
KYC Compliance Agent — ingests client onboarding dossier PDFs, extracts structured client data
via DocumentExtractor, checks document completeness against BCT KYC circulars, screens names
against local/international sanctions lists, and outputs a comprehensive KYCReport.
"""

from __future__ import annotations

import difflib
import json
import logging
import os
import re
from typing import List, Dict, Any, Optional, Union, Tuple

from backend.agent.schemas import KYCReport, DocumentCheckResult, SanctionsScreeningResult
from backend.config import Config
from backend.processing.document_extractor import DocumentExtractor

logger = logging.getLogger(__name__)


class KYCAgent:
    """Specialized agent for client onboarding KYC validation and automated dossier parsing."""

    def __init__(self, config: Optional[Config] = None):
        self.cfg = config or Config()
        self.checklists = self._load_checklists()
        self.extractor = DocumentExtractor()

    def _load_checklists(self) -> Dict[str, Any]:
        base_dir = getattr(self.cfg, "BASE_DIR", os.getcwd())
        path = os.path.join(base_dir, "backend/data/reference/kyc_checklist.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("checklists", {})
            except Exception as e:
                logger.warning("Failed to load kyc_checklist.json: %s", e)

        return {
            "individuel": {
                "label": "Client Individuel",
                "documents": [
                    {"id": "IND-01", "name": "Carte d'identité nationale (CIN)", "status": "obligatoire", "code": "cin_valide"},
                    {"id": "IND-02", "name": "Justificatif de domicile de moins de 3 mois", "status": "obligatoire", "validity_months": 3, "code": "justificatif_domicile"},
                    {"id": "IND-03", "name": "Justificatif de revenus / bulletin de salaire", "status": "obligatoire", "code": "bulletin_salaire"},
                    {"id": "IND-04", "name": "Déclaration d'origine des fonds", "status": "conditionnel", "code": "declaration_origine_fonds", "condition": "Dépôt supérieur à 50 000 TND"},
                    {"id": "IND-05", "name": "Spécimen de signature", "status": "obligatoire", "code": "specimen_signature"},
                ]
            },
            "corporate": {
                "label": "Client Corporate",
                "documents": [
                    {"id": "CORP-01", "name": "Registre de commerce (RNE)", "status": "obligatoire", "code": "rne"},
                    {"id": "CORP-02", "name": "Statuts de la société", "status": "obligatoire", "code": "statuts_societe"},
                    {"id": "CORP-03", "name": "Liste des bénéficiaires effectifs", "status": "obligatoire", "code": "liste_beneficiaires_effectifs"},
                    {"id": "CORP-04", "name": "États financiers des 2 derniers exercices", "status": "conditionnel", "code": "etats_financiers_2ans"},
                    {"id": "CORP-05", "name": "Procès-verbal de nomination des signataires", "status": "obligatoire", "code": "pv_nomination_signataires"},
                ]
            },
            "ppe": {
                "label": "Client PPE",
                "documents": [
                    {"id": "PPE-01", "name": "Déclaration de statut PPE", "status": "obligatoire", "code": "declaration_statut_ppe"},
                    {"id": "PPE-02", "name": "Justificatif de la fonction exercée", "status": "obligatoire", "code": "justificatif_fonction"},
                    {"id": "PPE-03", "name": "Déclaration détaillée d'origine des fonds", "status": "obligatoire", "code": "declaration_detaillee_origine_fonds"},
                    {"id": "PPE-04", "name": "Validation renforcée hiérarchie / conformité", "status": "obligatoire", "code": "validation_renforcee_hierarchie"},
                ]
            }
        }

    def run_kyc_check(
        self,
        client_name: Optional[str] = None,
        client_type: str = "individuel",
        dossier_files: Optional[Union[List[str], List[Dict[str, Any]]]] = None,
        deposit_amount_tnd: float = 0.0,
        sanctions_match_override: Optional[bool] = None,
        sanctions_list_override: Optional[str] = None,
        dossier_id: Optional[str] = None,
    ) -> KYCReport:
        dossier_files = dossier_files or []
        client_type_norm = (client_type or "individuel").lower()
        if client_type_norm in ["individual", "individuel"]:
            client_type_key = "individuel"
        elif client_type_norm in ["pep", "ppe"]:
            client_type_key = "ppe"
        else:
            client_type_key = "corporate"

        # 1. Automatic Document Extraction from raw PDF files
        extracted_entities: Dict[str, Any] = {}
        processed_files_info: List[Dict[str, Any]] = []
        total_fields_expected = 0
        total_fields_extracted = 0

        for file_item in dossier_files:
            file_path = file_item if isinstance(file_item, str) else file_item.get("path", "")
            doc_type_hint = file_item.get("type", "") if isinstance(file_item, dict) else ""

            if not file_path or not os.path.exists(file_path):
                if isinstance(file_item, dict):
                    processed_files_info.append(file_item)
                continue

            file_name = os.path.basename(file_path).lower()
            ext_type = doc_type_hint.upper() if doc_type_hint else ""

            if any(k in file_name for k in ["cin", "passport", "passeport", "id_card", "identite"]) or ext_type in ["CIN", "PASSEPORT", "IND-01"]:
                cin_data = self.extractor.extract_from_cin(file_path)
                extracted_entities["cin"] = cin_data
                total_fields_expected += 4
                total_fields_extracted += sum(1 for k in ["cin_number", "full_name", "date_of_birth", "address"] if cin_data.get(k))
                if not client_name and cin_data.get("full_name"):
                    client_name = cin_data["full_name"]
                processed_files_info.append({"code": "cin_valide", "name": "Carte d'identité nationale (CIN)", "present": True, "expired": False})

            elif any(k in file_name for k in ["salaire", "paie", "salary", "pay", "bulletin", "revenu"]) or ext_type in ["SALAIRE", "BULLETIN_SALAIRE", "IND-03"]:
                sal_data = self.extractor.extract_from_salary_slip(file_path)
                extracted_entities["salary"] = sal_data
                total_fields_expected += 3
                total_fields_extracted += sum(1 for k in ["employer_name", "employee_name", "net_monthly_salary"] if sal_data.get(k))
                if not client_name and sal_data.get("employee_name"):
                    client_name = sal_data["employee_name"]
                processed_files_info.append({"code": "bulletin_salaire", "name": "Justificatif de revenus / bulletin de salaire", "present": True, "expired": False})

            elif any(k in file_name for k in ["domicile", "steg", "facture", "address", "utility", "sonede"]) or ext_type in ["DOMICILE", "JUSTIFICATIF_DOMICILE", "IND-02"]:
                processed_files_info.append({"code": "justificatif_domicile", "name": "Justificatif de domicile de moins de 3 mois", "present": True, "expired": False})

            elif any(k in file_name for k in ["rne", "registre", "statuts", "kbis", "corporate"]) or ext_type in ["RNE", "CORP-01"]:
                rne_data = self.extractor.extract_from_corporate_registration(file_path)
                extracted_entities["corporate"] = rne_data
                total_fields_expected += 3
                total_fields_extracted += sum(1 for k in ["company_name", "registration_number", "legal_form"] if rne_data.get(k))
                if not client_name and rne_data.get("company_name"):
                    client_name = rne_data["company_name"]
                processed_files_info.append({"code": "rne", "name": "Registre de commerce (RNE)", "present": True, "expired": False})

            elif any(k in file_name for k in ["releve", "bancaire", "statement", "bank", "compte"]) or ext_type in ["RELEVE", "BANK_STATEMENT"]:
                bank_data = self.extractor.extract_from_bank_statement(file_path)
                extracted_entities["bank_statement"] = bank_data
                processed_files_info.append({"code": "releve_bancaire", "name": "Relevé bancaire", "present": True, "expired": False})

            elif any(k in file_name for k in ["signature", "specimen"]) or ext_type in ["SPECIMEN", "IND-05"]:
                processed_files_info.append({"code": "specimen_signature", "name": "Spécimen de signature", "present": True, "expired": False})

            else:
                code_guess = file_name.replace(".pdf", "")
                processed_files_info.append({"code": code_guess, "name": file_name, "present": True, "expired": False})

        effective_client_name = client_name or "Client Dossier Inconnu"
        dossier_id = dossier_id or f"kyc_{re.sub(r'[^a-zA-Z0-9]', '_', effective_client_name).lower()}"
        extraction_quality = round(total_fields_extracted / max(total_fields_expected, 1), 2) if total_fields_expected > 0 else 1.0

        # 2. Check document completeness
        doc_results, ratio, has_missing_mandatory, has_expired_doc, missing_conditional_escalation = self._check_completeness(
            client_type_key, processed_files_info if processed_files_info else dossier_files, deposit_amount_tnd
        )

        # 3. Perform sanctions screening
        sanctions_results, hit = self._screen_sanctions(
            effective_client_name, sanctions_match_override, sanctions_list_override
        )

        # 4. Assess verdict & risk
        if hit:
            verdict = "Escaladé"
            risk = "CRITICAL"
        elif missing_conditional_escalation:
            verdict = "Escaladé"
            risk = "HIGH"
        elif has_missing_mandatory or has_expired_doc or ratio < 0.75:
            verdict = "Non conforme"
            risk = "HIGH" if ratio < 0.6 else "MEDIUM"
        else:
            verdict = "Conforme"
            risk = "LOW"

        recommendations = []
        if hit:
            recommendations.append("GELER le dossier immédiatement. Signalement CTAF requis (Sanctions Match).")
        if missing_conditional_escalation:
            recommendations.append("Dossier à escalader au Comité de Conformité / Validation Hiérarchique Renforcée.")
        if has_missing_mandatory:
            recommendations.append("Réclamer les pièces obligatoires manquantes avant ouverture de compte.")
        if has_expired_doc:
            recommendations.append("Renouveler les pièces justificatives expirées.")
        if extraction_quality < 0.6:
            recommendations.append("Qualité d'extraction documentaire faible : vérification visuelle manuelle recommandée.")

        return KYCReport(
            client_name=effective_client_name,
            client_type=client_type,
            dossier_id=dossier_id,
            verdict=verdict,
            overall_risk=risk,
            document_checks=doc_results,
            completeness_score=ratio,
            extraction_quality_score=extraction_quality,
            extracted_entities=extracted_entities if extracted_entities else None,
            sanctions_results=sanctions_results,
            sanctions_hit=hit,
            regulatory_references=["Circulaire BCT N° 2018-09 (KYC/AML)", "Circulaire BCT N° 2017-08"],
            recommendations=recommendations,
            agent_confidence=0.95,
        )

    def _check_completeness(
        self, client_type_key: str, files: Union[List[str], List[Dict[str, Any]]], deposit_amount_tnd: float
    ) -> Tuple[List[DocumentCheckResult], float, bool, bool, bool]:
        chk_info = self.checklists.get(client_type_key, {})
        required_docs = chk_info.get("documents", [])
        
        results: List[DocumentCheckResult] = []
        found_mandatory = 0
        total_mandatory = 0
        has_missing_mandatory = False
        has_expired_doc = False
        missing_conditional_escalation = False

        file_lookup: Dict[str, Dict[str, Any]] = {}
        for item in files:
            if isinstance(item, str):
                item_clean = item.lower()
                file_lookup[item_clean] = {"present": True, "expired": False}
            elif isinstance(item, dict):
                code = str(item.get("code", "")).lower()
                name = str(item.get("name", "")).lower()
                path = str(item.get("path", "")).lower()
                present = bool(item.get("present", True))
                expired = bool(item.get("expired", False))
                if code:
                    file_lookup[code] = {"present": present, "expired": expired}
                if name:
                    file_lookup[name] = {"present": present, "expired": expired}
                if path:
                    file_lookup[path] = {"present": present, "expired": expired}

        for req in required_docs:
            code = req.get("code", "").lower()
            doc_name = req.get("name", req.get("code"))
            status = req.get("status", "obligatoire")

            is_present = False
            is_expired = False
            for k, val in file_lookup.items():
                if (code and (code in k or k in code)) or (doc_name and (doc_name.lower() in k or k in doc_name.lower())):
                    is_present = val.get("present", True)
                    is_expired = val.get("expired", False)
                    break
                # Common keyword match
                if any(x in k and x in doc_name.lower() for x in ["cin", "domicile", "salaire", "paie", "steg", "rne", "statuts", "signature"]):
                    is_present = val.get("present", True)
                    is_expired = val.get("expired", False)
                    break

            if status == "obligatoire":
                total_mandatory += 1
                if is_present and not is_expired:
                    found_mandatory += 1
                else:
                    has_missing_mandatory = True
                    if is_expired:
                        has_expired_doc = True
            elif status == "conditionnel":
                if deposit_amount_tnd > 50000.0 and not is_present:
                    missing_conditional_escalation = True

            note = ""
            if not is_present:
                note = "Document manquant au dossier"
            elif is_expired:
                note = "Document expiré (> 3 mois ou date dépassée)"
            else:
                note = "Conforme et validé"

            results.append(
                DocumentCheckResult(
                    document_name=doc_name,
                    is_present=is_present,
                    is_valid=is_present and not is_expired,
                    notes=note,
                )
            )

        ratio = round(found_mandatory / max(total_mandatory, 1), 2)
        return results, ratio, has_missing_mandatory, has_expired_doc, missing_conditional_escalation

    def _screen_sanctions(
        self,
        name: str,
        override_match: Optional[bool] = None,
        override_list: Optional[str] = None,
    ) -> Tuple[List[SanctionsScreeningResult], bool]:
        if override_match is not None:
            list_name = override_list or "OFAC_SDN"
            res = [
                SanctionsScreeningResult(
                    list_name=list_name,
                    match_found=override_match,
                    matched_name=name if override_match else None,
                    match_score=0.98 if override_match else 0.0,
                    match_type="exact" if override_match else "none",
                )
            ]
            return res, override_match

        sanctions_db = {
            "CNCT_TUNISIE": ["Ali Trabelsi", "Belhassen Trabelsi", "Imed Trabelsi", "Sakhr El Materi"],
            "OFAC_SDN": ["Viktor Bout", "Semion Mogilevich", "Ayman Al-Zawahiri"],
            "UN_CONSOLIDATED": ["Daesh Group", "Al-Qaeda Entity"],
        }

        results: List[SanctionsScreeningResult] = []
        any_hit = False
        name_clean = name.lower().strip()

        for list_name, entries in sanctions_db.items():
            hit_for_list = False
            best_match = None
            best_score = 0.0

            for entry in entries:
                entry_clean = entry.lower().strip()
                if name_clean == entry_clean:
                    hit_for_list = True
                    best_match = entry
                    best_score = 1.0
                    break
                ratio = difflib.SequenceMatcher(None, name_clean, entry_clean).ratio()
                if ratio > 0.85 and ratio > best_score:
                    hit_for_list = True
                    best_match = entry
                    best_score = ratio

            if hit_for_list:
                any_hit = True

            results.append(
                SanctionsScreeningResult(
                    list_name=list_name,
                    match_found=hit_for_list,
                    matched_name=best_match,
                    match_score=round(best_score, 2),
                    match_type="exact" if best_score == 1.0 else ("fuzzy" if hit_for_list else "none"),
                )
            )

        return results, any_hit
