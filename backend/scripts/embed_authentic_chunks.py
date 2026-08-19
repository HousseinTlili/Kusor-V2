"""
Embeds all authentic BCT text chunks into ChromaDB collections (circulars & kusor_documents).
Uses sentence-transformers / BAAI/bge-m3 / multilingual embeddings.
"""
import os
import sys
import chromadb

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app import create_app
from backend.models.document import Document
from backend.models.chunk import Chunk
from backend.rag.embeddings import EmbeddingService

def embed_all_authentic_chunks():
    app = create_app("development")
    with app.app_context():
        embedder = EmbeddingService()
        chroma_client = chromadb.PersistentClient(path="chroma_db")
        
        col_circulars = chroma_client.get_or_create_collection(
            name="circulars",
            metadata={"hnsw:space": "cosine"}
        )
        col_kusor = chroma_client.get_or_create_collection(
            name="kusor_documents",
            metadata={"hnsw:space": "cosine"}
        )

        all_chunks = Chunk.query.join(Document).all()
        print(f"Embedding {len(all_chunks)} authentic chunks into ChromaDB...")

        batch_size = 64
        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i:i+batch_size]
            texts = [c.content for c in batch]
            ids = [f"chk_{c.id}" for c in batch]
            metadatas = [
                {
                    "chunk_id": str(c.id),
                    "document_id": str(c.document_id),
                    "circular_number": str(c.document.number) if c.document else "BCT",
                    "title": str(c.document.title) if c.document else "",
                    "category": str(c.document.category) if c.document else "",
                    "page_number": int(c.page_number) if c.page_number else 1
                }
                for c in batch
            ]
            
            embeddings = embedder.embed_documents(texts)
            
            col_circulars.upsert(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
            col_kusor.upsert(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
            print(f"Embedded {min(i+batch_size, len(all_chunks))}/{len(all_chunks)} chunks...")

        print("✅ Finished embedding all authentic BCT chunks into ChromaDB collections!")

if __name__ == "__main__":
    embed_all_authentic_chunks()
