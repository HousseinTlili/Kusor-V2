import chromadb
import ollama
from config import Config

_settings = Config()


class VectorSearcher:
    """
    Module 5 — Recherche vectorielle (sémantique) via ChromaDB.
    Interroge la collection de chunks déjà indexée par le Module 3.
    """

    def __init__(self, chroma_host=None, chroma_port=None, collection_name="circulars", embedding_model="nomic-embed-text"):
        chroma_host = chroma_host or _settings.CHROMA_HOST
        chroma_port = chroma_port or int(_settings.CHROMA_PORT)
        self.client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
        self.collection = self.client.get_collection(name=collection_name)
        self.embedding_model = embedding_model

    def search(self, question: str, top_k: int = 5) -> list[dict]:
        """
        Retourne les top_k chunks les plus proches sémantiquement de la question.
        Chaque résultat contient: text, metadata, distance (score de dissimilarité).
        """
        # Étape 1 : convertir la question en vecteur avec le MÊME modèle
        # que celui utilisé pour indexer les chunks (nomic-embed-text).
        # C'est essentiel : comparer des vecteurs générés par des modèles
        # différents n'a aucun sens mathématique.
        response = ollama.embeddings(model=self.embedding_model, prompt=question)
        query_embedding = response["embedding"]

        # Étape 2 : ChromaDB calcule la distance entre ce vecteur
        # et tous les vecteurs déjà stockés, puis retourne les plus proches.
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        # Étape 3 : reformater le résultat brut de ChromaDB
        # en une liste simple et lisible.
        formatted = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            formatted.append({
                "text": doc,
                "document_id": meta.get("document_id"),
                "page_number": meta.get("page_number"),
                "chunk_index": meta.get("chunk_index"),
                "distance": dist,  # plus petit = plus pertinent
            })

        return formatted


if __name__ == "__main__":
    searcher = VectorSearcher()

    question = "quelles sont les règles sur les créances non performantes"
    results = searcher.search(question, top_k=3)

    print(f"🔍 Question : {question}\n")
    print(f"📊 {len(results)} résultats trouvés\n")

    for i, r in enumerate(results, 1):
        print(f"--- Résultat {i} (page {r['page_number']}, distance={r['distance']:.4f}) ---")
        print(r["text"][:200])
        print()