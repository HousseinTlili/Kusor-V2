# backend/routes/graph.py
"""Graph exploration endpoints: /graph/overview, /graph/subgraph, /graph/temporal."""

from flask import request
from flask_jwt_extended import jwt_required
from flask_restx import Namespace, Resource

from backend.extensions import get_neo4j_manager

ns = Namespace("graph", description="Neo4j Knowledge Graph operations")


@ns.route("/overview")
class GraphOverview(Resource):
    @jwt_required()
    def get(self):
        """Get graph statistics and node counts."""
        neo4j = get_neo4j_manager()
        node_counts = neo4j.run_query("MATCH (n) RETURN labels(n)[0] AS label, count(n) AS cnt")
        rel_counts = neo4j.run_query("MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS cnt")
        return {
            "node_counts": {r["label"]: r["cnt"] for r in node_counts if r.get("label")},
            "relationship_counts": {r["type"]: r["cnt"] for r in rel_counts if r.get("type")},
        }, 200


@ns.route("/subgraph")
class GraphSubgraph(Resource):
    @jwt_required()
    def get(self):
        """Get subgraph around node/label."""
        label = request.args.get("label", "Circular")
        limit = int(request.args.get("limit", 50))
        neo4j = get_neo4j_manager()

        query = f"MATCH (n:{label})-[r]-(m) RETURN n, r, m LIMIT {limit}"
        records = neo4j.run_query(query)
        return {"records": records}, 200


@ns.route("/temporal")
class GraphTemporal(Resource):
    @jwt_required()
    def get(self):
        """Get temporal graph state as of a specified date."""
        as_of_date = request.args.get("as_of_date")
        neo4j = get_neo4j_manager()

        query = """
        MATCH (c:Circular)
        WHERE (c.date_issued IS NULL OR c.date_issued <= date($as_of_date))
        OPTIONAL MATCH (c)-[r]->(m)
        WHERE (r.valid_from IS NULL OR r.valid_from <= date($as_of_date))
          AND (r.valid_until IS NULL OR r.valid_until >= date($as_of_date))
        RETURN c, r, m
        LIMIT 100
        """
        records = neo4j.run_query(query, {"as_of_date": as_of_date}) if as_of_date else []
        return {"as_of_date": as_of_date, "records": records}, 200
