# backend/routes/admin.py
"""Admin dashboard endpoints: /admin/stats, /admin/sync, /admin/digest. Gated to admin role."""

from flask_jwt_extended import jwt_required
from flask_restx import Namespace, Resource

from backend.extensions import get_neo4j_manager, get_chroma_collection
from backend.models.document import Document
from backend.models.user import User
from backend.models.audit_log import AuditLog
from backend.middleware.auth import role_required
from backend.middleware.audit_middleware import audit_action

ns = Namespace("admin", description="Admin & Infrastructure operations")


@ns.route("/stats")
class AdminStats(Resource):
    @jwt_required()
    @role_required("admin")
    def get(self):
        """Get system statistics across PostgreSQL, Neo4j, and ChromaDB."""
        user_count = User.query.count()
        doc_count = Document.query.count()
        audit_count = AuditLog.query.count()

        chroma_col = get_chroma_collection()
        vector_count = chroma_col.count()

        neo4j = get_neo4j_manager()
        node_res = neo4j.run_query("MATCH (n) RETURN count(n) AS cnt")
        rel_res = neo4j.run_query("MATCH ()-[r]->() RETURN count(r) AS cnt")

        neo4j_nodes = node_res[0]["cnt"] if node_res else 0
        neo4j_rels = rel_res[0]["cnt"] if rel_res else 0

        return {
            "users_total": user_count,
            "documents_total": doc_count,
            "audit_logs_total": audit_count,
            "chromadb_vectors": vector_count,
            "neo4j_nodes": neo4j_nodes,
            "neo4j_relationships": neo4j_rels,
        }, 200


@ns.route("/sync")
class AdminSync(Resource):
    @jwt_required()
    @role_required("admin")
    @audit_action("BCT_SCRAPE_TRIGGERED", "admin")
    def post(self):
        """Trigger manual BCT website scrape (Admin only)."""
        from backend.collector.bct_scraper import BCTScraper
        scraper = BCTScraper()
        count = scraper.run_scraping_cycle()
        return {"message": "Scraping BCT terminé", "new_circulars": count}, 200


@ns.route("/digest")
class AdminDigest(Resource):
    @jwt_required()
    @role_required("admin")
    def get(self):
        """Get system activity digest summary."""
        recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(20).all()
        return {
            "recent_activity": [
                {
                    "id": l.id,
                    "action": l.action,
                    "user_id": l.user_id,
                    "endpoint": l.endpoint,
                    "timestamp": l.created_at.isoformat() if l.created_at else None,
                }
                for l in recent_logs
            ]
        }, 200
