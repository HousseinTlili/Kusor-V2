import re
from rank_bm25 import BM25Okapi
import chromadb


class BM25Searcher:
    """
    Module 5 — Recherche par mots-clés (BM25).
    Contrairement à VectorSearcher, cette recherche ne comprend pas le "sens"
    mais trouve les correspondances exactes de termes (ex: numéros de circulaire,
    termes juridiques précis).
    """

    def __init__(self, chroma_host="localhost", chroma_port=8001, collection_name="circulars"):
        # On récupère tous les chunks déjà stockés dans ChromaDB (Module 3)
        # pour construire l'index BM25 à partir des mêmes données.
        client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
        collection = client.get_collection(name=collection_name)

        # get() sans argument récupère TOUT le contenu de la collection
        all_data = collection.get(include=["documents", "metadatas"])

        self.documents = all_data["documents"]
        self.metadatas = all_data["metadatas"]

        # Tokenisation simple : on découpe chaque texte en mots minuscules.
        # BM25 a besoin de listes de mots (tokens), pas de texte brut.
        tokenized_corpus = [self._tokenize(doc) for doc in self.documents]

        # Construction de l'index BM25 en mémoire.
        # C'est cette étape qui "apprend" la fréquence des mots dans le corpus.
        self.bm25 = BM25Okapi(tokenized_corpus)

    def _tokenize(self, text: str) -> list[str]:
        """Découpe un texte en mots simples (minuscules, sans ponctuation)."""
        text = text.lower()
        tokens = re.findall(r"\b\w+\b", text)
        return tokens

    def search(self, question: str, top_k: int = 5) -> list[dict]:
        """Retourne les top_k chunks les plus pertinents selon BM25."""
        tokenized_query = self._tokenize(question)

        # get_scores calcule un score de pertinence pour CHAQUE chunk du corpus
        # par rapport à la question.
        scores = self.bm25.get_scores(tokenized_query)

        # On trie les indices par score décroissant et on garde les top_k.
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for idx in top_indices:
            meta = self.metadatas[idx]
            results.append({
                "text": self.documents[idx],
                "document_id": meta.get("document_id"),
                "page_number": meta.get("page_number"),
                "chunk_index": meta.get("chunk_index"),
                "score": scores[idx],  # plus grand = plus pertinent (inverse de la distance !)
            })

        return results


if __name__ == "__main__":
    searcher = BM25Searcher()

    question = "créances non performantes prévention"
    results = searcher.search(question, top_k=3)

    print(f"🔍 Question : {question}\n")
    print(f"📊 {len(results)} résultats trouvés\n")

    for i, r in enumerate(results, 1):
        print(f"--- Résultat {i} (page {r['page_number']}, score={r['score']:.4f}) ---")
        print(r["text"][:200])
        print()
        