import re
from neo4j import GraphDatabase
from config import Config

_settings = Config()


class GraphSearcher:
    """
    Module 5 — Recherche relationnelle via Neo4j.
    Détecte les numéros de circulaires mentionnés dans une question,
    puis traverse le graphe pour trouver les circulaires liées.
    """
    def __init__(self, uri=None, user="neo4j", password=None):
        uri = uri or _settings.NEO4J_URI
        password = password or getattr(_settings, "NEO4J_PASSWORD", "kusor_password")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def _extract_circular_numbers(self, question: str) -> list[str]:
        """
        Détecte les numéros de circulaires dans la question posée par l'utilisateur.
        Réutilise la même logique de pattern que Module 3 (extract_circular_references),
        mais appliquée ici à une question au lieu d'un document.
        """
        pattern = r"\b(\d{4}-\d{2})\b"
        matches = re.findall(pattern, question)
        return list(set(matches))

    def search(self, question: str, max_hops: int = 2, top_k: int = 20) -> list[dict]:
        """
        Retourne les circulaires liées aux numéros détectés dans la question,
        en suivant les relations du graphe jusqu'à max_hops sauts de distance.
        """
        circular_numbers = self._extract_circular_numbers(question)

        if not circular_numbers:
            # Aucune référence explicite détectée dans la question :
            # cette méthode de recherche n'a rien à apporter ici.
            return []

        results = []

        with self.driver.session() as session:
            for number in circular_numbers:
                # Cypher : on part du nœud correspondant au numéro détecté,
                # et on suit TOUTES les relations sortantes ET entrantes
                # jusqu'à max_hops sauts, dans n'importe quelle direction.
                query = f"""
                MATCH (start:Circular {{number: $number}})-[r*1..{max_hops}]-(related:Circular)
                RETURN DISTINCT related.number AS number,
                       related.title AS title,
                       related.category AS category
                """
                result = session.run(query, number=number)

                for record in result:
                    results.append({
                        "source_query": number,
                        "related_circular": record["number"],
                        "title": record["title"],
                        "category": record["category"],
                    })

        return results


if __name__ == "__main__":
    searcher = GraphSearcher()

    question = "Est-ce que la circulaire 2022-01 a été modifiée ou référencée ailleurs ?"
    results = searcher.search(question)

    print(f"🔍 Question : {question}\n")
    print(f"📊 {len(results)} relations trouvées\n")

    for r in results:
        print(f"--- {r['source_query']} → {r['related_circular']} ---")
        print(f"Titre : {r['title']}")
        print(f"Catégorie : {r['category']}")
        print()

    searcher.close()