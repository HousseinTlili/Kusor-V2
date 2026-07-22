# backend/scripts/init_neo4j.py
"""
Initialize Neo4j constraints and indexes for KUSOR v3.

Run once after Neo4j is started:
    python -m backend.scripts.init_neo4j

Creates:
- Uniqueness constraints on all node types
- Performance indexes for common query patterns
- Temporal property indexes for date-range queries
"""

import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.config import Config
from backend.graph.neo4j_manager import Neo4jManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_neo4j():
    """Create all constraints and indexes for the KUSOR v3 knowledge graph."""
    cfg = Config()
    neo4j = Neo4jManager(cfg.NEO4J_URI, cfg.NEO4J_USER, cfg.NEO4J_PASSWORD)

    # ── Uniqueness Constraints ───────────────────────────────────
    constraints = [
        # Circular: reference is globally unique (e.g., "2024-01")
        "CREATE CONSTRAINT circular_reference_unique IF NOT EXISTS "
        "FOR (c:Circular) REQUIRE c.reference IS UNIQUE",

        # Circular: number is globally unique (backward compat with v1 data)
        "CREATE CONSTRAINT circular_number_unique IF NOT EXISTS "
        "FOR (c:Circular) REQUIRE c.number IS UNIQUE",

        # Entity: (name, label) pair is unique
        "CREATE CONSTRAINT entity_name_label_unique IF NOT EXISTS "
        "FOR (e:Entity) REQUIRE (e.name, e.label) IS UNIQUE",

        # Obligation: id is unique
        "CREATE CONSTRAINT obligation_id_unique IF NOT EXISTS "
        "FOR (o:Obligation) REQUIRE o.id IS UNIQUE",

        # Process: id is unique
        "CREATE CONSTRAINT process_id_unique IF NOT EXISTS "
        "FOR (p:Process) REQUIRE p.id IS UNIQUE",

        # ContractTemplate: id is unique
        "CREATE CONSTRAINT contract_template_id_unique IF NOT EXISTS "
        "FOR (ct:ContractTemplate) REQUIRE ct.id IS UNIQUE",

        # Theme: name is unique
        "CREATE CONSTRAINT theme_name_unique IF NOT EXISTS "
        "FOR (t:Theme) REQUIRE t.name IS UNIQUE",
    ]

    # ── Performance Indexes ──────────────────────────────────────
    indexes = [
        # Circular indexes
        "CREATE INDEX circular_document_id IF NOT EXISTS FOR (c:Circular) ON (c.document_id)",
        "CREATE INDEX circular_date_issued IF NOT EXISTS FOR (c:Circular) ON (c.date_issued)",
        "CREATE INDEX circular_status IF NOT EXISTS FOR (c:Circular) ON (c.status)",

        # Section indexes
        "CREATE INDEX section_document_id IF NOT EXISTS FOR (s:Section) ON (s.document_id)",
        "CREATE INDEX section_name IF NOT EXISTS FOR (s:Section) ON (s.name)",

        # Article indexes
        "CREATE INDEX article_document_id IF NOT EXISTS FOR (a:Article) ON (a.document_id)",
        "CREATE INDEX article_name IF NOT EXISTS FOR (a:Article) ON (a.name)",

        # Entity indexes
        "CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)",
        "CREATE INDEX entity_label IF NOT EXISTS FOR (e:Entity) ON (e.label)",

        # Theme indexes
        "CREATE INDEX theme_name IF NOT EXISTS FOR (t:Theme) ON (t.name)",

        # Obligation indexes
        "CREATE INDEX obligation_circular_id IF NOT EXISTS FOR (o:Obligation) ON (o.circular_id)",
        "CREATE INDEX obligation_type IF NOT EXISTS FOR (o:Obligation) ON (o.obligation_type)",
        "CREATE INDEX obligation_article_id IF NOT EXISTS FOR (o:Obligation) ON (o.article_id)",

        # Process indexes
        "CREATE INDEX process_name IF NOT EXISTS FOR (p:Process) ON (p.name)",

        # ContractTemplate indexes
        "CREATE INDEX contract_template_name IF NOT EXISTS FOR (ct:ContractTemplate) ON (ct.name)",

        # Full-text index for entity search (requires APOC)
        "CREATE FULLTEXT INDEX entity_fulltext IF NOT EXISTS "
        "FOR (e:Entity) ON EACH [e.name]",

        # Full-text index for circular search
        "CREATE FULLTEXT INDEX circular_fulltext IF NOT EXISTS "
        "FOR (c:Circular) ON EACH [c.reference, c.title, c.number]",
    ]

    for stmt in constraints:
        try:
            neo4j.run_query(stmt)
            logger.info("✓ %s", stmt[:80])
        except Exception as e:
            logger.warning("⚠ %s — %s", stmt[:80], e)

    for stmt in indexes:
        try:
            neo4j.run_query(stmt)
            logger.info("✓ %s", stmt[:80])
        except Exception as e:
            logger.warning("⚠ %s — %s", stmt[:80], e)

    neo4j.close()
    logger.info("Neo4j v3 initialization complete")


if __name__ == "__main__":
    init_neo4j()
