"""Flask extensions initialized here, imported in app factory."""
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()


def get_neo4j_manager():
    from flask import current_app
    return getattr(current_app, "neo4j_manager", None)

