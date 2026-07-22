# backend/retrieval/tests/test_obligation_searcher.py
"""
Unit tests for ObligationSearcher.
"""

from backend.config import Config
from backend.graph.neo4j_manager import Neo4jManager
from backend.retrieval.obligation_searcher import ObligationSearcher


def test_obligation_searcher_cypher_query():
    cfg = Config()
    neo4j = Neo4jManager(cfg.NEO4J_URI, cfg.NEO4J_USER, cfg.NEO4J_PASSWORD)

    # Seed test obligation
    neo4j.run_query("""
        MERGE (c:Circular {reference: '2024-88'})
        MERGE (o:Obligation {id: 'ob_test_99'})
        SET o.text = 'Les banques doivent maintenir un ratio de liquidité supérieur à 100%.',
            o.obligation_type = 'THRESHOLD'
        MERGE (c)-[:INTRODUCES]->(o)
    """)

    searcher = ObligationSearcher(neo4j)
    results = searcher.search("liquidité", top_k=5)

    assert len(results) >= 1
    assert any("2024-88" in r.content for r in results)
    assert any(r.source == "obligation" for r in results)
    neo4j.close()
