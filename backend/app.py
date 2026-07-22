# backend/app.py
"""
Flask Application Factory for KUSOR v3.
"""

from flask import Flask
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

    @app.route("/health")
    def health_check():
        return {"status": "healthy", "service": "KUSOR v3 API"}, 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000)
