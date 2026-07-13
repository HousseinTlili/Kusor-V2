"""Documents namespace: CRUD + processing."""
import os
import re
import uuid
import pickle
from datetime import datetime
from flask import request, current_app
from flask_restx import Namespace, Resource, fields, abort
from flask_jwt_extended import jwt_required
import chromadb
from backend.models.document import Document
from backend.models.chunk import Chunk
from backend.models.audit_log import AuditLog
from backend.extensions import db
from backend.middleware.auth import admin_required, audit_action
from backend.collector.bct_scraper import CircularMetadata

api = Namespace("documents", description="Document management")

# RESTX Models for Swagger
document_model = api.model("DocumentResponse", {
    "id": fields.String(description="Document UUID"),
    "number": fields.String(description="Circular number"),
    "title": fields.String(description="Document title"),
    "date": fields.String(description="Publication date"),
    "category": fields.String(description="Category"),
    "url": fields.String(description="BCT URL"),
    "status": fields.String(description="ACTIVE/MODIFIED/ABROGATED"),
    "indexation_state": fields.String(description="PENDING/PROCESSING/INDEXED/FAILED"),
})

paginated_response = api.model("PaginatedDocuments", {
    "total": fields.Integer(description="Total count of documents"),
    "page": fields.Integer(description="Current page"),
    "pages": fields.Integer(description="Total pages count"),
    "limit": fields.Integer(description="Limit per page"),
    "items": fields.List(fields.Nested(document_model), description="List of documents"),
})

status_response = api.model("DocumentStatusResponse", {
    "id": fields.String(description="Document UUID"),
    "number": fields.String(description="Circular number"),
    "indexation_state": fields.String(description="PENDING/PROCESSING/INDEXED/FAILED"),
})

def delete_document_from_all_stores(doc_id: str, number: str) -> None:
    """Helper to cleanly delete a document from Postgres, ChromaDB, BM25, and Neo4j."""
    # 1. Delete associated chunks from ChromaDB
    try:
        chroma_client = chromadb.HttpClient(
            host=current_app.config["CHROMA_HOST"],
            port=current_app.config["CHROMA_PORT"]
        )
        collection = chroma_client.get_collection(name=current_app.document_processor.collection_name)
        collection.delete(where={"document_id": doc_id})
    except Exception as e:
        current_app.logger.warning(f"Failed to delete {doc_id} from ChromaDB: {e}")

    # 2. Delete from BM25 index
    bm25_index_path = current_app.document_processor.bm25_index_path
    if os.path.exists(bm25_index_path):
        try:
            with open(bm25_index_path, "rb") as f:
                bm25_data = pickle.load(f)
            corpus = bm25_data.get("corpus", [])
            chunks = bm25_data.get("chunks", [])
            
            filtered_corpus = []
            filtered_chunks = []
            for corp_item, chunk_item in zip(corpus, chunks):
                if chunk_item.get("document_id") != doc_id:
                    filtered_corpus.append(corp_item)
                    filtered_chunks.append(chunk_item)
            
            from rank_bm25 import BM25Okapi
            bm25 = BM25Okapi(filtered_corpus) if filtered_corpus else None
            
            with open(bm25_index_path, "wb") as f:
                pickle.dump({
                    "corpus": filtered_corpus,
                    "chunks": filtered_chunks,
                    "bm25": bm25
                }, f)
            # Reload BM25 index in memory in searchers if needed
            current_app.hybrid_retriever.bm25_searcher.reload_index()
        except Exception as e:
            current_app.logger.warning(f"Failed to delete {doc_id} from BM25: {e}")

    # 3. Delete from Neo4j
    try:
        current_app.neo4j_manager.execute_write(
            "MATCH (c:Circular {id: $doc_id}) DETACH DELETE c",
            {"doc_id": doc_id}
        )
        # Clean up isolated entities
        current_app.neo4j_manager.execute_write(
            "MATCH (e:Entity) WHERE not (e)--() DELETE e"
        )
    except Exception as e:
        current_app.logger.warning(f"Failed to delete {doc_id} from Neo4j: {e}")

    # 4. Delete chunks and document from Postgres
    Chunk.query.filter_by(document_id=doc_id).delete()
    Document.query.filter_by(id=doc_id).delete()
    db.session.commit()

@api.route("/")
class DocumentList(Resource):
    @api.doc("list_documents", security="Bearer")
    @jwt_required()
    @api.marshal_with(paginated_response)
    def get(self):
        """GET /api/documents/ — list all documents with pagination"""
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 10, type=int)
        
        pagination = Document.query.order_by(Document.created_at.desc()).paginate(
            page=page, per_page=limit, error_out=False
        )
        
        # Serialize datetime
        items = []
        for d in pagination.items:
            items.append({
                "id": d.id,
                "number": d.number,
                "title": d.title,
                "date": d.date.strftime("%Y-%m-%d") if d.date else None,
                "category": d.category,
                "url": d.url,
                "status": d.status,
                "indexation_state": d.indexation_state
            })
            
        return {
            "total": pagination.total,
            "page": pagination.page,
            "pages": pagination.pages,
            "limit": pagination.per_page,
            "items": items
        }

@api.route("/upload")
class DocumentUpload(Resource):
    @api.doc("upload_document", security="Bearer")
    @jwt_required()
    @admin_required
    @audit_action("DOCUMENT_UPLOADED", "Document")
    def post(self):
        """POST /api/documents/upload — upload a PDF, trigger processing pipeline"""
        if "file" not in request.files:
            abort(400, "Missing PDF file in request")
            
        file = request.files["file"]
        if not file.filename.endswith(".pdf"):
            abort(400, "Uploaded file is not a PDF")
            
        # Parse inputs
        number = request.form.get("number")
        title = request.form.get("title")
        category = request.form.get("category", "Réglementation")
        date_str = request.form.get("date")
        
        # Determine circular number
        if not number:
            num_match = re.search(r"\b(\d{4}-\d+)\b", file.filename)
            if num_match:
                number = num_match.group(1)
            else:
                abort(400, "Could not extract circular number from filename. Please provide 'number' parameter.")
                
        if not title:
            title = f"Circulaire aux banques n° {number}"
            
        if date_str:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
            except Exception:
                date = datetime.utcnow()
        else:
            date = datetime.utcnow()
            
        # Calculate deterministic document id
        doc_id = current_app.document_processor._generate_document_id(f"{number}.pdf")
        
        # Overwrite if exists
        existing_doc = Document.query.filter((Document.id == doc_id) | (Document.number == number)).first()
        if existing_doc:
            delete_document_from_all_stores(existing_doc.id, existing_doc.number)
            
        # Save file to directory
        os.makedirs(current_app.bct_scraper.PDF_DOWNLOAD_DIR, exist_ok=True)
        pdf_path = os.path.join(current_app.bct_scraper.PDF_DOWNLOAD_DIR, f"{number}.pdf")
        file.save(pdf_path)
        
        # Build Metadata
        circ_meta = CircularMetadata(
            number=number,
            title=title,
            date=date,
            category=category,
            pdf_url="",
            source_page_url="manual_upload"
        )
        
        # Run Ingestion
        result = current_app.bct_scraper.ingest_circular(circ_meta, pdf_path)
        
        if not result.get("success"):
            # Update database record to FAILED
            failed_doc = Document.query.get(doc_id)
            if failed_doc:
                failed_doc.indexation_state = "FAILED"
                db.session.commit()
            abort(500, f"Document ingestion failed: {result.get('error')}")
            
        return {
            "id": doc_id,
            "number": number,
            "title": title,
            "indexation_state": "INDEXED",
            "chunks_count": result.get("chunks_count", 0),
            "message": "Document successfully uploaded and indexed"
        }

@api.route("/<string:id>/status")
class DocumentStatus(Resource):
    @api.doc("document_status", security="Bearer")
    @jwt_required()
    @api.marshal_with(status_response)
    def get(self, id: str):
        """GET /api/documents/:id/status — get indexation state"""
        doc = Document.query.get(id)
        if not doc:
            abort(404, "Document not found")
        return doc

@api.route("/<string:id>")
class DocumentDetail(Resource):
    @api.doc("delete_document", security="Bearer")
    @jwt_required()
    @admin_required
    @audit_action("DOCUMENT_DELETED", "Document")
    def delete(self, id: str):
        """DELETE /api/documents/:id — remove document and its chunks"""
        doc = Document.query.get(id)
        if not doc:
            abort(404, "Document not found")
            
        number = doc.number
        
        # Remove local file if exists
        pdf_path = os.path.join(current_app.bct_scraper.PDF_DOWNLOAD_DIR, f"{number}.pdf")
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except Exception:
                pass
                
        delete_document_from_all_stores(id, number)
        
        return {
            "id": id,
            "number": number,
            "message": "Document successfully deleted from all stores"
        }

@api.route("/<string:id>/reindex")
class DocumentReindex(Resource):
    @api.doc("reindex_document", security="Bearer")
    @jwt_required()
    @admin_required
    @audit_action("DOCUMENT_REINDEXED", "Document")
    def post(self, id: str):
        """POST /api/documents/:id/reindex — re-process and re-index"""
        doc = Document.query.get(id)
        if not doc:
            abort(404, "Document not found")
            
        number = doc.number
        pdf_path = os.path.join(current_app.bct_scraper.PDF_DOWNLOAD_DIR, f"{number}.pdf")
        
        if not os.path.exists(pdf_path):
            # If the PDF does not exist locally, we cannot re-index it
            abort(400, f"Local PDF source file not found for circular {number}. Re-index not possible.")
            
        # Re-run ingestion. Scraper's ingest_circular will automatically call processor
        # and builder which clean up old elements and overwrite.
        
        # Build Metadata
        circ_meta = CircularMetadata(
            number=doc.number,
            title=doc.title,
            date=doc.date,
            category=doc.category or "Réglementation",
            pdf_url=doc.url or "",
            source_page_url="reindex"
        )
        
        # Clean up database records first to avoid conflict on re-insert
        delete_document_from_all_stores(id, number)
        
        result = current_app.bct_scraper.ingest_circular(circ_meta, pdf_path)
        
        if not result.get("success"):
            abort(500, f"Re-indexing failed: {result.get('error')}")
            
        return {
            "id": id,
            "number": number,
            "indexation_state": "INDEXED",
            "message": "Document successfully re-indexed"
        }
