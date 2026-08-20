"""
KUSOR — Unified Enterprise Server (Single Port: 5000)
Serves the Angular 21 Single Page Application (SPA), the Neo4j Graph visualizer,
the Flask-RESTX OpenAPI / Swagger documentation, and developer test tools.
"""
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from flask import Flask, request, jsonify, send_from_directory, abort
from flask_cors import CORS
from flask_restx import Api

from backend.config import config_map, Config
from backend.extensions import db, jwt, migrate
from backend.middleware.error_handlers import register_error_handlers

from backend.graph.neo4j_manager import Neo4jManager
from backend.graph.graph_builder import GraphBuilder
from backend.agent.agent_graph import build_agent_graph, KusorAgent
from backend.agent.schemas import AgentState

ANGULAR_DIST = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "frontend", "kusor-ui", "dist", "kusor-ui", "browser")
)
STATIC_PROTOTYPES = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))


def create_app(config_name: str = "development") -> Flask:
    """Flask unified application factory."""
    app = Flask(__name__, static_folder=None)
    
    # Load configuration
    cfg_class = config_map.get(config_name, Config)
    app.config.from_object(cfg_class)
    
    # Initialize extensions
    CORS(app, resources={r"/*": {"origins": "*"}})
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    register_error_handlers(app)

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        return jsonify({
            "code": 401,
            "name": "Unauthorized",
            "message": "Token de session invalide ou corrompu",
            "error": str(reason)
        }), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            "code": 401,
            "name": "Unauthorized",
            "message": "Session expirée. Veuillez vous reconnecter.",
            "error": "token_expired"
        }), 401

    @jwt.unauthorized_loader
    def missing_token_callback(reason):
        return jsonify({
            "code": 401,
            "name": "Unauthorized",
            "message": "Autorisation requise pour cette action",
            "error": str(reason)
        }), 401
    
    # Initialize Neo4j and GraphBuilder services
    try:
        app.neo4j_manager = Neo4jManager(
            uri=app.config.get("NEO4J_URI", "bolt://localhost:7687"),
            user=app.config.get("NEO4J_USER", "neo4j"),
            password=app.config.get("NEO4J_PASSWORD", "kusor_password")
        )
        app.graph_builder = GraphBuilder(
            neo4j_manager=app.neo4j_manager,
            ollama_base_url=app.config.get("OLLAMA_BASE_URL", "http://localhost:11434"),
            llm_model=app.config.get("LLM_MODEL", "qwen2.5:7b")
        )
    except Exception as e:
        app.logger.warning(f"Neo4j initialization warning: {e}")
        app.neo4j_manager = None
        app.graph_builder = None

    # Initialize Document Processor & BCT Scraper
    try:
        from backend.processing.document_processor import DocumentProcessor
        from backend.collector.bct_scraper import BCTScraper
        app.document_processor = DocumentProcessor(
            chroma_host=app.config.get("CHROMA_HOST", "localhost"),
            chroma_port=app.config.get("CHROMA_PORT", 8001),
            ollama_base_url=app.config.get("OLLAMA_BASE_URL", "http://localhost:11434")
        )
        app.bct_scraper = BCTScraper(
            db_session=db.session,
            document_processor=app.document_processor,
            graph_builder=app.graph_builder,
            pdf_download_dir=app.config.get("CIRCULAR_DOWNLOAD_DIR", "data/circulars")
        )
    except Exception as e:
        app.logger.warning(f"Processor/Scraper initialization warning: {e}")
        app.document_processor = None
        app.bct_scraper = None

    # Initialize LangGraph Agent
    try:
        app.agent_executor = build_agent_graph()
        app.kusor_agent = KusorAgent(agent_graph=app.agent_executor)
    except Exception as e:
        app.logger.warning(f"Agent initialization warning: {e}")
        app.agent_executor = None
        app.kusor_agent = None

    # Initialize Flask-RESTX Api under /api
    api = Api(
        app,
        version="1.0",
        title="KUSOR Regulatory Intelligence API",
        description="API for BCT circular query, GraphRAG visualization, and compliance auditing.",
        doc="/api/docs",
        prefix="/api",
        authorizations={
            "Bearer": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": "JWT Authorization header using the Bearer scheme. Example: 'Bearer {token}'"
            }
        }
    )

    # Register REST API Namespaces
    from backend.routes.auth import api as auth_ns
    from backend.routes.documents import api as docs_ns
    from backend.routes.graph import api as graph_ns
    from backend.routes.search import api as search_ns
    from backend.routes.chat import api as chat_ns
    from backend.routes.admin import api as admin_ns
    from backend.routes.credit import api as credit_ns
    from backend.routes.contract import api as contract_ns
    from backend.routes.kyc import api as kyc_ns
    from backend.routes.impact import api as impact_ns
    from backend.routes.obligations import api as obligations_ns

    api.add_namespace(auth_ns, path="/auth")
    api.add_namespace(docs_ns, path="/documents")
    api.add_namespace(graph_ns, path="/graph")
    api.add_namespace(search_ns, path="/search")
    api.add_namespace(chat_ns, path="/chat")
    api.add_namespace(admin_ns, path="/admin")
    api.add_namespace(credit_ns, path="/credit")
    api.add_namespace(contract_ns, path="/contract")
    api.add_namespace(kyc_ns, path="/kyc")
    api.add_namespace(impact_ns, path="/impact")
    api.add_namespace(obligations_ns, path="/obligations")

    # ------------------------------------------------------------------
    # Specialized System, Swagger UI & Diagnostic Routes
    # ------------------------------------------------------------------
    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"}), 200

    @app.route("/docs")
    @app.route("/swagger")
    @app.route("/apidocs")
    @app.route("/swagger-ui")
    def swagger_ui():
        """Official interactive Swagger UI 5.x."""
        return send_from_directory(STATIC_PROTOTYPES, "swagger_ui.html")

    @app.route("/test")
    @app.route("/console")
    def test_console():
        """Developer RAG diagnostic console."""
        return send_from_directory(STATIC_PROTOTYPES, "kusor_console.html")

    # Direct agent endpoint for lightweight requests & test console
    @app.route("/api/agent/ask", methods=["POST"])
    def ask_agent():
        data = request.get_json(silent=True) or {}
        question = data.get("question", "").strip()

        if not question:
            return jsonify({"error": "Le champ 'question' est requis."}), 400

        if not app.agent_executor:
            return jsonify({"error": "Agent non initialisé"}), 500

        try:
            initial_state = AgentState(question=question)
            final_state = app.agent_executor.invoke(initial_state)
        except Exception as e:
            app.logger.exception("Erreur dans l'agent LangGraph")
            return jsonify({"error": "Erreur interne de l'agent.", "detail": str(e)}), 500

        result = final_state["final_response"]

        score = result.confidence_score
        if score >= 0.8:
            confidence_label = "Confiance haute"
        elif score >= 0.6:
            confidence_label = "Confiance moyenne"
        else:
            confidence_label = "Confiance faible"

        escalade = None
        if score < 0.5 or final_state["question_type"].value == "hors_perimetre":
            escalade = {"text": "Réponse à confiance faible — vérifie les sources ou contacte l'équipe Conformité."}

        return jsonify({
            "classification": final_state["question_type"].value,
            "confidence": confidence_label,
            "confidence_score": score,
            "answer": {
                "text": result.answer,
                "sources": [
                    f"{s.circular_number} — p.{s.page} — {s.title}" for s in result.sources
                ],
                "escalade": escalade,
            },
            "related_circulars": result.related_circulars,
            "graph_path_used": result.graph_path_used,
        })

    # ------------------------------------------------------------------
    # Unified Single-Port Angular SPA Frontend Serving (Port 5000)
    # ------------------------------------------------------------------
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_spa(path):
        # Never catch /api calls (leave them to Flask-RESTX)
        if path.startswith("api"):
            abort(404)

        # 1. Check if direct static asset exists in Angular build (JS, CSS, images)
        if os.path.exists(os.path.join(ANGULAR_DIST, path)) and path != "":
            return send_from_directory(ANGULAR_DIST, path)

        # 2. Check if Angular index.html is built and return it for SPA routing
        if os.path.exists(os.path.join(ANGULAR_DIST, "index.html")):
            return send_from_directory(ANGULAR_DIST, "index.html")

        # 3. Fallback to prototype chat if Angular has not been built
        return send_from_directory(STATIC_PROTOTYPES, "kusor_chat_final.html")

    return app


# Create default instance for WSGI / Flask CLI / python app.py
app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    print("=================================================================")
    print("🚀 KUSOR Unified Server running on http://localhost:5000")
    print("   • Application Web & Graphe Neo4j : http://localhost:5000")
    print("   • Documentation Swagger / OpenAPI : http://localhost:5000/api/docs")
    print("   • Console de Test & Diagnostic   : http://localhost:5000/test")
    print("=================================================================")
    app.run(debug=True, host="0.0.0.0", port=5000)