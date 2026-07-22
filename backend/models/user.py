# backend/models/user.py
"""
User model — authentication and role-based access control.

V3 changes from v2:
- role expanded from {admin, user} to {admin, compliance, legal, credit, user}
- Added department field for organizational context
"""

import uuid
from datetime import datetime, timezone

import bcrypt

from backend.extensions import db


class User(db.Model):
    """Application user with role-based access."""

    __tablename__ = "users"

    # ── Columns ──────────────────────────────────────────────────
    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(200), default="")
    role = db.Column(
        db.String(20),
        nullable=False,
        default="user",
        comment="One of: admin, compliance, legal, credit, user",
    )
    department = db.Column(
        db.String(100),
        nullable=True,
        comment="Organizational department (e.g., Direction Conformité)",
    )
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ────────────────────────────────────────────
    sessions = db.relationship(
        "ConversationSession", backref="user", lazy="dynamic"
    )
    audit_logs = db.relationship("AuditLog", backref="user", lazy="dynamic")

    # ── Valid roles ──────────────────────────────────────────────
    VALID_ROLES = {"admin", "compliance", "legal", "credit", "user"}

    # ── Methods ──────────────────────────────────────────────────
    def set_password(self, password: str) -> None:
        """Hash and store the password using bcrypt."""
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, password: str) -> bool:
        """Verify a plaintext password against the stored hash."""
        pw_hash = self.password_hash
        if not isinstance(pw_hash, bytes):
            pw_hash = pw_hash.encode("utf-8")
        return bcrypt.checkpw(password.encode("utf-8"), pw_hash)

    def has_role(self, *roles: str) -> bool:
        """Check if user has any of the specified roles."""
        return self.role in roles

    def __repr__(self) -> str:
        return f"<User {self.username} role={self.role}>"
