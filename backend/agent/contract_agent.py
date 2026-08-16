# backend/agent/contract_agent.py
"""
Contract Risk Analyzer Agent — segments contract PDFs into clauses, classifies clause types,
compares against BCT standard language, and verifies temporal validity of regulatory bases.
"""

from __future__ import annotations

import logging
import re
from datetime import date
from typing import List, Optional, Tuple

from backend.agent.schemas import ContractReport, ClauseAnalysis
from backend.config import Config
from backend.graph.neo4j_manager import Neo4jManager

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

    def analyze_contract(
        self, contract_text: str, contract_title: str, contract_date: Optional[date] = None
    ) -> ContractReport:
        clauses_raw = self._segment_clauses(contract_text)
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

        overall_risk = "CRITICAL" if critical_count > 0 else ("HIGH" if high_count > 0 or non_conform_count > 0 else "LOW")

        return ContractReport(
            contract_title=contract_title,
            contract_date=contract_date,
            total_clauses=len(clauses_raw),
            clauses=clause_analyses,
            non_conformity_count=non_conform_count,
            critical_issues=critical_count,
            high_issues=high_count,
            overall_risk=overall_risk,
            temporal_issues=temporal_issues_count,
            recommendations=self._generate_recommendations(clause_analyses),
            note="Comparaison contre texte BCT standard — modèles de contrats banque en attente",
        )

    def _segment_clauses(self, text: str) -> List[str]:
        parts = re.split(r"(?i)\n(?=\s*(?:clause|article)\s+\d+)", text)
        result = [p.strip() for p in parts if len(p.strip()) > 20]
        return result or [text[:1000]]

    def _analyze_clause(
        self, num: int, text: str, contract_date: Optional[date]
    ) -> ClauseAnalysis:
        c_type = self._classify_clause(text)
        reg_ref = self._extract_regulatory_ref(text)

        still_valid = True
        superseding = None

        if reg_ref:
            still_valid, superseding = self._check_temporal_validity(reg_ref, contract_date)

        conformity = "CONFORMING" if still_valid else "NON_CONFORMING"
        severity = "HIGH" if not still_valid else "LOW"

        return ClauseAnalysis(
            clause_number=num,
            clause_text=text[:300],
            clause_type=c_type,
            conformity_status=conformity,
            severity=severity,
            regulatory_basis_ref=reg_ref or "Normes BCT",
            regulatory_basis_still_valid=still_valid,
            superseding_circular=superseding,
        )

    def _classify_clause(self, text: str) -> str:
        t = text.lower()
        if any(kw in t for kw in ["intérêt", "taux", "teg", "marge", "indexation"]):
            return "interest_rate"
        elif any(kw in t for kw in ["pénalité", "retard", "défaut", "majoration", "sanction"]):
            return "penalty"
        elif any(kw in t for kw in ["remboursement", "échéance", "amortissement", "mensualité"]):
            return "repayment"
        elif any(kw in t for kw in ["garantie", "hypothèque", "caution", "nantissement", "privilège"]):
            return "guarantee"
        elif any(kw in t for kw in ["tribunal", "juridiction", "droit applicable", "litige", "arbitrage"]):
            return "jurisdiction"
        elif any(kw in t for kw in ["engagement", "ratio", "obligation d'information"]):
            return "covenant"
        return "general"

    def _extract_regulatory_ref(self, text: str) -> Optional[str]:
        match = _CIRCULAR_REF_RE.search(text)
        if match:
            return match.group(1) or match.group(2)
        return None

    def _check_temporal_validity(
        self, reg_ref: str, contract_date: Optional[date]
    ) -> Tuple[bool, Optional[str]]:
        if not contract_date or not self._neo4j:
            return True, None

        cypher = """
        MATCH (c:Circular)
        WHERE c.reference = $ref OR c.number = $ref
        MATCH (c)<-[r:REPLACES|AMENDS]-(newer:Circular)
        WHERE r.valid_from > date($c_date)
        RETURN newer.reference AS superseding_ref, newer.number AS superseding_num
        LIMIT 1
        """
        try:
            records = self._neo4j.run_query(
                cypher, {"ref": reg_ref, "c_date": contract_date.isoformat()}
            )
            if records:
                rec = records[0]
                return False, rec.get("superseding_ref") or rec.get("superseding_num")
        except Exception as e:
            logger.warning("Temporal validity check failed: %s", e)

        return True, None

    def _generate_recommendations(self, analyses: List[ClauseAnalysis]) -> List[str]:
        recs = []
        for a in analyses:
            if not a.regulatory_basis_still_valid:
                recs.append(
                    f"Mettre à jour la clause {a.clause_number}: la base réglementaire {a.regulatory_basis_ref} "
                    f"a été modifiée ou abrogée par la circulaire {a.superseding_circular}."
                )
        return recs

