# backend/agent/tests/test_propagation_agent.py
"""
Unit tests for ChangePropagationAgent.
"""

from backend.agent.propagation_agent import ChangePropagationAgent
from backend.config import Config
from backend.graph.neo4j_manager import Neo4jManager


def test_propagation_agent_analysis():
    cfg = Config()
    neo4j = Neo4jManager(cfg.NEO4J_URI, cfg.NEO4J_USER, cfg.NEO4J_PASSWORD)

    agent = ChangePropagationAgent(neo4j)
    report = agent.analyze_impact("2024-88")

    assert report.source_circular_ref == "2024-88"
    assert report.total_affected >= 0
    neo4j.close()
