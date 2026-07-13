from typing import List, Optional
import chromadb
from langchain_ollama import OllamaEmbeddings
from backend.retrieval.schemas import RetrievedChunk

class VectorSearcher:
    """
    Searches ChromaDB via embedded question for semantically similar chunks.
    Uses nomic-embed-text (via Ollama) to embed the query.
    """

    def __init__(
        self,
        chroma_host: str = "localhost",
        chroma_port: int = 8001,
        collection_name: str = "kusor_documents",
        ollama_base_url: str = "http://localhost:11434",
        embedding_model: str = "nomic-embed-text",
    ) -> None:
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.collection_name = collection_name
        self.ollama_base_url = ollama_base_url
        self.embedding_model = embedding_model

    def search(
        self,
        query: str,
        top_k: int = 10,
        filter_circular: Optional[str] = None,
    ) -> List[RetrievedChunk]:
        """
        Embed query with nomic-embed-text, search ChromaDB with cosine similarity.
        Returns top-k chunks with scores.
        Optional: filter by circular_number.
        """
        client = chromadb.HttpClient(host=self.chroma_host, port=self.chroma_port)
        collection = client.get_collection(name=self.collection_name)
        
        embeddings_model = OllamaEmbeddings(
            base_url=self.ollama_base_url,
            model=self.embedding_model
        )
        query_embedding = embeddings_model.embed_query(query)
        
        where = {}
        if filter_circular:
            where["circular_number"] = filter_circular
            
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where if where else None
        )
        
        retrieved = []
        if not results or not results.get("ids") or len(results["ids"][0]) == 0:
            return retrieved
            
        ids = results["ids"][0]
        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        documents = results.get("documents", [[]])[0]
        
        for i in range(len(ids)):
            dist = distances[i] if i < len(distances) else 0.0
            score = max(0.0, min(1.0, 1.0 - dist))
            
            meta = metadatas[i] if i < len(metadatas) else {}
            content = documents[i] if i < len(documents) else ""
            
            retrieved.append(RetrievedChunk(
                content=content,
                document_id=meta.get("document_id", ""),
                chunk_index=int(meta.get("chunk_index", 0)),
                page_number=int(meta.get("page_number", 1)),
                source_filename=meta.get("source_filename", ""),
                circular_number=meta.get("circular_number"),
                score=score,
                retrieval_method="vector"
            ))
            
        return retrieved
