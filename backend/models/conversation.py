from backend.extensions import db
from datetime import datetime

class ConversationSession(db.Model):
    __tablename__ = "conversation_sessions"

    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    messages = db.relationship("ConversationMessage", backref="session", lazy="dynamic", cascade="all, delete-orphan")

class ConversationMessage(db.Model):
    __tablename__ = "conversation_messages"

    id = db.Column(db.String(36), primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey("conversation_sessions.id", ondelete="CASCADE"), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sources_json = db.Column(db.Text, nullable=True)
    confidence = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
