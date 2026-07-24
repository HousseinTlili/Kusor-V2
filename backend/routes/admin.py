"""Admin namespace: stats and manual sync."""
from flask import current_app
from flask_restx import Namespace, Resource, fields, abort
from flask_jwt_extended import jwt_required
import chromadb
from backend.models.document import Document
from backend.models.chunk import Chunk
from backend.models.audit_log import AuditLog
from backend.extensions import db
from backend.middleware.auth import admin_required, audit_action
from backend.graph.cypher_queries import GET_GRAPH_STATS

api = Namespace("admin", description="Admin operations")

# RESTX Models for Swagger
neo4j_stats_model = api.model("Neo4jStats", {
    "circular_nodes": fields.Integer(description="Number of Circular nodes"),
    "entity_nodes": fields.Integer(description="Number of Entity nodes"),
    "relationships": fields.Integer(description="Number of relationship edges"),
})

chroma_stats_model = api.model("ChromaStats", {
    "count": fields.Integer(description="Number of embedded document chunks in ChromaDB"),
})

stats_response = api.model("AdminStatsResponse", {
    "document_count": fields.Integer(description="Number of documents in PostgreSQL"),
    "circular_count": fields.Integer(description="Number of distinct circulars in PostgreSQL"),
    "chunk_count": fields.Integer(description="Number of text chunks in PostgreSQL"),
    "last_sync_at": fields.String(description="Timestamp of the last scraper synchronization"),
    "neo4j_stats": fields.Nested(neo4j_stats_model, description="Knowledge graph stats"),
    "chroma_stats": fields.Nested(chroma_stats_model, description="Vector database stats"),
})

sync_response = api.model("SyncResponse", {
    "total_found": fields.Integer(description="Total circulars found on BCT site"),
    "new_count": fields.Integer(description="New circulars discovered"),
    "ingested": fields.Integer(description="Number of circulars successfully ingested"),
    "errors": fields.List(fields.String, description="Errors encountered during sync"),
    "message": fields.String(description="Status message"),
})

@api.route("/stats")
class AdminStats(Resource):
    @api.doc("admin_stats", security="Bearer")
    @jwt_required()
    @admin_required
    @api.marshal_with(stats_response)
    def get(self):
        """GET /api/admin/stats — returns system statistics"""
        try:
            document_count = Document.query.count()
            circular_count = db.session.query(Document.number).distinct().count()
            chunk_count = Chunk.query.count()
            
            # Retrieve last sync timestamp from AuditLog
            last_sync_log = AuditLog.query.filter_by(action="SYNC_TRIGGERED").order_by(AuditLog.created_at.desc()).first()
            last_sync_at = last_sync_log.created_at.isoformat() if last_sync_log else "Never"
            
            # Neo4j stats
            try:
                res = current_app.neo4j_manager.execute_query(GET_GRAPH_STATS)
                if res:
                    neo4j_stats = {
                        "circular_nodes": res[0].get("circulars", 0),
                        "entity_nodes": res[0].get("entities", 0),
                        "relationships": res[0].get("relationships", 0)
                    }
                else:
                    neo4j_stats = {"circular_nodes": 0, "entity_nodes": 0, "relationships": 0}
            except Exception as e:
                current_app.logger.error(f"Failed to fetch Neo4j stats: {e}")
                neo4j_stats = {"circular_nodes": -1, "entity_nodes": -1, "relationships": -1}
                
            # ChromaDB stats
            try:
                chroma_client = chromadb.HttpClient(
                    host=current_app.config["CHROMA_HOST"],
                    port=current_app.config["CHROMA_PORT"]
                )
                col = chroma_client.get_collection(name=current_app.document_processor.collection_name)
                chroma_stats = {"count": col.count()}
            except Exception as e:
                current_app.logger.error(f"Failed to fetch ChromaDB stats: {e}")
                chroma_stats = {"count": -1}
                
            return {
                "document_count": document_count,
                "circular_count": circular_count,
                "chunk_count": chunk_count,
                "last_sync_at": last_sync_at,
                "neo4j_stats": neo4j_stats,
                "chroma_stats": chroma_stats
            }
        except Exception as e:
            abort(500, f"Failed to retrieve admin stats: {str(e)}")

@api.route("/sync")
class AdminSync(Resource):
    @api.doc("manual_sync", security="Bearer")
    @jwt_required()
    @admin_required
    @audit_action("SYNC_TRIGGERED", "System")
    @api.marshal_with(sync_response)
    def post(self):
        """POST /api/admin/sync — trigger immediate BCT scraper run"""
        try:
            # Trigger immediate scraper run
            sync_result = current_app.bct_scraper.run()
            
            # Add message to result
            sync_result["message"] = f"Manual sync completed. Ingested {sync_result.get('ingested', 0)} new circulars."
            
            return sync_result
        except Exception as e:
            abort(500, f"Synchronization failed: {str(e)}")
