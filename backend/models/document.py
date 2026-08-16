# backend/models/document.py
"""
Document model — represents an ingested regulatory document.
COPY from v2 with minor additions for v3.
"""

import uuid
from datetime import datetime, timezone

from backend.extensions import db


class Document(db.Model):
    """A regulatory document (circular, note, contract, etc.)."""

    __tablename__ = "documents"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.Text, nullable=False)
    filename = db.Column(db.String(255))
    doc_type = db.Column(
        db.String(50),
        default="circular",
        comment="circular | note | contract | kyc_dossier | credit_dossier",
    )
    number = db.Column(
        db.String(50),
        unique=True,
        nullable=True,
        comment="Circular number from BCT (e.g., 2024-01). Null for non-circulars.",
    )
    circular_reference = db.Column(
        db.String(100),
        nullable=True,
        comment="Alias for number — kept for v2 compatibility",
    )
    date_issued = db.Column(db.Date, nullable=True)
    category = db.Column(db.String(100), nullable=True)
    source = db.Column(db.String(100), default="BCT Portal", comment="BCT Portal | OFAC | EU Commission | UN Security Council | GAFI / FATF")
    source_url = db.Column(db.String(500))

    content_hash = db.Column(db.String(64), comment="SHA-256 for deduplication")
    status = db.Column(
        db.String(50),
        default="ACTIVE",
        comment="ACTIVE | MODIFIED | ABROGATED",
    )
    indexation_state = db.Column(
        db.String(50),
        default="PENDING",
        comment="PENDING | PROCESSING | INDEXED | FAILED",
    )
    language = db.Column(db.String(10), default="fr", comment="fr | ar | fr-ar")
    raw_text = db.Column(db.Text, comment="Full extracted text for reprocessing")

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ────────────────────────────────────────────
    chunks = db.relationship(
        "Chunk", backref="document", lazy="dynamic", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Document {self.number or self.id[:8]}>"
