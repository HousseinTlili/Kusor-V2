# backend/app.py
"""
Flask Application Factory for KUSOR v3.
"""

from flask import Flask
from flask_restx import Api

from backend.config import Config
from backend.extensions import db, jwt, cors, migrate


def create_app(config_class=Config):
    """Factory creating and configuring the Flask app instance."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)
    migrate.init_app(app, db)

    # Import models to ensure they are registered with SQLAlchemy/Alembic
    import backend.models  # noqa: F401

    # Initialize Flask-RESTX OpenAPI documentation API
    api = Api(
        app,
        version="3.0",
        title="KUSOR v3 API",
        description="AI Compliance & Regulatory Intelligence Platform for Attijari Bank Tunisia",
        doc="/api/docs",
        prefix="/api",
    )

    # Register all 10 Namespaces
    from backend.routes.auth import ns as auth_ns
    from backend.routes.documents import ns as documents_ns
    from backend.routes.search import ns as search_ns
    from backend.routes.chat import ns as chat_ns
    from backend.routes.graph import ns as graph_ns
    from backend.routes.kyc import ns as kyc_ns
    from backend.routes.contract import ns as contract_ns
    from backend.routes.credit import ns as credit_ns
    from backend.routes.impact import ns as impact_ns
    from backend.routes.admin import ns as admin_ns

    api.add_namespace(auth_ns, path="/auth")
    api.add_namespace(documents_ns, path="/documents")
    api.add_namespace(search_ns, path="/search")
    api.add_namespace(chat_ns, path="/chat")
    api.add_namespace(graph_ns, path="/graph")
    api.add_namespace(kyc_ns, path="/kyc")
    api.add_namespace(contract_ns, path="/contract")
    api.add_namespace(credit_ns, path="/credit")
    api.add_namespace(impact_ns, path="/impact")
    api.add_namespace(admin_ns, path="/admin")

    @app.route("/health")
    def health_check():
        return {"status": "healthy", "service": "KUSOR v3 API"}, 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000)
