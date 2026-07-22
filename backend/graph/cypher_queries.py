# backend/graph/cypher_queries.py
"""
Cypher query templates for KUSOR v3.
Includes point-in-time temporal date filtering queries.
"""

# ── Temporal Point-in-Time Circular Search ───────────────────────
TEMPORAL_CIRCULAR_SEARCH = """
MATCH (c:Circular {reference: $reference})
OPTIONAL MATCH (c)-[r:AMENDS|REPLACES|REFERENCES]->(target:Circular)
WHERE (r.valid_from IS NULL OR r.valid_from <= date($as_of_date))
  AND (r.valid_until IS NULL OR r.valid_until >= date($as_of_date))
RETURN c, type(r) as rel_type, target
"""

# ── Temporal Point-in-Time Subgraph Query ────────────────────────
TEMPORAL_SUBGRAPH_AS_OF = """
MATCH (n)
WHERE (n:Circular OR n:Obligation OR n:Process OR n:ContractTemplate)
OPTIONAL MATCH (n)-[r]->(m)
WHERE (r.valid_from IS NULL OR r.valid_from <= date($as_of_date))
  AND (r.valid_until IS NULL OR r.valid_until >= date($as_of_date))
RETURN n, r, m
LIMIT $limit
"""

# ── Obligation Impact Traversal Query ────────────────────────────
OBLIGATION_IMPACT_TRAVERSAL = """
MATCH (c:Circular {reference: $circular_ref})
MATCH (c)-[r1:INTRODUCES]->(o:Obligation)
WHERE (r1.valid_from IS NULL OR r1.valid_from <= date($as_of_date))
  AND (r1.valid_until IS NULL OR r1.valid_until >= date($as_of_date))
OPTIONAL MATCH (o)-[r2:AFFECTS]->(p:Process)
WHERE (r2.valid_from IS NULL OR r2.valid_from <= date($as_of_date))
  AND (r2.valid_until IS NULL OR r2.valid_until >= date($as_of_date))
OPTIONAL MATCH (o)-[r3:CONSTRAINS]->(ct:ContractTemplate)
WHERE (r3.valid_from IS NULL OR r3.valid_from <= date($as_of_date))
  AND (r3.valid_until IS NULL OR r3.valid_until >= date($as_of_date))
RETURN o, p, ct
"""
