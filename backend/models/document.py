from backend.extensions import db
from datetime import datetime

class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.String(36), primary_key=True)
    number = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    category = db.Column(db.String(100), nullable=True)
    url = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(50), default="ACTIVE")
    indexation_state = db.Column(db.String(50), default="PENDING")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    chunks = db.relationship("Chunk", backref="document", lazy="dynamic", cascade="all, delete-orphan")
