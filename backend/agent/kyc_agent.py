# backend/agent/kyc_agent.py
"""
KYC Compliance Agent — ingests client onboarding dossiers, checks document completeness
against BCT KYC circulars, screens names against local sanctions lists, and outputs a KYCReport.
"""

from __future__ import annotations

import logging
import os
import re
from typing import List, Dict, Any, Optional

from backend.agent.schemas import KYCReport, DocumentCheckResult, SanctionsScreeningResult
from backend.config import Config

logger = logging.getLogger(__name__)

# BCT KYC Standard Checklists
_REQUIRED_INDIVIDUAL_DOCS = ["cin_passport", "justificatif_domicile", "fiche_signaletique", "declaration_patrimoine"]
_REQUIRED_CORPORATE_DOCS = ["rne_extrait", "statuts_societe", "pv_nomination_gérant", "cin_gerant", "liste_beneficiaires_effectifs"]


class KYCAgent:
    """Specialized agent for client onboarding KYC validation."""

    def __init__(self, config: Optional[Config] = None):
        self.cfg = config or Config()

    def run_kyc_check(
        self, client_name: str, client_type: str, dossier_files: List[str]
    ) -> KYCReport:
        dossier_id = f"kyc_{re.sub(r'[^a-zA-Z0-9]', '_', client_name).lower()}"

        # 1. Check document completeness
        doc_results, ratio = self._check_completeness(client_type, dossier_files)

        # 2. Perform sanctions screening
        sanctions_results, hit = self._screen_sanctions(client_name)

        # 3. Assess overall risk
        if hit:
            risk = "CRITICAL"
        elif ratio < 0.75:
            risk = "HIGH"
        elif ratio < 1.0:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        recommendations = []
        if hit:
            recommendations.append("GELER le dossier immédiatement. Signalement CTAF requis.")
        if ratio < 1.0:
            recommendations.append("Réclamer les pièces manquantes avant ouverture de compte.")

        return KYCReport(
            client_name=client_name,
            client_type=client_type,
            dossier_id=dossier_id,
            overall_risk=risk,
            document_checks=doc_results,
            completeness_score=ratio,
            sanctions_results=sanctions_results,
            sanctions_hit=hit,
            regulatory_references=["Circulaire BCT N° 2018-09", "Circulaire BCT N° 2017-08"],
            recommendations=recommendations,
            agent_confidence=0.95,
        )

    def _check_completeness(
        self, client_type: str, files: List[str]
    ) -> tuple[List[DocumentCheckResult], float]:
        required = _REQUIRED_CORPORATE_DOCS if client_type == "corporate" else _REQUIRED_INDIVIDUAL_DOCS
        results = []
        found_count = 0

        files_clean = [f.lower() for f in files]
        for req in required:
            present = any(req in f for f in files_clean)
            if present:
                found_count += 1
            results.append(
                DocumentCheckResult(
                    document_name=req,
                    is_present=present,
                    is_valid=present,
                    notes="Présent dans le dossier" if present else "PIÈCE MANQUANTE",
                )
            )

        ratio = round(found_count / len(required), 2)
        return results, ratio

    def _screen_sanctions(
        self, name: str
    ) -> tuple[List[SanctionsScreeningResult], bool]:
        sanctions_dir = getattr(self.cfg, "SANCTIONS_DIR", "backend/data/sanctions")
        results = []
        any_hit = False

        for lst in ["OFAC", "EU", "UN"]:
            list_file = os.path.join(sanctions_dir, f"{lst.lower()}_list.txt")
            matched = False
            matched_name = None

            if os.path.exists(list_file):
                with open(list_file, "r", encoding="utf-8", errors="ignore") as f:
                    targets = [line.strip().lower() for line in f if line.strip()]
                    if name.lower() in targets:
                        matched = True
                        matched_name = name
                        any_hit = True

            results.append(
                SanctionsScreeningResult(
                    list_name=lst,
                    match_found=matched,
                    matched_name=matched_name,
                    match_score=1.0 if matched else 0.0,
                    match_type="exact" if matched else "none",
                )
            )

        return results, any_hit
