from neo4j import GraphDatabase
from config import Config

_settings = Config()


class Neo4jManager:
    """Gère la connexion et les opérations Cypher sur Neo4j."""
    def __init__(self, uri=None, user="neo4j", password=None):
        uri = uri or _settings.NEO4J_URI
        password = password or getattr(_settings, "NEO4J_PASSWORD", "kusor_password")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_circular_node(self, number: str, title: str = "", date: str = "", category: str = "", status: str = "active"):
        """Crée (ou met à jour) un nœud Circular."""
        query = """
        MERGE (c:Circular {number: $number})
        SET c.title = $title,
            c.date = $date,
            c.category = $category,
            c.status = $status
        RETURN c
        """
        with self.driver.session() as session:
            session.run(query, number=number, title=title, date=date, category=category, status=status)

    def create_reference_relationship(self, from_number: str, to_number: str, relation_type: str = "REFERENCES"):
        """
        Crée une relation entre deux circulaires (ex: REFERENCES, MODIFIES, ABROGATES).
        Crée aussi le nœud cible s'il n'existe pas encore.
        """
        query = f"""
        MERGE (c1:Circular {{number: $from_number}})
        MERGE (c2:Circular {{number: $to_number}})
        MERGE (c1)-[:{relation_type}]->(c2)
        """
        with self.driver.session() as session:
            session.run(query, from_number=from_number, to_number=to_number)

    def get_circular_relations(self, number: str):
        """Retourne toutes les relations sortantes d'une circulaire donnée."""
        query = """
        MATCH (c:Circular {number: $number})-[r]->(other:Circular)
        RETURN type(r) as relation, other.number as target
        """
        with self.driver.session() as session:
            result = session.run(query, number=number)
            return [{"relation": r["relation"], "target": r["target"]} for r in result]


if __name__ == "__main__":
    manager = Neo4jManager()

    manager.create_circular_node(
        number="2022-01",
        title="Prévention et résolution des créances non performantes",
        date="2022-03-01",
        category="Risque de crédit"
    )
    print("✅ Nœud Circular 2022-01 créé")

    manager.create_reference_relationship("2022-01", "2021-05", "REFERENCES")
    print("✅ Relation REFERENCES créée : 2022-01 -> 2021-05")

    relations = manager.get_circular_relations("2022-01")
    print(f"\n📊 Relations de 2022-01 : {relations}")

    manager.close()
    