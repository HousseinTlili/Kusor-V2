# backend/routes/documents.py
"""Document management endpoints (CRUD + upload + status + reindex)."""

import os
from flask import request
from flask_jwt_extended import jwt_required
from flask_restx import Namespace, Resource
from werkzeug.datastructures import FileStorage

from backend.extensions import db, get_chroma_collection, get_neo4j_manager
from backend.models.document import Document
from backend.models.chunk import Chunk
from backend.middleware.auth import role_required
from backend.middleware.audit_middleware import audit_action
from backend.processing.document_processor import DocumentProcessor

ns = Namespace("documents", description="Document management operations")


@ns.route("/")
class DocumentList(Resource):
    @jwt_required()
    def get(self):
        """List all documents."""
        docs = Document.query.order_by(Document.created_at.desc()).all()
        return [
            {
                "id": d.id,
                "title": d.title,
                "filename": d.filename,
                "doc_type": d.doc_type,
                "circular_reference": d.number or d.circular_reference,
                "date_issued": d.date_issued.isoformat() if d.date_issued else None,
                "status": d.status,
                "indexation_state": d.indexation_state,
                "chunk_count": Chunk.query.filter_by(document_id=d.id).count(),
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in docs
        ], 200

    @jwt_required()
    @role_required("admin")
    @audit_action("DOCUMENT_UPLOADED", "document")
    def post(self):
        """Upload and process a new document (Admin only)."""
        if "file" not in request.files:
            return {"error": "Fichier manquant dans la requête"}, 400

        file = request.files["file"]
        title = request.form.get("title", file.filename)
        doc_type = request.form.get("doc_type", "circular")

        processor = DocumentProcessor(
            chroma_collection=get_chroma_collection(),
            neo4j_manager=get_neo4j_manager(),
        )

        doc = processor.process_upload(file_storage=file, title=title, doc_type=doc_type)

        return {
            "message": "Document téléversé et indexé avec succès",
            "document": {
                "id": doc.id,
                "title": doc.title,
                "circular_reference": doc.number or doc.circular_reference,
                "indexation_state": doc.indexation_state,
            },
        }, 201


@ns.route("/<string:id>")
class DocumentDetail(Resource):
    @jwt_required()
    def get(self, id):
        """Get document details and chunks."""
        doc = Document.query.get(id)
        if not doc:
            return {"error": "Document introuvable"}, 404

        chunks = Chunk.query.filter_by(document_id=doc.id).order_by(Chunk.chunk_index.asc()).all()
        return {
            "id": doc.id,
            "title": doc.title,
            "filename": doc.filename,
            "doc_type": doc.doc_type,
            "circular_reference": doc.number or doc.circular_reference,
            "date_issued": doc.date_issued.isoformat() if doc.date_issued else None,
            "status": doc.status,
            "indexation_state": doc.indexation_state,
            "raw_text": doc.raw_text,
            "chunks": [
                {
                    "id": c.id,
                    "section_title": c.section_title,
                    "content": c.content,
                    "chunk_index": c.chunk_index,
                }
                for c in chunks
            ],
        }, 200

    @jwt_required()
    @role_required("admin")
    @audit_action("DOCUMENT_DELETED", "document")
    def delete(self, id):
        """Delete document and all stored chunks (Admin only)."""
        doc = Document.query.get(id)
        if not doc:
            return {"error": "Document introuvable"}, 404

        # Delete chunks from Postgres
        Chunk.query.filter_by(document_id=doc.id).delete()
        db.session.delete(doc)
        db.session.commit()

        return {"message": "Document supprimé avec succès"}, 200
