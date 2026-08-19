from retrieval.hybrid_retriever import HybridRetriever
from retrieval.graph_searcher import GraphSearcher


class AgentTools:
    """
    Expose les capacités de recherche (Module 5) comme des "outils"
    utilisables par l'agent LangGraph (Module 6).
    """

    def __init__(self):
        self.hybrid_retriever = HybridRetriever()
        self.graph_searcher = GraphSearcher()

    def search_hybrid(self, question: str, top_k: int = 5) -> list[dict]:
        """
        Outil principal : recherche combinée Vector + BM25 + Graph avec fusion RRF.
        À utiliser pour les questions factuelles ou conceptuelles.
        """
        return self.hybrid_retriever.retrieve(question, top_k=top_k)

    def get_circular_relations(self, circular_number: str) -> list[dict]:
        """
        Outil ciblé : récupère uniquement les relations d'une circulaire précise.
        À utiliser pour les questions purement relationnelles
        (ex: "cette circulaire a-t-elle été modifiée ?").
        """
        fake_question = f"circulaire {circular_number}"
        return self.graph_searcher.search(fake_question)

    def close(self):
        self.graph_searcher.close()


if __name__ == "__main__":
    tools = AgentTools()

    print("🔧 Test 1 — search_hybrid\n")
    results = tools.search_hybrid("quelles sont les règles sur les créances non performantes", top_k=3)
    print(f"{len(results)} résultats trouvés")
    for r in results[:2]:
        print(f"  - {r['text'][:100]}...")

    print("\n🔧 Test 2 — get_circular_relations\n")
    relations = tools.get_circular_relations("2022-01")
    print(f"{len(relations)} relations trouvées")
    for rel in relations:
        print(f"  - {rel}")

    tools.close()