# backend/models/conversation.py
"""
Conversation models — sessions and messages for the chat interface.
COPY from v2.
"""

import uuid
from datetime import datetime, timezone

from backend.extensions import db


class ConversationSession(db.Model):
    """A chat session belonging to a user."""

    __tablename__ = "conversation_sessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = db.Column(db.String(255), default="Nouvelle conversation")

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    messages = db.relationship(
        "ConversationMessage",
        backref="session",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )


class ConversationMessage(db.Model):
    """A single message in a conversation session."""

    __tablename__ = "conversation_messages"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(
        db.String(36),
        db.ForeignKey("conversation_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    role = db.Column(db.String(20), nullable=False, comment="user | assistant")
    content = db.Column(db.Text, nullable=False)
    sources_json = db.Column(db.Text, nullable=True, comment="JSON-serialized sources")
    confidence = db.Column(db.Float, nullable=True)
    metadata_json = db.Column(db.JSON, default=dict)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
