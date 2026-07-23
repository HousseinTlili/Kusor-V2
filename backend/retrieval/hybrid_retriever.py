from retrieval.vector_searcher import VectorSearcher
from retrieval.bm25_searcher import BM25Searcher
from retrieval.graph_searcher import GraphSearcher


class HybridRetriever:
    """
    Module 5 — Orchestre les 3 stratégies de recherche et fusionne
    leurs résultats avec Reciprocal Rank Fusion (RRF).
    """

    def __init__(self, k: int = 60):
        self.vector_searcher = VectorSearcher()
        self.bm25_searcher = BM25Searcher()
        self.graph_searcher = GraphSearcher()
        self.k = k  # constante de lissage standard pour RRF

    def _chunk_key(self, result: dict) -> str:
        """
        Identifiant unique d'un chunk, utilisé pour savoir si le MÊME chunk
        apparaît dans plusieurs listes de résultats.
        """
        return f"{result.get('document_id')}_{result.get('chunk_index')}"

    def retrieve(self, question: str, top_k: int = 5) -> list[dict]:
        # Étape 1 : lancer les 3 recherches indépendamment.
        vector_results = self.vector_searcher.search(question, top_k=10)
        bm25_results = self.bm25_searcher.search(question, top_k=10)
        graph_results = self.graph_searcher.search(question)  # peut être vide

        # Étape 2 : calculer le score RRF pour chaque chunk.
        # rrf_scores associe chunk_key -> score cumulé
        rrf_scores = {}
        chunk_data = {}  # garde le texte complet de chaque chunk pour l'affichage final

        for rank, result in enumerate(vector_results, start=1):
            key = self._chunk_key(result)
            rrf_scores[key] = rrf_scores.get(key, 0) + 1 / (self.k + rank)
            chunk_data[key] = result

        for rank, result in enumerate(bm25_results, start=1):
            key = self._chunk_key(result)
            rrf_scores[key] = rrf_scores.get(key, 0) + 1 / (self.k + rank)
            chunk_data[key] = result

        # Note : GraphSearcher ne retourne pas des chunks mais des circulaires liées.
        # On les traite différemment : on les ajoute comme contexte supplémentaire,
        # avec un score fixe qui les fait apparaître mais sans dominer le classement.
        for rank, result in enumerate(graph_results, start=1):
            key = f"graph_{result['related_circular']}"
            rrf_scores[key] = rrf_scores.get(key, 0) + 1 / (self.k + rank)
            chunk_data[key] = {
                "text": f"[Relation graphe] Circulaire liée : {result['related_circular']}",
                "source": "graph",
                "related_circular": result["related_circular"],
            }

        # Étape 3 : trier tous les chunks par score RRF décroissant.
        sorted_keys = sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)

        # Étape 4 : construire la liste finale avec le score RRF inclus.
        final_results = []
        for key in sorted_keys[:top_k]:
            item = chunk_data[key]
            item["rrf_score"] = rrf_scores[key]
            final_results.append(item)

        return final_results

    def close(self):
        self.graph_searcher.close()


if __name__ == "__main__":
    retriever = HybridRetriever()

    question = "quelles sont les règles sur les créances non performantes de la circulaire 2022-01"
    results = retriever.retrieve(question, top_k=5)

    print(f"🔍 Question : {question}\n")
    print(f"📊 {len(results)} résultats fusionnés (RRF)\n")

    for i, r in enumerate(results, 1):
        print(f"--- Résultat {i} (score RRF={r['rrf_score']:.4f}) ---")
        print(r["text"][:200])
        print()

    retriever.close()