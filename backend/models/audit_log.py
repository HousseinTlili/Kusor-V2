# backend/models/audit_log.py
"""
AuditLog model — immutable audit trail for every significant action.
V3 changes: added input_hash, output_summary, ip_address, endpoint fields.
"""

import uuid
from datetime import datetime, timezone

from backend.extensions import db


class AuditLog(db.Model):
    """Immutable audit-trail entry."""

    __tablename__ = "audit_logs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action = db.Column(
        db.String(100),
        nullable=False,
        comment="e.g., DOCUMENT_UPLOADED, CHAT_MESSAGE_SENT, KYC_CHECK_RUN",
    )
    entity_type = db.Column(db.String(50), comment="document, chat, kyc, contract, credit")
    entity_id = db.Column(db.String(100))
    endpoint = db.Column(db.String(200), comment="HTTP method + path, e.g., POST /api/chat/message")
    ip_address = db.Column(db.String(45), comment="Client IP (IPv4 or IPv6)")
    input_hash = db.Column(
        db.String(64),
        nullable=True,
        comment="SHA-256 of the request body for tamper detection",
    )
    output_summary = db.Column(
        db.Text,
        nullable=True,
        comment="Truncated response summary (first 500 chars)",
    )
    details_json = db.Column(db.Text, nullable=True, comment="Full JSON details")

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
