# backend/processing/document_extractor.py
"""
DocumentExtractor — extracts structured entities and numerical metadata from banking dossier PDFs
(CIN, Salary Slips, Bank Statements, Corporate Registries, Property Valuations, Contracts).
Features PyMuPDF stream parsing with automated Tesseract OCR fallback for scanned documents.
"""

from __future__ import annotations

import io
import logging
import os
import re
from datetime import datetime, date
from typing import Dict, Any, List, Optional

import fitz  # PyMuPDF
from PIL import Image
import pytesseract

logger = logging.getLogger(__name__)


def _clean_number(text: str) -> Optional[float]:
    """Helper to convert Tunisian currency string (e.g., '2 800,000 DT', '320.000 TND') to float."""
    if not text:
        return None
    cleaned = re.sub(r"[^\d,\.]", "", text).strip()
    if not cleaned:
        return None
    if "," in cleaned and "." in cleaned:
        if cleaned.find(".") < cleaned.find(","):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        parts = cleaned.split(",")
        if len(parts[-1]) == 3 and len(parts) == 2:  # Millimes e.g. 2800,000 -> 2800.0
            cleaned = f"{parts[0]}.{parts[1]}"
        else:
            cleaned = cleaned.replace(",", ".")
    elif "." in cleaned:
        parts = cleaned.split(".")
        if len(parts) > 2:
            cleaned = "".join(parts[:-1]) + "." + parts[-1]
    try:
        return float(cleaned)
    except ValueError:
        return None


def _clean_line(text: str) -> str:
    """Strip colons, dashes, and extra whitespace from extracted values."""
    if not text:
        return ""
    cleaned = text.strip()
    if cleaned.startswith(":") or cleaned.startswith("-"):
        cleaned = cleaned[1:].strip()
    return cleaned.split("\n")[0].strip()


class DocumentExtractor:
    """Extracts structured fields from various Tunisian banking and compliance documents."""

    def __init__(self, tesseract_lang: str = "fra+ara"):
        self._tesseract_lang = tesseract_lang

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract raw text from PDF with automatic Tesseract OCR fallback."""
        if not os.path.exists(pdf_path):
            logger.warning("PDF file not found: %s", pdf_path)
            return ""

        try:
            doc = fitz.open(pdf_path)
            pages_text = []
            for page in doc:
                text = page.get_text()
                if len(text.strip()) < 80:
                    try:
                        pix = page.get_pixmap(dpi=300)
                        img = Image.open(io.BytesIO(pix.tobytes("png")))
                        ocr_text = pytesseract.image_to_string(img, lang="fra")
                        text = ocr_text if len(ocr_text.strip()) > len(text.strip()) else text
                    except Exception as ocr_err:
                        logger.debug("OCR fallback exception for %s: %s", pdf_path, ocr_err)
                pages_text.append(text)
            doc.close()
            return "\n".join(pages_text)
        except Exception as e:
            logger.error("Error reading PDF %s: %s", pdf_path, e)
            return ""

    def extract_from_cin(self, pdf_path: str) -> Dict[str, Any]:
        """Extracts identity data from Tunisian National Identity Card (CIN)."""
        raw_text = self.extract_text_from_pdf(pdf_path)
        warnings: List[str] = []

        # 1. 8-digit CIN Number
        cin_match = re.search(r"\b(\d{8})\b", raw_text)
        cin_number = cin_match.group(1) if cin_match else None
        if not cin_number:
            warnings.append("Numéro CIN à 8 chiffres non détecté")

        # 2. Full Name
        name_match = re.search(
            r"^(?:Nom\s*(?:et\s*Pr[ée]nom)?|Pr[ée]nom\s*et\s*Nom|Titulaire)\s*[:\-]\s*([^\n\r]+)",
            raw_text,
            re.IGNORECASE | re.MULTILINE,
        )
        full_name = _clean_line(name_match.group(1)) if name_match else None
        if not full_name:
            lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
            for line in lines:
                if re.match(r"^[A-Z\s]{4,30}$", line) and not any(k in line for k in ["REPUBLIQUE", "TUNISIENNE", "CARTE", "NATIONALE", "IDENTITE"]):
                    full_name = line.title()
                    break

        # 3. Date of Birth
        dob_match = re.search(
            r"^(?:N[ée]\s*le|Date\s*de\s*naissance)\s*[:\-]?\s*(\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{4})",
            raw_text,
            re.IGNORECASE | re.MULTILINE,
        )
        date_of_birth = dob_match.group(1) if dob_match else None

        # 4. Expiry / Delivery Date
        expiry_match = re.search(
            r"^(?:Expire\s*le|Valable\s*jusqu['’]au|D[ée]livr[ée]e\s*le)\s*[:\-]?\s*(\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{4}|\b20\d{2}\b)",
            raw_text,
            re.IGNORECASE | re.MULTILINE,
        )
        expiry_date = expiry_match.group(1) if expiry_match else None

        # 5. Address
        addr_match = re.search(
            r"^(?:Adresse|Domicile|R[ée]sidence)\s*[:\-]\s*([^\n\r]+)",
            raw_text,
            re.IGNORECASE | re.MULTILINE,
        )
        address = _clean_line(addr_match.group(1)) if addr_match else None

        return {
            "document_type": "CIN",
            "cin_number": cin_number,
            "full_name": full_name,
            "date_of_birth": date_of_birth,
            "expiry_date": expiry_date,
            "address": address,
            "raw_text_length": len(raw_text),
            "warnings": warnings,
        }

    def extract_from_salary_slip(self, pdf_path: str) -> Dict[str, Any]:
        """Extracts employer, employee, and monthly salary data from a pay slip."""
        raw_text = self.extract_text_from_pdf(pdf_path)
        warnings: List[str] = []

        # 1. Employer Name
        emp_match = re.search(
            r"^(?:Employeur|Soci[ée]t[ée]|Entreprise|Raison\s*Sociale)\s*[:\-]\s*([^\n\r]+)",
            raw_text,
            re.IGNORECASE | re.MULTILINE,
        )
        employer_name = _clean_line(emp_match.group(1)) if emp_match else None

        # 2. Employee Name
        empl_match = re.search(
            r"^(?:Salari[ée]|Employ[ée]|Nom\s*et\s*Pr[ée]nom|B[ée]n[ée]ficiaire)\s*[:\-]\s*([^\n\r]+)",
            raw_text,
            re.IGNORECASE | re.MULTILINE,
        )
        employee_name = _clean_line(empl_match.group(1)) if empl_match else None

        # 3. Net Monthly Salary
        net_match = re.search(
            r"(?:Net\s*[àa]\s*payer|Salaire\s*Net|Total\s*Net)[\s\:\-]+([\d\s,\.]+\s*(?:TND|DT|Dinar)?)",
            raw_text,
            re.IGNORECASE,
        )
        net_salary = _clean_number(net_match.group(1)) if net_match else None

        # 4. Gross Salary
        gross_match = re.search(
            r"(?:Salaire\s*Brut|Total\s*Brut|Brut)[\s\:\-]+([\d\s,\.]+\s*(?:TND|DT|Dinar)?)",
            raw_text,
            re.IGNORECASE,
        )
        gross_salary = _clean_number(gross_match.group(1)) if gross_match else None

        # 5. Month / Year Period
        period_match = re.search(
            r"^(?:P[ée]riode|Mois|Mois\s*de)\s*[:\-]?\s*([A-Za-zÀ-ÿ]+\s*\d{4}|\d{1,2}\/\d{4})",
            raw_text,
            re.IGNORECASE | re.MULTILINE,
        )
        period = period_match.group(1).strip() if period_match else None

        # 6. CIN Reference if included on slip
        cin_match = re.search(r"\bCIN\s*[:\-]?\s*(\d{8})\b", raw_text, re.IGNORECASE)
        cin_number = cin_match.group(1) if cin_match else None

        if net_salary is None:
            warnings.append("Salaire net à payer non détecté sur le bulletin")

        return {
            "document_type": "SALARY_SLIP",
            "employer_name": employer_name,
            "employee_name": employee_name,
            "net_monthly_salary": net_salary,
            "gross_monthly_salary": gross_salary,
            "period": period,
            "cin_number": cin_number,
            "raw_text_length": len(raw_text),
            "warnings": warnings,
        }

    def extract_from_bank_statement(self, pdf_path: str) -> Dict[str, Any]:
        """Extracts financial balance and significant transactions from a bank account statement."""
        raw_text = self.extract_text_from_pdf(pdf_path)
        warnings: List[str] = []

        # 1. Account Holder
        holder_match = re.search(
            r"^(?:Titulaire|Client|Nom\s*du\s*compte)\s*[:\-]\s*([^\n\r]+)",
            raw_text,
            re.IGNORECASE | re.MULTILINE,
        )
        account_holder = _clean_line(holder_match.group(1)) if holder_match else None

        # 2. Account Number / IBAN
        iban_match = re.search(r"\b(TN\d{2}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{2}|\d{20})\b", raw_text)
        account_number = iban_match.group(1).replace(" ", "") if iban_match else None

        # 3. Solde / Average Balance
        balance_match = re.search(
            r"(?:Solde\s*Cr[ée]diteur|Solde\s*Fin\s*de\s*P[ée]riode|Solde\s*Actuel)[\s\:\-]+([\d\s,\.]+\s*(?:TND|DT)?)",
            raw_text,
            re.IGNORECASE,
        )
        balance = _clean_number(balance_match.group(1)) if balance_match else None

        # 4. Period
        period_match = re.search(
            r"(?:P[ée]riode\s*du|Du)\s*(\d{1,2}[\/\.]\d{1,2}[\/\.]\d{4})\s*au\s*(\d{1,2}[\/\.]\d{1,2}[\/\.]\d{4})",
            raw_text,
            re.IGNORECASE,
        )
        period_str = f"Du {period_match.group(1)} au {period_match.group(2)}" if period_match else None

        # 5. Significant transactions > 5000 TND
        significant_txs = []
        for line in raw_text.splitlines():
            amt_match = re.search(r"(\d{1,3}(?:[ \.]\d{3})*(?:,\d{1,3})?)\s*(?:TND|DT)", line)
            if amt_match:
                val = _clean_number(amt_match.group(1))
                if val and val >= 5000.0:
                    significant_txs.append({"line": line.strip()[:100], "amount_tnd": val})

        return {
            "document_type": "BANK_STATEMENT",
            "account_holder": account_holder,
            "account_number": account_number,
            "current_balance": balance,
            "statement_period": period_str,
            "significant_transactions": significant_txs[:10],
            "raw_text_length": len(raw_text),
            "warnings": warnings,
        }

    def extract_from_corporate_registration(self, pdf_path: str) -> Dict[str, Any]:
        """Extracts corporate legal metadata from an RNE or Trade Register certificate."""
        raw_text = self.extract_text_from_pdf(pdf_path)
        warnings: List[str] = []

        # 1. Company Name / Raison Sociale
        comp_match = re.search(
            r"^(?:D[ée]nomination\s*Sociale|Raison\s*Sociale|Nom\s*de\s*la\s*Soci[ée]t[ée])\s*[:\-]\s*([^\n\r]+)",
            raw_text,
            re.IGNORECASE | re.MULTILINE,
        )
        company_name = _clean_line(comp_match.group(1)) if comp_match else None

        # 2. Registration ID (RNE / Matricule Fiscal)
        rne_match = re.search(
            r"(?:Matricule\s*Fiscal|Identifiant\s*Unique|RNE|RCS)[\s\:\-]+([0-9A-Z\/\-]+)",
            raw_text,
            re.IGNORECASE,
        )
        registration_number = rne_match.group(1).strip() if rne_match else None

        # 3. Legal Form (SARL, SUARL, SA, etc.)
        form_match = re.search(r"\b(SARL|SUARL|SA|SNC|SCS|Soci[ée]t[ée]\s*Anonyme)\b", raw_text, re.IGNORECASE)
        legal_form = form_match.group(1).upper() if form_match else None

        # 4. Capital Amount
        cap_match = re.search(
            r"(?:Capital\s*Social|Capital)[\s\:\-]+([\d\s,\.]+\s*(?:TND|DT|Dinars)?)",
            raw_text,
            re.IGNORECASE,
        )
        capital_amount = _clean_number(cap_match.group(1)) if cap_match else None

        # 5. Directors / Managers / Signataires
        directors = []
        dir_matches = re.finditer(
            r"^(?:G[ée]rant|Directeur\s*G[ée]n[ée]ral|Pr[ée]sident|Administrateur)\s*[:\-]\s*([^\n\r]+)",
            raw_text,
            re.IGNORECASE | re.MULTILINE,
        )
        for m in dir_matches:
            name = _clean_line(m.group(1))
            if len(name) > 3 and name not in directors:
                directors.append(name)

        return {
            "document_type": "CORPORATE_RNE",
            "company_name": company_name,
            "registration_number": registration_number,
            "legal_form": legal_form,
            "capital_amount": capital_amount,
            "directors": directors,
            "raw_text_length": len(raw_text),
            "warnings": warnings,
        }

    def extract_from_property_valuation(self, pdf_path: str) -> Dict[str, Any]:
        """Extracts appraised real estate valuation data for mortgage credit."""
        raw_text = self.extract_text_from_pdf(pdf_path)
        warnings: List[str] = []

        # 1. Estimated Value
        val_match = re.search(
            r"(?:Valeur\s*V[ée]nale\s*Estim[ée]e|Valeur\s*V[ée]nale|Valeur\s*Estim[ée]e|Valeur\s*du\s*bien|Estimation)[\s\:\-]+([\d\s,\.]+\s*(?:TND|DT|Dinars)?)",
            raw_text,
            re.IGNORECASE,
        )
        estimated_value = _clean_number(val_match.group(1)) if val_match else None

        # 2. Property Address / Location
        loc_match = re.search(
            r"^(?:Situation\s*du\s*bien|Adresse\s*du\s*bien|Localisation|Emplacement|Situation)\s*[:\-]\s*([^\n\r]+)",
            raw_text,
            re.IGNORECASE | re.MULTILINE,
        )
        property_address = _clean_line(loc_match.group(1)) if loc_match else None

        # 3. Valuation Date
        date_match = re.search(
            r"(?:Date\s*d['’]expertise|Date\s*d['’]estimation|Fait\s*le)[\s\:\-]+(\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{4})",
            raw_text,
            re.IGNORECASE,
        )
        valuation_date = date_match.group(1) if date_match else None

        # 4. Valuation Agency / Expert Name
        agency_match = re.search(
            r"^(?:Cabinet\s*d['’]expertise|Cabinet|Expert\s*Agr[ée][ée]|Expert|Bureau\s*d['’]expertise)\s*[:\-]\s*([^\n\r]+)",
            raw_text,
            re.IGNORECASE | re.MULTILINE,
        )
        agency_name = _clean_line(agency_match.group(1)) if agency_match else None

        if estimated_value is None:
            warnings.append("Valeur vénale du bien non détectée dans le rapport d'expertise")

        return {
            "document_type": "PROPERTY_VALUATION",
            "estimated_value_tnd": estimated_value,
            "property_address": property_address,
            "valuation_date": valuation_date,
            "agency_name": agency_name,
            "raw_text_length": len(raw_text),
            "warnings": warnings,
        }

    def extract_from_contract(self, pdf_path: str) -> Dict[str, Any]:
        """Extracts loan metadata and segments clauses from a credit/banking contract PDF."""
        raw_text = self.extract_text_from_pdf(pdf_path)
        warnings: List[str] = []

        # 1. Principal Loan Amount
        amt_match = re.search(
            r"(?:Montant\s*du\s*pr[êe]t|Montant\s*en\s*principal|Cr[ée]dit\s*accord[ée])[\s\:\-]+([\d\s,\.]+\s*(?:TND|DT|Dinars)?)",
            raw_text,
            re.IGNORECASE,
        )
        loan_amount = _clean_number(amt_match.group(1)) if amt_match else None

        # 2. Interest Rate
        rate_match = re.search(
            r"(?:Taux\s*d['’]int[ée]r[êe]t|Taux\s*nominal|TMM\s*\+\s*|Taux\s*fixe)[\s\:\-]+([\d,\.]+\s*%)",
            raw_text,
            re.IGNORECASE,
        )
        interest_rate = rate_match.group(1).strip() if rate_match else None

        # 3. Term / Duration
        term_match = re.search(
            r"(?:Dur[ée]e|P[ée]riode\s*de\s*remboursement)[\s\:\-]+(\d{1,3})\s*(?:mois|ans|ann[ée]es)",
            raw_text,
            re.IGNORECASE,
        )
        loan_term_months = None
        if term_match:
            val = int(term_match.group(1))
            if "an" in term_match.group(0).lower():
                val *= 12
            loan_term_months = val

        # 4. Signing Date
        date_match = re.search(
            r"(?:Fait\s*le|Date\s*de\s*signature|Sign[ée]\s*le)[\s\:\-]+(\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{4})",
            raw_text,
            re.IGNORECASE,
        )
        signing_date = date_match.group(1) if date_match else None

        # 5. Parties (Lender & Borrower)
        lender_match = re.search(
            r"^(?:La\s*Banque|Pr[êe]teur)\s*[:\-]\s*([^\n\r,]+)",
            raw_text,
            re.IGNORECASE | re.MULTILINE,
        )
        lender_name = _clean_line(lender_match.group(1)) if lender_match else "Attijari Bank Tunisia"

        borrower_match = re.search(
            r"^(?:L['’]Emprunteur|Emprunteur|Client|D[ée]biteur)\s*[:\-]\s*([^\n\r,]+)",
            raw_text,
            re.IGNORECASE | re.MULTILINE,
        )
        borrower_name = _clean_line(borrower_match.group(1)) if borrower_match else None

        # 6. Segment Contract Clauses
        clause_pattern = re.compile(
            r"(?:^|\n)\s*(?:Article|ARTICLE|Clause|CLAUSE)\s*(\d+|[IVXLCDM]+|[A-Z])\s*[:\.\-]\s*([^\n]+(?:\n(?!(?:Article|ARTICLE|Clause|CLAUSE)\s*\d+)[^\n]+)*)",
            re.IGNORECASE,
        )
        clauses = []
        for match in clause_pattern.finditer(raw_text):
            clause_body = match.group(0).strip()
            if len(clause_body) > 20:
                clauses.append(clause_body)

        if not clauses:
            clauses = [p.strip() for p in raw_text.split("\n\n") if len(p.strip()) > 50]

        return {
            "document_type": "CONTRACT",
            "lender_name": lender_name,
            "borrower_name": borrower_name,
            "loan_amount_tnd": loan_amount,
            "interest_rate": interest_rate,
            "loan_term_months": loan_term_months,
            "signing_date": signing_date,
            "clauses": clauses,
            "raw_text": raw_text,
            "warnings": warnings,
        }
