# backend/models/__init__.py
"""Re-export all SQLAlchemy models so Alembic can discover them."""

from backend.models.user import User
from backend.models.document import Document
from backend.models.chunk import Chunk
from backend.models.conversation import ConversationSession, ConversationMessage
from backend.models.audit_log import AuditLog
from backend.models.impact_record import ImpactRecord

__all__ = [
    "User",
    "Document",
    "Chunk",
    "ConversationSession",
    "ConversationMessage",
    "AuditLog",
    "ImpactRecord",
]
