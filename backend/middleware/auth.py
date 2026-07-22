# backend/middleware/auth.py
"""
Role-based access control (RBAC) middleware for KUSOR v3.
Supports 5 roles: admin, compliance, legal, credit, user.
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from backend.models.user import User


def role_required(*allowed_roles: str):
    """
    Decorator enforcing that the authenticated user possesses one of the allowed roles.
    Usage:
        @jwt_required()
        @role_required("compliance", "admin")
        def my_route(): ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = User.query.get(user_id)

            if not user:
                return jsonify({"error": "Utilisateur introuvable"}), 404

            if not user.is_active:
                return jsonify({"error": "Compte utilisateur désactivé"}), 403

            if user.role != "admin" and user.role not in allowed_roles:
                return jsonify({
                    "error": f"Accès refusé. Rôle '{user.role}' non autorisé pour cette opération.",
                    "required_roles": list(allowed_roles),
                }), 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator
