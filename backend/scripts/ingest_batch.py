# backend/scripts/ingest_batch.py
"""
Batch ingestion script for KUSOR v3.
Processes all circular PDF files in backend/data/uploads/ and indexes them
into PostgreSQL, ChromaDB, and Neo4j.
"""

import os
import sys
import glob
import logging

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app import create_app
from backend.extensions import db, get_chroma_collection, get_neo4j_manager
from backend.models.document import Document
from backend.processing.document_processor import DocumentProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    app = create_app()
    with app.app_context():
        uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/uploads"))
        pdf_files = sorted(glob.glob(os.path.join(uploads_dir, "*.pdf")))

        logger.info("Found %d PDF circulars in %s", len(pdf_files), uploads_dir)

        processor = DocumentProcessor(
            chroma_collection=get_chroma_collection(),
            neo4j_manager=get_neo4j_manager(),
        )

        success_count = 0
        for pdf_path in pdf_files:
            filename = os.path.basename(pdf_path)
            ref_name = os.path.splitext(filename)[0]
            title = f"Circulaire BCT N° {ref_name}"

            # Check if document already ingested
            existing = Document.query.filter(
                (Document.filename == filename) | (Document.circular_reference == ref_name)
            ).first()

            if existing and existing.indexation_state == "INDEXED":
                logger.info("Skipping already indexed document: %s", filename)
                continue

            try:
                logger.info("Ingesting document: %s", filename)
                raw_text = processor._extract_pdf(pdf_path)
                if not raw_text.strip():
                    logger.warning("No text extracted from %s", filename)
                    continue

                doc = processor.process_text_content(
                    raw_text=raw_text,
                    title=title,
                    doc_type="circular",
                    existing_doc=existing,
                )
                doc.filename = filename
                doc.circular_reference = ref_name
                db.session.commit()
                success_count += 1
                logger.info("Successfully indexed %s (ID: %s)", filename, doc.id)

            except Exception as e:
                logger.error("Failed to ingest %s: %s", filename, e)
                db.session.rollback()

        logger.info("Batch ingestion finished. Total newly indexed documents: %d", success_count)

if __name__ == "__main__":
    main()
