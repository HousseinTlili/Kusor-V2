# backend/collector/bct_scraper.py
"""
BCTScraper — scrapes Banque Centrale de Tunisie website for new regulatory circulars.
COPY from v2.
"""

from __future__ import annotations

import logging
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from backend.config import Config

logger = logging.getLogger(__name__)


class BCTScraper:
    def __init__(self, config: Optional[Config] = None):
        cfg = config or Config()
        self._base_url = cfg.BCT_BASE_URL
        self._circulars_url = cfg.BCT_CIRCULARS_URL
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "KUSOR/3.0 BCT Scraper",
        })

    def scrape_latest(self) -> List[Dict[str, str]]:
        try:
            resp = self._session.get(self._circulars_url, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.error("Failed to fetch BCT circulars page: %s", e)
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        circulars = []

        for row in soup.select("table tr"):
            cells = row.find_all("td")
            if len(cells) < 3:
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
