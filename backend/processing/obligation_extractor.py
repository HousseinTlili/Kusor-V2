# backend/processing/obligation_extractor.py
"""
ObligationExtractor — second extraction pass over regulatory text.
Identifies regulatory obligations and classifies them into:
- PROHIBITION (Interdiction)
- REQUIREMENT (Obligation / Exigence)
- THRESHOLD (Seuil / Ratio)
- DEADLINE (Échéance / Délai)
"""

from __future__ import annotations

import logging
import re
import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import instructor
from openai import OpenAI

from backend.models.document import Document

logger = logging.getLogger(__name__)

# Regex patterns for French regulatory obligation types
_PROHIBITION_PATTERNS = [
    re.compile(r"\bil\s+est\s+interdit\b", re.IGNORECASE),
    re.compile(r"\bne\s+peuvent\s+pas\b", re.IGNORECASE),
    re.compile(r"\bne\s+peut\s+en\s+aucun\s+cas\b", re.IGNORECASE),
    re.compile(r"\binterdiction\s+de\b", re.IGNORECASE),
    re.compile(r"\bsous\s+peine\s+d['’]interdiction\b", re.IGNORECASE),
]

_REQUIREMENT_PATTERNS = [
    re.compile(r"\bsont\s+tenus\s+de\b", re.IGNORECASE),
    re.compile(r"\bdoivent\s+estimer\b|\bdoivent\s+mettre\b|\bdoivent\s+transmettre\b", re.IGNORECASE),
    re.compile(r"\best\s+tenue\s+de\b", re.IGNORECASE),
    re.compile(r"\bl['’]obligation\s+de\b", re.IGNORECASE),
    re.compile(r"\best\s+exigé\s+de\b", re.IGNORECASE),
    re.compile(r"\bdoit\s+être\b", re.IGNORECASE),
]

_THRESHOLD_PATTERNS = [
    re.compile(r"\bne\s+doit\s+pas\s+dépasser\b", re.IGNORECASE),
    re.compile(r"\bun\s+maximum\s+de\b", re.IGNORECASE),
    re.compile(r"\bun\s+minimum\s+de\b", re.IGNORECASE),
    re.compile(r"\bratio\s+de\b", re.IGNORECASE),
    re.compile(r"\bseuil\s+de\b", re.IGNORECASE),
    re.compile(r"\blimite\s+maximale\b", re.IGNORECASE),
    re.compile(r"\b\d+\s*%\b"),  # Percentage patterns
]

_DEADLINE_PATTERNS = [
    re.compile(r"\bdans\s+un\s+délai\s+de\b", re.IGNORECASE),
    re.compile(r"\bau\s+plus\s+tard\s+le\b", re.IGNORECASE),
    re.compile(r"\bavant\s+le\b", re.IGNORECASE),
    re.compile(r"\bà\s+compter\s+du\b", re.IGNORECASE),
    re.compile(r"\béchéance\b", re.IGNORECASE),
    re.compile(r"\bchaque\s+mois\b|\bchaque\s+trimestre\b|\bannuellement\b", re.IGNORECASE),
]


class ExtractedObligationSchema(BaseModel):
    """Pydantic schema for LLM-assisted obligation extraction."""
    obligation_type: str = Field(
        description="PROHIBITION | REQUIREMENT | THRESHOLD | DEADLINE"
    )
    text: str = Field(description="Exact or summarized text of the obligation")
    article_reference: Optional[str] = Field(None, description="e.g., Article 4")
    target_process: Optional[str] = Field(None, description="Affected banking process, e.g., Octroi de crédit")
    target_contract: Optional[str] = Field(None, description="Affected contract type, e.g., Convention de compte")


class SectionObligationsSchema(BaseModel):
    obligations: List[ExtractedObligationSchema] = Field(default_factory=list)


class ExtractedObligation:
    """Domain model for extracted obligation."""
    def __init__(
        self,
        obligation_id: str,
        text: str,
        obligation_type: str,
        circular_id: str,
        article_id: Optional[str] = None,
        target_process: Optional[str] = None,
        target_contract: Optional[str] = None,
    ):
        self.id = obligation_id
        self.text = text
        self.obligation_type = obligation_type  # PROHIBITION, REQUIREMENT, THRESHOLD, DEADLINE
        self.circular_id = circular_id
        self.article_id = article_id
        self.target_process = target_process
        self.target_contract = target_contract


class ObligationExtractor:
    """Extracts obligation nodes from structured regulatory sections."""

    def __init__(self, ollama_base_url: str = "http://localhost:11434", llm_model: str = "qwen2.5:7b"):
        self._ollama_base_url = ollama_base_url
        self._llm_model = llm_model

    def extract_obligations(
        self, doc: Document, sections: List[tuple[str, str]], use_llm: bool = False
    ) -> List[ExtractedObligation]:
        obligations: List[ExtractedObligation] = []

        for section_title, section_content in sections:
            # 1. Regex Pass
            regex_obs = self._extract_via_regex(doc, section_title, section_content)
            obligations.extend(regex_obs)

            # 2. LLM Pass for complex sections if enabled
            if use_llm and not regex_obs and len(section_content.split()) > 50:
                llm_obs = self._extract_via_llm(doc, section_title, section_content)
                obligations.extend(llm_obs)

        logger.info("Extracted %d obligations for doc %s", len(obligations), doc.id)
        return obligations

    def _extract_via_regex(
        self, doc: Document, section_title: str, content: str
    ) -> List[ExtractedObligation]:
        results = []
        sentences = re.split(r"(?<=[.!?])\s+", content)

        for sentence in sentences:
            sentence_clean = sentence.strip()
            if len(sentence_clean) < 15:
                continue

            ob_type = None
            if any(p.search(sentence_clean) for p in _PROHIBITION_PATTERNS):
                ob_type = "PROHIBITION"
            elif any(p.search(sentence_clean) for p in _THRESHOLD_PATTERNS):
                ob_type = "THRESHOLD"
            elif any(p.search(sentence_clean) for p in _DEADLINE_PATTERNS):
                ob_type = "DEADLINE"
            elif any(p.search(sentence_clean) for p in _REQUIREMENT_PATTERNS):
                ob_type = "REQUIREMENT"

            if ob_type:
                results.append(
                    ExtractedObligation(
                        obligation_id=f"ob_{doc.id}_{uuid.uuid4().hex[:8]}",
                        text=sentence_clean,
                        obligation_type=ob_type,
                        circular_id=doc.number or doc.circular_reference or doc.id,
                        article_id=section_title if section_title.startswith("Article") else None,
                    )
                )
        return results

    def _extract_via_llm(
        self, doc: Document, section_title: str, content: str
    ) -> List[ExtractedObligation]:
        try:
            client = instructor.from_openai(
                OpenAI(base_url=f"{self._ollama_base_url}/v1", api_key="ollama"),
                mode=instructor.Mode.JSON,
            )
            prompt = (
                f"Analyse le texte juridique suivant ({section_title}) et extrait TOUTES les obligations réglementaires bancaires.\n"
                f"Classifie chaque obligation selon son type (PROHIBITION, REQUIREMENT, THRESHOLD, DEADLINE).\n\n"
                f"Texte:\n{content}"
            )
            res = client.chat.completions.create(
                model=self._llm_model,
                response_model=SectionObligationsSchema,
                messages=[
                    {"role": "system", "content": "Tu es un expert en conformité bancaire BCT."},
                    {"role": "user", "content": prompt},
                ],
                max_retries=2,
            )

            obs = []
            for item in res.obligations:
                obs.append(
                    ExtractedObligation(
                        obligation_id=f"ob_{doc.id}_{uuid.uuid4().hex[:8]}",
                        text=item.text,
                        obligation_type=item.obligation_type,
                        circular_id=doc.number or doc.circular_reference or doc.id,
                        article_id=item.article_reference or section_title,
                        target_process=item.target_process,
                        target_contract=item.target_contract,
                    )
                )
            return obs
        except Exception as e:
            logger.warning("LLM obligation extraction skipped for section %s: %s", section_title, e)
            return []
