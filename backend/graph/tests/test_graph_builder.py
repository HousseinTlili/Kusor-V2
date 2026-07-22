# backend/graph/tests/test_graph_builder.py
"""
Unit tests for GraphBuilder temporal relationship creation.
"""

from backend.config import Config
from backend.graph.neo4j_manager import Neo4jManager
from backend.graph.graph_builder import GraphBuilder
from backend.models.document import Document


def test_graph_builder_temporal_circular():
    cfg = Config()
    neo4j = Neo4jManager(cfg.NEO4J_URI, cfg.NEO4J_USER, cfg.NEO4J_PASSWORD)
    builder = GraphBuilder(neo4j)

    doc = Document(
        id="test_doc_graph_1",
        title="Circulaire de test graph",
        number="2024-99",
        doc_type="circular",
    )
    raw_text = "Circulaire N° 2024-99 abrogeant Circulaire N° 2020-01."

    builder.build_document_graph(doc, raw_text)

    res = neo4j.run_query(
        "MATCH (c:Circular {reference: '2024-99'})-[r:REPLACES]->(t:Circular {reference: '2020-01'}) RETURN r.valid_from as vf"
    )
    assert len(res) == 1
    assert res[0]["vf"] is not None
    neo4j.close()
