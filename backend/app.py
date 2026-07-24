import os
from flask import Flask, Blueprint
from flask_cors import CORS
from backend.config import config_map
from backend.extensions import db, jwt, migrate
from backend.middleware.error_handlers import register_error_handlers
from backend.models.user import User

# Route imports
from backend.routes.auth import api as auth_ns
from backend.routes.documents import api as documents_ns
from backend.routes.search import api as search_ns
from backend.routes.chat import api as chat_ns
from backend.routes.admin import api as admin_ns
from backend.routes.graph import api as graph_ns

def create_app(config_name: str = None) -> Flask:
    """
    Flask application factory.
    
    1. Create Flask app
    2. Load config
    3. Initialize extensions (db, jwt, CORS)
    4. Register Flask-RESTX API with all namespaces
    5. Initialize services (Neo4jManager, HybridRetriever, KusorAgent, etc.)
    6. Start collector scheduler (if not testing)
    7. Return app
    """
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")
        
    app = Flask(__name__)
    app.config.from_object(config_map[config_name])
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    
    # Configure CORS for Angular dev server
    CORS(app, resources={r"/api/*": {
        "origins": ["http://localhost:4200", "http://localhost:5000", "http://127.0.0.1:4200"],
        "supports_credentials": True
    }})
    
    # JWT callbacks
    @jwt.user_identity_loader
    def user_identity_lookup(user_id):
        return user_id

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return User.query.filter_by(id=identity).one_or_none()
        
    # Initialize Flask-RESTX
    authorizations = {
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'Enter JWT token in the format "Bearer <your_token>"'
        }
    }
    
    api_bp = Blueprint("api", __name__, url_prefix="/api")
    
    from flask_restx import Api
    api = Api(
        api_bp,
        title="KUSOR API",
        version="1.0",
        description="KUSOR Regulatory Intelligence Assistant API",
        doc="/docs",
        authorizations=authorizations,
        security="Bearer"
    )
    
    # Register namespaces
    api.add_namespace(auth_ns)
    api.add_namespace(documents_ns)
    api.add_namespace(search_ns)
    api.add_namespace(chat_ns)
    api.add_namespace(admin_ns)
    api.add_namespace(graph_ns)
    
    app.register_blueprint(api_bp)
    
    # Register global HTTP error handlers
    register_error_handlers(app)
    
    # Initialize services
    with app.app_context():
        # Lazy imports to avoid circular dependency
        from backend.graph.neo4j_manager import Neo4jManager
        from backend.processing.document_processor import DocumentProcessor
        from backend.graph.graph_builder import GraphBuilder
        from backend.retrieval.vector_searcher import VectorSearcher
        from backend.retrieval.bm25_searcher import BM25Searcher
        from backend.retrieval.graph_searcher import GraphSearcher
        from backend.retrieval.reranker import CrossEncoderReranker
        from backend.retrieval.hybrid_retriever import HybridRetriever
        from backend.agent.agent_graph import KusorAgent
        from backend.collector.bct_scraper import BCTScraper
        from backend.collector.scheduler import CollectorScheduler
        
        # Instantiate core managers
        app.neo4j_manager = Neo4jManager(
            uri=app.config["NEO4J_URI"],
            user=app.config["NEO4J_USER"],
            password=app.config["NEO4J_PASSWORD"]
        )
        
        app.document_processor = DocumentProcessor(
            chroma_host=app.config["CHROMA_HOST"],
            chroma_port=app.config["CHROMA_PORT"],
            ollama_base_url=app.config["OLLAMA_BASE_URL"],
            embedding_model=app.config["EMBEDDING_MODEL"]
        )
        
        app.graph_builder = GraphBuilder(
            neo4j_manager=app.neo4j_manager,
            ollama_base_url=app.config["OLLAMA_BASE_URL"],
            llm_model=app.config["LLM_MODEL"]
        )
        
        # Instantiate retrievers
        vector_searcher = VectorSearcher(
            chroma_host=app.config["CHROMA_HOST"],
            chroma_port=app.config["CHROMA_PORT"],
            ollama_base_url=app.config["OLLAMA_BASE_URL"],
            embedding_model=app.config["EMBEDDING_MODEL"]
        )
        
        bm25_searcher = BM25Searcher()
        
        graph_searcher = GraphSearcher(
            neo4j_manager=app.neo4j_manager,
            chroma_host=app.config["CHROMA_HOST"],
            chroma_port=app.config["CHROMA_PORT"]
        )
        
        reranker = CrossEncoderReranker()
        
        app.hybrid_retriever = HybridRetriever(
            vector_searcher=vector_searcher,
            bm25_searcher=bm25_searcher,
            graph_searcher=graph_searcher,
            reranker=reranker
        )
        
        # Instantiate agent graph
        app.kusor_agent = KusorAgent(
            hybrid_retriever=app.hybrid_retriever,
            neo4j_manager=app.neo4j_manager,
            ollama_base_url=app.config["OLLAMA_BASE_URL"],
            llm_model=app.config["LLM_MODEL"]
        )
        
        # Instantiate collector scraper
        app.bct_scraper = BCTScraper(
            db_session=db.session,
            document_processor=app.document_processor,
            graph_builder=app.graph_builder
        )
        
        # Start scraper scheduler in the background (unless in testing mode)
        if not app.config.get("TESTING"):
            app.scheduler = CollectorScheduler(scraper=app.bct_scraper)
            app.scheduler.start()
            
    return app
