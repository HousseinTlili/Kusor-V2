import os
import re
import json
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from backend.models.document import Document
from backend.models.chunk import Chunk
from backend.models.audit_log import AuditLog
from backend.graph.graph_builder import CircularNode

@dataclass
class CircularMetadata:
    number: str          # e.g., "2024-01"
    title: str
    date: datetime
    category: str        # e.g., "Politique monétaire", "Supervision bancaire"
    pdf_url: str
    source_page_url: str

class BCTScraper:
    """
    Scrapes BCT (bct.gov.tn) publications page for new circulars.
    Downloads PDFs and triggers the processing + graph pipeline.
    """

    BCT_BASE_URL: str = "https://www.bct.gov.tn"
    CIRCULARS_PAGE: str = "/bct/siteprod/page.jsp?id=226"
    PDF_DOWNLOAD_DIR: str = "backend/data/circulars"

    def __init__(
        self,
        db_session: Any,  # SQLAlchemy session
        document_processor: Any,  # DocumentProcessor
        graph_builder: Any,  # GraphBuilder
    ) -> None:
        self.db_session = db_session
        self.document_processor = document_processor
        self.graph_builder = graph_builder

    def scrape_circulars(self) -> List[CircularMetadata]:
        """
        Parse BCT publications page using requests + BeautifulSoup.
        Extract: number, title, date, category, PDF URL.
        Returns list of all circulars found on the page.
        """
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        try:
            import requests
            from bs4 import BeautifulSoup
            
            url = self.BCT_BASE_URL + self.CIRCULARS_PAGE
            response = requests.get(url, verify=False, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            circulars = []
            
            # French months for date parsing
            months_map = {
                "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
                "juillet": 7, "août": 8, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12
            }
            
            # Find all <a> tags with href
            links = soup.find_all("a", href=True)
            for link in links:
                href = link["href"]
                text = link.get_text(" ", strip=True)
                
                # We only want French circular PDFs
                is_pdf = href.lower().endswith(".pdf")
                is_circ = "cir_" in href.lower() or "circulaire" in text.lower()
                is_arabic = "_ar.pdf" in href.lower() or "_ar" in href.lower()
                
                if is_pdf and is_circ and not is_arabic:
                    # Extract circular number
                    num_match = re.search(r"cir_(\d{4})_(\d+)", href.lower())
                    if num_match:
                        year = num_match.group(1)
                        num = num_match.group(2)
                        number = f"{year}-{num.zfill(2)}"
                    else:
                        num_match = re.search(r"\b(\d{4}-\d+)\b", text + " " + href)
                        if num_match:
                            number = num_match.group(1)
                        else:
                            continue
                    
                    # Parse full PDF URL
                    if href.startswith("http"):
                        pdf_url = href
                    elif href.startswith("/"):
                        pdf_url = self.BCT_BASE_URL + href
                    else:
                        pdf_url = self.BCT_BASE_URL + "/bct/siteprod/" + href
                    
                    # Parse date from link text (e.g. "du 30 décembre 2016" or "du 05 Janvier 2026")
                    date_val = datetime.utcnow()
                    date_match = re.search(r"(?i)du\s+(\d{1,2}(?:er)?)\s+(\w+)\s+(\d{4})", text)
                    if date_match:
                        try:
                            day_str = date_match.group(1).replace("er", "")
                            month_str = date_match.group(2).lower()
                            year_str = date_match.group(3)
                            
                            month_num = months_map.get(month_str, 1)
                            date_val = datetime(int(year_str), month_num, int(day_str))
                        except Exception:
                            # Fallback to circular year if parsing fails
                            year_prefix = number.split("-")[0]
                            if year_prefix.isdigit():
                                date_val = datetime(int(year_prefix), 1, 1)
                    else:
                        year_prefix = number.split("-")[0]
                        if year_prefix.isdigit():
                            date_val = datetime(int(year_prefix), 1, 1)
                    
                    # Categorize based on keywords in text
                    category = "Réglementation"
                    lower_text = text.lower()
                    if "monétaire" in lower_text or "monetaire" in lower_text:
                        category = "Politique Monétaire"
                    elif "supervision" in lower_text or "bancaire" in lower_text or "banque" in lower_text:
                        category = "Supervision Bancaire"
                    elif "change" in lower_text:
                        category = "Réglementation des Changes"
                    
                    circulars.append(CircularMetadata(
                        number=number,
                        title=text,
                        date=date_val,
                        category=category,
                        pdf_url=pdf_url,
                        source_page_url=url
                    ))
            
            # Deduplicate just in case the same link appears multiple times
            unique_circulars = []
            seen_numbers = set()
            for circ in circulars:
                if circ.number not in seen_numbers:
                    seen_numbers.add(circ.number)
                    unique_circulars.append(circ)
            
            return unique_circulars
        except Exception:
            return []

    def get_new_circulars(
        self,
        scraped: List[CircularMetadata],
    ) -> List[CircularMetadata]:
        """
        Compare scraped circulars against PostgreSQL Document table.
        Return only circulars not yet in the database.
        """
        existing_numbers = {doc[0] for doc in self.db_session.query(Document.number).all()}
        return [c for c in scraped if c.number not in existing_numbers]

    def download_pdf(
        self,
        circular: CircularMetadata,
    ) -> Optional[str]:
        """
        Download PDF to backend/data/circulars/{number}.pdf.
        Returns local file path on success, None on failure.
        """
        os.makedirs(self.PDF_DOWNLOAD_DIR, exist_ok=True)
        pdf_path = os.path.join(self.PDF_DOWNLOAD_DIR, f"{circular.number}.pdf")
        
        try:
            import requests
            response = requests.get(circular.pdf_url, verify=False, timeout=30)
            response.raise_for_status()
            with open(pdf_path, "wb") as f:
                f.write(response.content)
            return pdf_path
        except Exception:
            return None

    def ingest_circular(
        self,
        circular: CircularMetadata,
        pdf_path: str,
    ) -> Dict[str, Any]:
        """
        Full ingestion pipeline for one circular:
        1. Run DocumentProcessor
        2. Run GraphBuilder
        3. Update PostgreSQL metadata (Document record + status)
        4. Log to AuditLog table
        Returns ingestion result summary.
        """
        try:
            doc_id = self.document_processor._generate_document_id(f"{circular.number}.pdf")
            
            # 1. Run DocumentProcessor
            proc_res = self.document_processor.process_document(
                pdf_path=pdf_path,
                document_id=doc_id,
                circular_number=circular.number
            )
            
            # 2. Run GraphBuilder
            circ_node = CircularNode(
                id=doc_id,
                number=circular.number,
                title=circular.title,
                date=circular.date.strftime("%Y-%m-%d"),
                category=circular.category,
                url=circular.pdf_url,
                status="ACTIVE"
            )
            self.graph_builder.create_circular_node(circ_node)
            
            # Extract entities
            entities = [{"text": ent.text, "type": ent.label} for ent in proc_res.entities]
            self.graph_builder.create_entity_nodes(circular.number, entities)
            
            # Extract relationships
            full_text = "\n".join([chunk.get("content", "") for chunk in proc_res.chunks])
            regex_rels = self.graph_builder.extract_relationships_regex(circular.number, full_text)
            self.graph_builder.create_relationships(regex_rels)
            
            llm_rels = self.graph_builder.extract_relationships_llm(circular.number, full_text)
            self.graph_builder.create_relationships(llm_rels)
            
            # 3. Update PostgreSQL metadata
            db_doc = Document(
                id=doc_id,
                number=circular.number,
                title=circular.title,
                date=circular.date,
                category=circular.category,
                url=circular.pdf_url,
                status="ACTIVE",
                indexation_state="INDEXED" if not proc_res.errors else "FAILED"
            )
            self.db_session.add(db_doc)
            
            for chunk in proc_res.chunks:
                chunk_id = f"{doc_id}_{chunk.get('chunk_index')}"
                db_chunk = Chunk(
                    id=chunk_id,
                    document_id=doc_id,
                    chunk_index=chunk.get("chunk_index"),
                    page_number=chunk.get("page_number"),
                    content=chunk.get("content"),
                    embedding_id=chunk_id
                )
                self.db_session.add(db_chunk)
                
            # 4. Log to AuditLog
            audit = AuditLog(
                id=str(uuid.uuid4()),
                action="DOCUMENT_UPLOADED",
                entity_type="Document",
                entity_id=doc_id,
                details_json=json.dumps({
                    "number": circular.number,
                    "title": circular.title,
                    "chunks_count": len(proc_res.chunks),
                    "errors": proc_res.errors
                })
            )
            self.db_session.add(audit)
            self.db_session.commit()
            
            return {
                "success": True,
                "document_id": doc_id,
                "chunks_count": len(proc_res.chunks),
                "errors": proc_res.errors
            }
        except Exception as e:
            self.db_session.rollback()
            return {
                "success": False,
                "error": str(e)
            }

    def run(self) -> Dict[str, Any]:
        """
        Main entry point. Scrape → filter new → download → ingest each.
        Returns summary: {total_found, new_count, ingested, errors}.
        """
        scraped = self.scrape_circulars()
        new_circs = self.get_new_circulars(scraped)
        
        ingested_count = 0
        errors = []
        
        for circ in new_circs:
            pdf_path = self.download_pdf(circ)
            if not pdf_path:
                errors.append(f"Failed to download PDF for circular {circ.number}")
                continue
                
            res = self.ingest_circular(circ, pdf_path)
            if res.get("success"):
                ingested_count += 1
            else:
                errors.append(f"Failed to ingest circular {circ.number}: {res.get('error') or res.get('errors')}")
                
        return {
            "total_found": len(scraped),
            "new_count": len(new_circs),
            "ingested": ingested_count,
            "errors": errors
        }
