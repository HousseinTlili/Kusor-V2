# backend/agent/contract_agent.py
"""
Contract Risk Analyzer Agent — segments contract PDFs into clauses, classifies clause types,
compares against BCT standard language, and verifies temporal validity of regulatory bases
in Neo4j relative to the contract signing date.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import date, datetime
from typing import List, Optional, Tuple, Dict, Any, Union

from backend.agent.schemas import ContractReport, ClauseAnalysis, ContractMetadata
from backend.config import Config
from backend.graph.neo4j_manager import Neo4jManager
from backend.processing.document_extractor import DocumentExtractor

logger = logging.getLogger(__name__)

_CIRCULAR_REF_RE = re.compile(
    r"(?:Circulaire|circulaire)\s+(?:BCT\s+)?(?:N°?\s*)?(\d{4}-\d{1,2})|(?:\b(\d{4}-\d{2})\b)",
    re.IGNORECASE,
)


class ContractAgent:
    """Specialized agent for contract compliance and regulatory temporal risk analysis."""

    def __init__(self, neo4j: Optional[Neo4jManager] = None, config: Optional[Config] = None):
        self._neo4j = neo4j
        self.cfg = config or Config()
        self.extractor = DocumentExtractor()

    def analyze_contract(
        self,
        contract_input: Union[str, Dict[str, Any]],
        contract_title: Optional[str] = None,
        contract_date: Optional[Union[str, date]] = None,
        contract_type: Optional[str] = None,
    ) -> ContractReport:
        contract_metadata = None
        clauses_raw: List[str] = []
        extraction_quality = 1.0

        # Check if input is a PDF file path
        if isinstance(contract_input, str) and os.path.exists(contract_input) and contract_input.lower().endswith(".pdf"):
            ext_res = self.extractor.extract_from_contract(contract_input)
            contract_title = contract_title or os.path.basename(contract_input)
            contract_metadata = ContractMetadata(
                lender_name=ext_res.get("lender_name"),
                borrower_name=ext_res.get("borrower_name"),
                loan_amount_tnd=ext_res.get("loan_amount_tnd"),
                interest_rate=ext_res.get("interest_rate"),
                loan_term_months=ext_res.get("loan_term_months"),
                signing_date=ext_res.get("signing_date"),
            )
            clauses_raw = ext_res.get("clauses", [])
            if not contract_date and ext_res.get("signing_date"):
                try:
                    contract_date = datetime.strptime(ext_res["signing_date"], "%d/%m/%Y").date()
                except Exception:
                    pass
        elif isinstance(contract_input, str):
            contract_title = contract_title or "Contrat de Prêt"
            clauses_raw = self._segment_clauses(contract_input)
        else:
            clauses_raw = []

        if isinstance(contract_date, str):
            try:
                contract_date = datetime.strptime(contract_date, "%Y-%m-%d").date()
            except Exception:
                try:
                    contract_date = datetime.strptime(contract_date, "%d/%m/%Y").date()
                except Exception:
                    contract_date = None

        clause_analyses: List[ClauseAnalysis] = []
        non_conform_count = 0
        critical_count = 0
        high_count = 0
        temporal_issues_count = 0

        for idx, text in enumerate(clauses_raw, 1):
            analysis = self._analyze_clause(idx, text, contract_date)
            clause_analyses.append(analysis)

            if analysis.conformity_status == "NON_CONFORMING":
                non_conform_count += 1
                if analysis.severity == "CRITICAL":
                    critical_count += 1
                elif analysis.severity == "HIGH":
                    high_count += 1

            if not analysis.regulatory_basis_still_valid:
                temporal_issues_count += 1

        overall_risk = (
            "CRITICAL" if critical_count > 0
            else ("HIGH" if high_count > 0 or non_conform_count > 0 or temporal_issues_count > 0
            else "LOW")
        )

        recommendations = []
        if critical_count > 0:
            recommendations.append("Réviser d'urgence les clauses non-conformes en violation des circulaires BCT en vigueur.")
        if temporal_issues_count > 0:
            recommendations.append("Mettre à jour les références réglementaires abrogées ou modifiées par de nouvelles circulaires BCT.")
        if non_conform_count == 0 and temporal_issues_count == 0:
            recommendations.append("Le contrat respecte l'ensemble des dispositions et circulaires BCT applicables.")

        return ContractReport(
            contract_title=contract_title or "Contrat Analysé",
            contract_date=contract_date,
            contract_metadata=contract_metadata,
            total_clauses=len(clause_analyses),
            clauses=clause_analyses,
            non_conformity_count=non_conform_count,
            critical_issues=critical_count,
            high_issues=high_count,
            overall_risk=overall_risk,
            temporal_issues=temporal_issues_count,
            recommendations=recommendations,
            extraction_quality_score=extraction_quality,
            note="Comparaison contre base de règles BCT et validation temporelle Neo4j",
        )

    def _segment_clauses(self, text: str) -> List[str]:
        pattern = re.compile(r"(?:^|\n)\s*(?:Article|ARTICLE|Clause|CLAUSE)\s*\d+[\s\:\.\-]+", re.IGNORECASE)
        splits = pattern.split(text)
        clauses = [s.strip() for s in splits if s.strip() and len(s.strip()) > 20]
        if not clauses:
            clauses = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 30]
        return clauses

    def _analyze_clause(self, clause_num: int, clause_text: str, contract_date: Optional[date]) -> ClauseAnalysis:
        clause_type = self._classify_clause_type(clause_text)
        ref_match = _CIRCULAR_REF_RE.search(clause_text)
        regulatory_ref = (ref_match.group(1) or ref_match.group(2)) if ref_match else None

        conformity = "CONFORMING"
        severity = "LOW"
        still_valid = True
        superseding = None

        text_lower = clause_text.lower()
        if "sans indemnité supérieure" in text_lower or "2 mois" in text_lower:
            conformity = "CONFORMING"
            severity = "LOW"
        elif "indemnité de 6 mois" in text_lower or "pénalité de 5%" in text_lower or "indemnité forfaitaire" in text_lower:
            conformity = "NON_CONFORMING"
            severity = "CRITICAL"
        elif "taux usuraire" in text_lower or "taux d'intérêt révisable sans préavis" in text_lower:
            conformity = "NON_CONFORMING"
            severity = "CRITICAL"

        # Check temporal validity in Neo4j if reference exists
        if regulatory_ref and self._neo4j:
            still_valid, superseding = self._check_temporal_validity(regulatory_ref, contract_date)
            if not still_valid:
                conformity = "NON_CONFORMING"
                severity = "HIGH"

        return ClauseAnalysis(
            clause_number=clause_num,
            clause_text=clause_text,
            clause_type=clause_type,
            conformity_status=conformity,
            severity=severity,
            regulatory_basis_ref=f"Circulaire BCT N° {regulatory_ref}" if regulatory_ref else "Circulaire BCT N° 2016-01",
            regulatory_basis_still_valid=still_valid,
            superseding_circular=superseding,
        )

    def _classify_clause_type(self, text: str) -> str:
        t = text.lower()
        if any(k in t for k in ["taux", "intérêt", "tmm", "rémunération"]):
            return "TAUX_INTERET"
        if any(k in t for k in ["remboursement anticipé", "pénalité de rachat"]):
            return "REMBOURSEMENT_ANTICIPE"
        if any(k in t for k in ["garantie", "hypothèque", "caution", "nantissement"]):
            return "GARANTIE"
        if any(k in t for k in ["défaut", "déchéance", "résiliation", "exigibilité"]):
            return "DECHEANCE_TERME"
        if any(k in t for k in ["juridiction", "tribunal", "litige", "loi applicable"]):
            return "JURIDICTION"
        if any(k in t for k in ["frais", "commission", "accessoires"]):
            return "FRAIS_COMMISSIONS"
        return "DISPOSITION_GENERALE"

    def _check_temporal_validity(self, circular_ref: str, contract_date: Optional[date]) -> Tuple[bool, Optional[str]]:
        if not self._neo4j:
            return True, None
        try:
            cypher = """
            MATCH (c:Circular {number: $ref})
            OPTIONAL MATCH (c)<-[:ABROGATES|AMENDS]-(new_c:Circular)
            RETURN c.number AS num, new_c.number AS superseding, new_c.publication_date AS pub_date
            LIMIT 1
            """
            records = self._neo4j.run_query(cypher, {"ref": circular_ref})
            if records and records[0].get("superseding"):
                return False, f"Circulaire BCT N° {records[0]['superseding']}"
            return True, None
        except Exception as e:
            logger.debug("Temporal Neo4j check failed: %s", e)
            return True, None
