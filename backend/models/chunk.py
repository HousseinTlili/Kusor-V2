from backend.extensions import db

class Chunk(db.Model):
    __tablename__ = "chunks"

    id = db.Column(db.String(100), primary_key=True)
    document_id = db.Column(db.String(36), db.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = db.Column(db.Integer, nullable=False)
    page_number = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    embedding_id = db.Column(db.String(255), nullable=True)
