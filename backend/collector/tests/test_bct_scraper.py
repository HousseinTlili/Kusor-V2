import pytest
import os
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime
from backend.collector.bct_scraper import BCTScraper, CircularMetadata

class TestBCTScraper:
    @pytest.fixture
    def mock_dependencies(self):
        db_session = MagicMock()
        document_processor = MagicMock()
        graph_builder = MagicMock()
        return db_session, document_processor, graph_builder

    def test_parse_circular_metadata(self, mock_dependencies) -> None:
        """Mock HTTP response, verify metadata (number, title, date, URL) parsed correctly."""
        db_session, dp, gb = mock_dependencies
        scraper = BCTScraper(db_session, dp, gb)
        
        mock_html = """
        <html>
            <body>
                <ul>
                    <li><a href="documents/Cir_2024_01_fr.pdf">Circulaire aux banques n°2024-01 du 15 janvier 2024</a></li>
                </ul>
            </body>
        </html>
        """
        
        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.content = mock_html.encode("utf-8")
            mock_resp.raise_for_status.return_value = None
            mock_get.return_value = mock_resp
            
            metadata = scraper.scrape_circulars()
            
            assert len(metadata) == 1
            assert metadata[0].number == "2024-01"
            assert "Circulaire aux banques n°2024-01" in metadata[0].title
            assert metadata[0].date == datetime(2024, 1, 15)
            assert metadata[0].category == "Supervision Bancaire"
            assert metadata[0].pdf_url == "https://www.bct.gov.tn/bct/siteprod/documents/Cir_2024_01_fr.pdf"

    def test_skip_known_circulars(self, mock_dependencies) -> None:
        """Second run should skip already-ingested circulars."""
        db_session, dp, gb = mock_dependencies
        scraper = BCTScraper(db_session, dp, gb)
        
        scraped = [
            CircularMetadata("2024-01", "Title 1", datetime.now(), "Cat 1", "http://pdf1", "http://page1"),
            CircularMetadata("2024-02", "Title 2", datetime.now(), "Cat 2", "http://pdf2", "http://page2")
        ]
        
        mock_query = MagicMock()
        mock_query.all.return_value = [("2024-01",)]
        db_session.query.return_value = mock_query
        
        new_circs = scraper.get_new_circulars(scraped)
        
        assert len(new_circs) == 1
        assert new_circs[0].number == "2024-02"

    def test_download_pdf(self, mock_dependencies) -> None:
        """Mock PDF download, verify file saved to correct path."""
        db_session, dp, gb = mock_dependencies
        scraper = BCTScraper(db_session, dp, gb)
        
        circ = CircularMetadata("2024-01", "Title 1", datetime.now(), "Cat 1", "http://pdf1", "http://page1")
        
        with patch("requests.get") as mock_get, \
             patch("builtins.open", mock_open()) as mock_file, \
             patch("os.makedirs") as mock_makedirs:
             
            mock_resp = MagicMock()
            mock_resp.content = b"PDF data bytes"
            mock_resp.raise_for_status.return_value = None
            mock_get.return_value = mock_resp
            
            pdf_path = scraper.download_pdf(circ)
            
            assert pdf_path == "backend/data/circulars/2024-01.pdf"
            mock_makedirs.assert_called_once_with("backend/data/circulars", exist_ok=True)
            mock_get.assert_called_once_with("http://pdf1", verify=False, timeout=30)

    def test_ingestion_triggers_pipeline(self, mock_dependencies) -> None:
        """Verify ingest_circular calls DocumentProcessor and GraphBuilder."""
        db_session, dp, gb = mock_dependencies
        scraper = BCTScraper(db_session, dp, gb)
        
        circ = CircularMetadata("2024-01", "Title 1", datetime(2024, 1, 15), "Cat 1", "http://pdf1", "http://page1")
        
        dp._generate_document_id.return_value = "doc-uuid-123"
        proc_res = MagicMock()
        proc_res.chunks = [{"chunk_index": 0, "page_number": 1, "content": "chunk content"}]
        proc_res.entities = []
        proc_res.errors = []
        dp.process_document.return_value = proc_res
        
        gb.extract_relationships_regex.return_value = []
        gb.extract_relationships_llm.return_value = []
        
        result = scraper.ingest_circular(circ, "/path/to/circular.pdf")
        
        assert result["success"] is True
        dp._generate_document_id.assert_called_once_with("2024-01.pdf")
        dp.process_document.assert_called_once_with(
            pdf_path="/path/to/circular.pdf",
            document_id="doc-uuid-123",
            circular_number="2024-01"
        )
        
        gb.create_circular_node.assert_called_once()
        db_session.add.assert_called()
        db_session.commit.assert_called_once()

    def test_error_handling(self, mock_dependencies) -> None:
        """Network errors should be logged, not crash the scraper."""
        db_session, dp, gb = mock_dependencies
        scraper = BCTScraper(db_session, dp, gb)
        
        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception("SSL Error")
            
            results = scraper.scrape_circulars()
            assert results == []
