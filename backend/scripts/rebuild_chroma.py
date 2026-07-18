import os
import sys
import requests

# Adjust Python path to allow importing from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import chromadb
from backend.app import create_app
from backend.extensions import db
from backend.models.document import Document
from backend.models.chunk import Chunk

def main():
    print("Initializing Flask App context...")
    app = create_app("development")
    
    with app.app_context():
        # Get configurations
        chroma_host = app.config.get("CHROMA_HOST", "localhost")
        chroma_port = app.config.get("CHROMA_PORT", 8001)
        ollama_url = app.config.get("OLLAMA_BASE_URL", "http://localhost:11434")
        embedding_model = app.config.get("EMBEDDING_MODEL", "nomic-embed-text")
        
        print(f"Connecting to ChromaDB at {chroma_host}:{chroma_port}...")
        client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
        
        # Recreate collection to start clean
        print("Recreating ChromaDB collection 'kusor_documents'...")
        try:
            client.delete_collection("kusor_documents")
        except Exception:
            pass
            
        collection = client.create_collection(
            name="kusor_documents",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Load all documents & chunks
        print("Fetching chunks from PostgreSQL...")
        documents = db.session.query(Document).all()
        doc_map = {d.id: d for d in documents}
        
        chunks = db.session.query(Chunk).order_by(Chunk.document_id, Chunk.chunk_index).all()
        total_chunks = len(chunks)
        print(f"Found {len(documents)} documents and {total_chunks} chunks. Generating embeddings...")
        
        # Prepare batch vectors
        ids = []
        texts = []
        metadatas = []
        
        batch_size = 128
        embed_url = f"{ollama_url}/api/embed"
        
        for idx, chunk in enumerate(chunks, start=1):
            doc = doc_map.get(chunk.document_id)
            if not doc:
                continue
                
            chunk_id = f"{chunk.document_id}_{chunk.chunk_index}"
            ids.append(chunk_id)
            texts.append(chunk.content)
            metadatas.append({
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number,
                "source_filename": f"{doc.number}.pdf",
                "circular_number": doc.number
            })
            
            # Embed and insert in batches of batch_size
            if len(texts) >= batch_size or idx == total_chunks:
                print(f"Embedding chunk batch {idx - len(texts) + 1} to {idx} / {total_chunks}...")
                try:
                    res = requests.post(
                        embed_url,
                        json={"model": embedding_model, "input": texts},
                        timeout=60
                    )
                    if res.status_code == 200:
                        embeddings = res.json().get("embeddings", [])
                        collection.add(
                            ids=ids,
                            embeddings=embeddings,
                            metadatas=metadatas,
                            documents=texts
                        )
                    else:
                        print(f"  Error: Ollama returned status code {res.status_code}: {res.text}")
                except Exception as e:
                    print(f"  Error inserting batch: {e}")
                
                # Clear batch lists
                ids = []
                texts = []
                metadatas = []
                
        print("ChromaDB rebuild complete!")

if __name__ == "__main__":
    main()
