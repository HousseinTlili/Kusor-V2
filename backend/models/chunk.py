# backend/models/chunk.py
"""
Chunk model — a segment of a document stored for retrieval.
COPY from v2.
"""

import uuid
from datetime import datetime, timezone

from backend.extensions import db


class Chunk(db.Model):
    """One chunk (segment) of a document."""

    __tablename__ = "chunks"

    id = db.Column(db.String(100), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = db.Column(
        db.String(36),
        db.ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    content = db.Column(db.Text, nullable=False)
    section_title = db.Column(db.String(300))
    chunk_index = db.Column(db.Integer, nullable=False, default=0)
    page_number = db.Column(db.Integer, nullable=True, default=1)
    token_count = db.Column(db.Integer)
    embedding_id = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<Chunk {self.id[:12]} doc={self.document_id[:8]}>"
