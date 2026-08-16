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
    def get(self):
        """Get system statistics across PostgreSQL, Neo4j, and ChromaDB."""
        user_count = User.query.count()
        doc_count = Document.query.count()
        audit_count = AuditLog.query.count()

        # Count by doc_type
        circulars_count = Document.query.filter(Document.doc_type == "circular").count()
        sanctions_count = Document.query.filter(Document.doc_type == "sanction_list").count()
        guidance_count = Document.query.filter(Document.doc_type == "guidance").count()

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
            "circulars_total": circulars_count,
            "sanctions_total": sanctions_count,
            "guidance_total": guidance_count,
            "audit_logs_total": audit_count,
            "chromadb_vectors": vector_count,
            "neo4j_nodes": neo4j_nodes,
            "neo4j_relationships": neo4j_rels,
        }, 200



@ns.route("/sync")
class AdminSync(Resource):
    def post(self):
        """Trigger full multi-source regulatory scraping and synchronization."""
        try:
            from backend.collector.multi_source_scraper import MultiSourceScraper
            scraper = MultiSourceScraper()
            result = scraper.run_full_sync()
            return result, 200
        except Exception as e:
            logger.error("Multi-source sync failed: %s", e)
            return {
                "status": "ERROR",
                "message": f"Erreur lors de la synchronisation multi-sources: {e}",
                "sources": []
            }, 500



@ns.route("/digest")
class AdminDigest(Resource):
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


@ns.route("/digest/generate")
class AdminDigestGenerate(Resource):
    def get(self):
        """Generate weekly regulatory digest for n8n email node."""
        from backend.models.impact_record import ImpactRecord
        doc_count = Document.query.count()
        impact_count = ImpactRecord.query.count()
        high_impacts = ImpactRecord.query.filter_by(severity="HIGH").count()
        critical_impacts = ImpactRecord.query.filter_by(severity="CRITICAL").count()

        recent_docs = Document.query.order_by(Document.created_at.desc()).limit(5).all()
        doc_titles = [d.title or d.number or d.id for d in recent_docs]

        digest_text = (
            f"SYNTHÈSE RÉGLEMENTAIRE KUSOR v3 — BCT & CONFORMITÉ\n\n"
            f"Statistiques globales:\n"
            f"- Total circulaires indexées: {doc_count}\n"
            f"- Total enregistrements d'impact: {impact_count}\n"
            f"- Impacts Critiques: {critical_impacts}\n"
            f"- Impacts Élevés: {high_impacts}\n\n"
            f"Dernières circulaires ingérées: {', '.join(doc_titles) if doc_titles else 'Aucune récente'}\n"
        )

        return {
            "digest_text": digest_text,
            "documents_count": doc_count,
            "critical_impacts": critical_impacts,
            "high_impacts": high_impacts,
        }, 200

