import sys
sys.path.append('.')

from processing.document_processor import DocumentProcessor
from graph.neo4j_manager import Neo4jManager


class GraphBuilder:
    """
    Orchestrateur : prend un document traité par DocumentProcessor
    et construit automatiquement les nœuds/relations dans Neo4j.
    """

    def __init__(self):
        self.processor = DocumentProcessor()
        self.graph = Neo4jManager()

    def process_and_build(self, pdf_path: str, circular_number: str, title: str = "", date: str = "", category: str = ""):
        # Étape 1 : extraction
        pages = self.processor.extract_text(pdf_path)
        all_text = " ".join(p["text"] for p in pages)

        # Étape 2 : créer le nœud principal
        self.graph.create_circular_node(
            number=circular_number,
            title=title,
            date=date,
            category=category
        )
        print(f"✅ Nœud créé pour la circulaire {circular_number}")

        # Étape 3 : détecter et créer les références
        refs = self.processor.extract_circular_references(all_text)
        refs = [r for r in refs if r != circular_number]  # évite l'auto-référence

        for ref in refs:
            self.graph.create_reference_relationship(circular_number, ref, "REFERENCES")
            print(f"✅ Relation créée : {circular_number} -REFERENCES-> {ref}")

        return {"circular": circular_number, "references_found": refs}

    def close(self):
        self.graph.close()


if __name__ == "__main__":
    builder = GraphBuilder()

    result = builder.process_and_build(
        pdf_path="/home/nour/kusor/data/circulars/Cir_2022_01_fr.pdf",
        circular_number="2022-01",
        title="Prévention et résolution des créances non performantes",
        date="2022-03-01",
        category="Risque de crédit"
    )

    print(f"\n📊 Résultat : {result}")
    builder.close()