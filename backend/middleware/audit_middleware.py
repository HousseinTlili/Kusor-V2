# backend/middleware/audit_middleware.py
"""
Audit Logging Middleware — automatically records every API request into PostgreSQL audit_logs.
Captures user_id, action, endpoint, client IP, request body SHA-256 hash, and response summary.
"""

from __future__ import annotations

import hashlib
import logging
from functools import wraps
from typing import Callable

from flask import request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from backend.extensions import db
from backend.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


def audit_action(action: str, entity_type: str = "general"):
    """
    Decorator to log an API endpoint invocation to PostgreSQL audit_logs.
    """
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user_id = None
            try:
                verify_jwt_in_request(optional=True)
                user_id = get_jwt_identity()
            except Exception:
                pass

            input_body = request.get_data() or b""
            input_hash = hashlib.sha256(input_body).hexdigest() if input_body else None

            response = fn(*args, **kwargs)

            output_summary = ""
            if isinstance(response, tuple):
                res_data = response[0]
            else:
                res_data = response

            if isinstance(res_data, dict):
                output_summary = str(res_data)[:500]

            try:
                log = AuditLog(
                    user_id=user_id,
                    action=action,
                    entity_type=entity_type,
                    entity_id=str(kwargs.get("id") or kwargs.get("circular_id") or ""),
                    endpoint=f"{request.method} {request.path}",
                    ip_address=request.remote_addr,
                    input_hash=input_hash,
                    output_summary=output_summary,
                )
                db.session.add(log)
                db.session.commit()
            except Exception as e:
                logger.error("Audit log recording failed: %s", e)
                db.session.rollback()

            return response

        return wrapper

    return decorator
