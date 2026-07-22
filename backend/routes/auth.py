# backend/routes/auth.py
"""
Authentication endpoints: login, register, me.
"""

from flask import request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_restx import Namespace, Resource

from backend.extensions import db
from backend.models.user import User

ns = Namespace("auth", description="Authentication operations")


@ns.route("/login")
class Login(Resource):
    def post(self):
        """Authenticate user and receive JWT access token."""
        data = request.get_json() or {}
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return {"error": "Nom d'utilisateur et mot de passe requis"}, 400

        user = User.query.filter((User.username == username) | (User.email == username)).first()
        if not user or not user.check_password(password):
            return {"error": "Identifiants invalides"}, 401

        if not user.is_active:
            return {"error": "Compte désactivé"}, 403

        token = create_access_token(identity=user.id)
        return {
            "access_token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "full_name": user.full_name,
                "department": user.department,
            },
        }, 200


@ns.route("/register")
class Register(Resource):
    def post(self):
        """Register a new user (default role: user)."""
        data = request.get_json() or {}
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        role = data.get("role", "user")

        if not username or not email or not password:
            return {"error": "Nom d'utilisateur, email et mot de passe requis"}, 400

        if User.query.filter_by(username=username).first():
            return {"error": "Ce nom d'utilisateur existe déjà"}, 400

        if User.query.filter_by(email=email).first():
            return {"error": "Cet email existe déjà"}, 400

        user = User(
            username=username,
            email=email,
            role=role if role in User.VALID_ROLES else "user",
            full_name=data.get("full_name", ""),
            department=data.get("department", ""),
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        token = create_access_token(identity=user.id)
        return {
            "message": "Utilisateur créé avec succès",
            "access_token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
            },
        }, 201


@ns.route("/me")
class Me(Resource):
    @jwt_required()
    def get(self):
        """Get current authenticated user info."""
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return {"error": "Utilisateur introuvable"}, 404

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name,
            "department": user.department,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }, 200
