"""JWT authentication middleware and helpers."""
from functools import wraps
import uuid
import json
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity
from flask_restx import abort
from backend.extensions import db
from backend.models.audit_log import AuditLog

def admin_required(fn):
    """Decorator: requires JWT token with role='admin'."""
    @wraps(fn)
    def decorator(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get("role") != "admin":
            abort(403, "Admin privileges required")
        return fn(*args, **kwargs)
    return decorator

def role_required(*allowed_roles: str):
    """
    Decorator enforcing that the authenticated user possesses one of the allowed roles.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get("role", "user")
            
            if user_role != "admin" and user_role not in allowed_roles:
                abort(403, f"Access denied. Role '{user_role}' not authorized.")

            return fn(*args, **kwargs)
        return wrapper
    return decorator

def audit_action(action: str, entity_type: str):
    """Decorator: logs the action to AuditLog after execution."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Execute route handler first
            result = fn(*args, **kwargs)
            
            # Extract response details for auditing
            entity_id = None
            details_dict = {}
            
            # Handle different flask-restx response formats (dict, tuple, Response, etc.)
            response_data = None
            if isinstance(result, tuple) and len(result) > 0:
                response_data = result[0]
            else:
                response_data = result

            if isinstance(response_data, dict):
                entity_id = response_data.get("id") or response_data.get("document_id") or response_data.get("session_id")
                details_dict = response_data.copy()
                # Remove sensitive information if present
                details_dict.pop("password", None)
                details_dict.pop("password_hash", None)
                details_dict.pop("access_token", None)
            
            # Optional extraction of kwargs (e.g. session_id or id from route param)
            if not entity_id:
                entity_id = kwargs.get("id") or kwargs.get("session_id") or kwargs.get("circular")
            
            # Get user ID from active JWT token, if any
            user_id = None
            try:
                verify_jwt_in_request(optional=True)
                user_id = get_jwt_identity()
            except Exception:
                pass
                
            try:
                log = AuditLog(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    action=action,
                    entity_type=entity_type,
                    entity_id=str(entity_id) if entity_id else None,
                    details_json=json.dumps(details_dict) if details_dict else None
                )
                db.session.add(log)
                db.session.commit()
            except Exception as e:
                # Never fail a request just because audit logging fails
                db.session.rollback()
                # Print to logs or stderr
                import sys
                print(f"Audit log failed: {e}", file=sys.stderr)

            return result
        return wrapper
    return decorator
