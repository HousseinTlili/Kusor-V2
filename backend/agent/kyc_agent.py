# backend/agent/kyc_agent.py
"""
KYC Compliance Agent — ingests client onboarding dossiers, checks document completeness
against BCT KYC circulars, screens names against local sanctions lists, and outputs a KYCReport.
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

logger = logging.getLogger(__name__)


class KYCAgent:
    """Specialized agent for client onboarding KYC validation."""

    def __init__(self, config: Optional[Config] = None):
        self.cfg = config or Config()
        self.checklists = self._load_checklists()

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
        client_name: str,
        client_type: str,
        dossier_files: Union[List[str], List[Dict[str, Any]]],
        deposit_amount_tnd: float = 0.0,
        sanctions_match_override: Optional[bool] = None,
        sanctions_list_override: Optional[str] = None,
        dossier_id: Optional[str] = None,
    ) -> KYCReport:
        dossier_id = dossier_id or f"kyc_{re.sub(r'[^a-zA-Z0-9]', '_', client_name).lower()}"
        client_type_norm = client_type.lower()
        if client_type_norm in ["individual", "individuel"]:
            client_type_key = "individuel"
        elif client_type_norm in ["pep", "ppe"]:
            client_type_key = "ppe"
        else:
            client_type_key = "corporate"

        # 1. Check document completeness
        doc_results, ratio, has_missing_mandatory, has_expired_doc, missing_conditional_escalation = self._check_completeness(
            client_type_key, dossier_files, deposit_amount_tnd
        )

        # 2. Perform sanctions screening
        sanctions_results, hit = self._screen_sanctions(
            client_name, sanctions_match_override, sanctions_list_override
        )

        # 3. Assess verdict & risk
        if hit:
            verdict = "Escaladé"
            risk = "CRITICAL"
        elif missing_conditional_escalation:
            verdict = "Escaladé"
            risk = "HIGH"
        elif has_missing_mandatory or has_expired_doc or ratio < 1.0:
            verdict = "Non conforme"
            risk = "HIGH" if ratio < 0.75 else "MEDIUM"
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

        return KYCReport(
            client_name=client_name,
            client_type=client_type,
            dossier_id=dossier_id,
            verdict=verdict,
            overall_risk=risk,
            document_checks=doc_results,
            completeness_score=ratio,
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

        # Convert provided files into lookup dict
        file_lookup: Dict[str, Dict[str, Any]] = {}
        for item in files:
            if isinstance(item, str):
                item_clean = item.lower()
                file_lookup[item_clean] = {"present": True, "expired": False}
            elif isinstance(item, dict):
                code = str(item.get("code", "")).lower()
                name = str(item.get("name", "")).lower()
                present = bool(item.get("present", True))
                expired = bool(item.get("expired", False))
                if code:
                    file_lookup[code] = {"present": present, "expired": expired}
                if name:
                    file_lookup[name] = {"present": present, "expired": expired}

        for req in required_docs:
            code = req.get("code", "").lower()
            doc_name = req.get("name", req.get("code"))
            status = req.get("status", "obligatoire")

            # Check matching in provided files
            is_present = False
            is_expired = False
            for k, val in file_lookup.items():
                if (code and code in k) or (doc_name and doc_name.lower() in k) or (k in code) or (k in doc_name.lower()):
                    if val["present"]:
                        is_present = True
                        if val["expired"]:
                            is_expired = True
                        break

            # Handle conditional rules
            is_mandatory = (status == "obligatoire")
            if code == "declaration_origine_fonds" and deposit_amount_tnd > 50000:
                is_mandatory = True
                if not is_present:
                    missing_conditional_escalation = True

            if is_mandatory:
                total_mandatory += 1
                if is_present and not is_expired:
                    found_mandatory += 1
                elif not is_present:
                    has_missing_mandatory = True
                if is_expired:
                    has_expired_doc = True

            notes = "Présent dans le dossier" if is_present else "PIÈCE MANQUANTE"
            if is_present and is_expired:
                notes = "DOCUMENT EXPIRÉ"

            results.append(
                DocumentCheckResult(
                    document_name=doc_name,
                    is_present=is_present,
                    is_valid=is_present and not is_expired,
                    notes=notes,
                )
            )

        ratio = round(found_mandatory / total_mandatory, 2) if total_mandatory > 0 else 1.0
        return results, ratio, has_missing_mandatory, has_expired_doc, missing_conditional_escalation

    def _screen_sanctions(
        self, name: str, match_override: Optional[bool] = None, list_override: Optional[str] = None
    ) -> Tuple[List[SanctionsScreeningResult], bool]:
        if match_override is not None:
            hit = bool(match_override)
            target_list = list_override or "OFAC"
            results = [
                SanctionsScreeningResult(
                    list_name=target_list,
                    match_found=hit,
                    matched_name=name if hit else None,
                    match_score=1.0 if hit else 0.0,
                    match_type="exact" if hit else "none",
                )
            ]
            return results, hit

        sanctions_dir = getattr(self.cfg, "SANCTIONS_DIR", "backend/data/sanctions")
        results = []
        any_hit = False
        name_clean = name.lower().strip()

        for lst in ["OFAC", "EU", "UN"]:
            matched = False
            matched_name = None
            match_score = 0.0

            if lst == "OFAC":
                path = os.path.join(sanctions_dir, "ofac_sdn.csv")
            elif lst == "EU":
                path = os.path.join(sanctions_dir, "eu_sanctions.xml")
            else:
                path = os.path.join(sanctions_dir, "un_sanctions.xml")

            txt_file = os.path.join(sanctions_dir, f"{lst.lower()}_list.txt")

            # Check if text/csv file exists
            if os.path.exists(path) or os.path.exists(txt_file):
                check_path = txt_file if os.path.exists(txt_file) else path
                try:
                    with open(check_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            line_clean = line.strip().lower()
                            if not line_clean:
                                continue
                            if name_clean in line_clean or line_clean in name_clean:
                                matched = True
                                matched_name = name
                                match_score = 1.0
                                any_hit = True
                                break
                            # Fuzzy matching threshold 0.85
                            if len(line_clean) > 5 and len(name_clean) > 5:
                                ratio = difflib.SequenceMatcher(None, name_clean, line_clean[:100]).ratio()
                                if ratio >= 0.85:
                                    matched = True
                                    matched_name = line.strip()[:50]
                                    match_score = round(ratio, 2)
                                    any_hit = True
                                    break
                except Exception as e:
                    logger.warning("Error screening sanctions list %s: %s", lst, e)

            results.append(
                SanctionsScreeningResult(
                    list_name=lst,
                    match_found=matched,
                    matched_name=matched_name,
                    match_score=match_score,
                    match_type="fuzzy" if matched and match_score < 1.0 else ("exact" if matched else "none"),
                )
            )

        return results, any_hit

