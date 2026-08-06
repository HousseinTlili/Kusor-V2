# backend/collector/bct_scraper.py
"""
BCTScraper — scrapes Banque Centrale de Tunisie website for new regulatory circulars
and runs automated ingestion cycle over discovered PDF documents.
"""

from __future__ import annotations

import logging
import os
import re
import uuid
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from backend.config import Config
from backend.models.document import Document

logger = logging.getLogger(__name__)


class BCTScraper:
    def __init__(self, config: Optional[Config] = None):
        self._cfg = config or Config()
        self._base_url = self._cfg.BCT_BASE_URL
        self._circulars_url = self._cfg.BCT_CIRCULARS_URL
        self._upload_folder = self._cfg.UPLOAD_FOLDER
        os.makedirs(self._upload_folder, exist_ok=True)

        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        })

    def scrape_latest(self) -> List[Dict[str, str]]:
        """Fetch list of circular PDFs published on BCT website."""
        try:
            resp = self._session.get(self._circulars_url, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.warning("Failed to reach live BCT website (%s), using local repository check", e)
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        circulars = []

        for row in soup.select("table tr"):
            cells = row.find_all("td")
            if len(cells) < 2:
                continue

            link = row.find("a", href=True)
            if not link or not link["href"].endswith(".pdf"):
                continue

            url = urljoin(self._base_url, link["href"])
            title = link.get_text(strip=True) or cells[0].get_text(strip=True)
            ref_match = re.search(r"(\d{4}-\d{1,2})", title)

            circulars.append({
                "title": title,
                "url": url,
                "reference": ref_match.group(1) if ref_match else "",
                "date": cells[-1].get_text(strip=True) if cells else "",
            })

        logger.info("Found %d circulars on BCT website", len(circulars))
        return circulars

    def run_scraping_cycle(self) -> int:
        """Run full scraping and automated ingestion cycle."""
        scraped_list = self.scrape_latest()
        ingested_count = 0

        from backend.processing.document_processor import DocumentProcessor
        dp = DocumentProcessor()

        # 1. Process online scraped circulars
        for item in scraped_list:
            pdf_url = item.get("url")
            title = item.get("title") or "Circulaire BCT"
            ref = item.get("reference") or None

            # Check if already in DB
            existing = Document.query.filter(
                (Document.title == title) | (Document.circular_reference == ref)
            ).first()
            if existing:
                continue

            try:
                pdf_resp = self._session.get(pdf_url, timeout=30)
                if pdf_resp.status_code == 200:
                    filename = f"bct_{ref or uuid.uuid4().hex[:6]}.pdf"
                    filepath = os.path.join(self._upload_folder, filename)
                    with open(filepath, "wb") as f:
                        f.write(pdf_resp.content)

                    doc = dp.process_document(filepath, doc_id=uuid.uuid4().hex, circular_ref=ref)
                    if doc:
                        ingested_count += 1
            except Exception as e:
                logger.error("Failed to download or ingest scraped circular %s: %s", pdf_url, e)

        # 2. Check upload folder for any pending unindexed local PDFs
        if os.path.exists(self._upload_folder):
            pdf_files = [f for f in os.listdir(self._upload_folder) if f.endswith(".pdf")]
            for filename in pdf_files:
                filepath = os.path.join(self._upload_folder, filename)
                ref_guess = filename.replace(".pdf", "")
                existing = Document.query.filter_by(circular_reference=ref_guess).first()
                if not existing:
                    try:
                        doc = dp.process_document(filepath, doc_id=str(uuid.uuid4()), circular_ref=ref_guess)
                        if doc:
                            ingested_count += 1
                    except Exception as e:
                        logger.error("Error ingesting local file %s: %s", filename, e)

        return ingested_count
