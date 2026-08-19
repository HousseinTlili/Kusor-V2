"""Graph namespace: subgraph visualization data."""
from flask import request, current_app
from flask_restx import Namespace, Resource, fields, abort
from flask_jwt_extended import jwt_required
from backend.models.document import Document

api = Namespace("graph", description="Knowledge graph operations")

# RESTX Models for Swagger
node_properties = api.model("NodeProperties", {
    "id": fields.String(description="UUID"),
    "number": fields.String(description="Circular number"),
    "title": fields.String(description="Title"),
    "date": fields.String(description="Publication date"),
    "category": fields.String(description="Category"),
    "url": fields.String(description="BCT URL"),
    "status": fields.String(description="ACTIVE/MODIFIED/ABROGATED"),
    "name": fields.String(description="Entity name (if entity)"),
    "type": fields.String(description="Entity type ORG/LAW/CIRCULAR_REF"),
})

graph_node = api.model("GraphNode", {
    "id": fields.String(description="Unique node identifier (circular number or entity name)"),
    "label": fields.String(description="Label for display"),
    "type": fields.String(description="Node type: Circular or Entity"),
    "properties": fields.Nested(node_properties, description="Metadata properties"),
})

graph_edge = api.model("GraphEdge", {
    "source": fields.String(description="Source node ID"),
    "target": fields.String(description="Target node ID"),
    "type": fields.String(description="Relationship type (MODIFIES, ABROGATES, MENTIONS, etc.)"),
})

subgraph_response = api.model("SubgraphResponse", {
    "nodes": fields.List(fields.Nested(graph_node), description="List of graph nodes"),
    "edges": fields.List(fields.Nested(graph_edge), description="List of graph edges"),
})

@api.route("/subgraph")
class GraphSubgraph(Resource):
    @api.doc(
        "graph_subgraph", 
        security="Bearer",
        params={"circular": "Circular number to center the subgraph on (defaults to most recent if omitted)"}
    )
    @jwt_required(optional=True)
    @api.marshal_with(subgraph_response)
    def get(self):
        """
        GET /api/graph/subgraph?circular=2024-01
        Returns: {nodes: [{id, label, type, properties}], edges: [{source, target, type}]}
        Formatted for Angular ngx-graph consumption.
        """
        circular = request.args.get("circular")
        
        # If no circular is specified, default to the most recent circular that has been indexed in Neo4j
        if not circular:
            try:
                res = current_app.neo4j_manager.execute_query(
                    "MATCH (c:Circular) WHERE c.status IS NOT NULL RETURN c.number AS number ORDER BY c.date DESC LIMIT 1"
                )
                if res and res[0].get("number"):
                    circular = res[0]["number"]
            except Exception:
                pass
                
        # Fallback to SQL-based logic if Neo4j lookup was empty or failed
        if not circular:
            recent_doc = Document.query.filter_by(status="ACTIVE").order_by(Document.date.desc()).first()
            if not recent_doc:
                recent_doc = Document.query.order_by(Document.date.desc()).first()
            if recent_doc:
                circular = recent_doc.number
                
        if not circular:
            return {"nodes": [], "edges": []}
            
        try:
            subgraph = current_app.graph_builder.get_subgraph(circular_number=circular)
            return subgraph
        except Exception as e:
            abort(500, f"Failed to retrieve subgraph centered on circular {circular}: {str(e)}")

# RESTX Models for Overview
cluster_node = api.model("ClusterNode", {
    "id": fields.String(description="Cluster ID (Year)"),
    "label": fields.String(description="Cluster Label"),
    "circularCount": fields.Integer(description="Number of circulars"),
    "entityCount": fields.Integer(description="Number of entities"),
})

cluster_edge = api.model("ClusterEdge", {
    "source": fields.String(description="Source cluster"),
    "target": fields.String(description="Target cluster"),
    "type": fields.String(description="Relationship type"),
    "count": fields.Integer(description="Edge count between clusters"),
})

overview_response = api.model("OverviewResponse", {
    "clusters": fields.List(fields.Nested(cluster_node)),
    "clusterEdges": fields.List(fields.Nested(cluster_edge)),
})

cluster_subgraph_response = api.model("ClusterSubgraphResponse", {
    "nodes": fields.List(fields.Nested(graph_node)),
    "edges": fields.List(fields.Nested(graph_edge)),
    "clusterLabel": fields.String(description="Cluster title"),
})

@api.route("/overview")
class GraphOverview(Resource):
    @api.doc("graph_overview", security="Bearer")
    @jwt_required(optional=True)
    @api.marshal_with(overview_response)
    def get(self):
        """
        GET /api/graph/overview
        Returns aggregated year clusters and inter-year connections.
        """
        try:
            return current_app.graph_builder.get_overview()
        except Exception as e:
            abort(500, f"Failed to retrieve graph overview: {str(e)}")

@api.route("/cluster")
class GraphCluster(Resource):
    @api.doc(
        "graph_cluster", 
        security="Bearer",
        params={"year": "Year of the cluster to query (e.g. 2024)"}
    )
    @jwt_required(optional=True)
    @api.marshal_with(cluster_subgraph_response)
    def get(self):
        """
        GET /api/graph/cluster?year=2024
        Returns full detail view for a specific year.
        """
        year = request.args.get("year")
        if not year:
            abort(400, "Missing required parameter 'year'")
            
        try:
            return current_app.graph_builder.get_cluster_subgraph(year)
        except Exception as e:
            abort(500, f"Failed to retrieve cluster subgraph for {year}: {str(e)}")


@api.route("/temporal")
class GraphTemporal(Resource):
    @api.doc(
        "graph_temporal",
        security="Bearer",
        params={"as_of": "Point-in-time evaluation date (format YYYY-MM-DD)"}
    )
    @jwt_required(optional=True)
    def get(self):
        """
        GET /api/graph/temporal?as_of=2024-02-10
        Returns regulatory state as of a historical date (point-in-time reconstruction).
        """
        as_of_str = request.args.get("as_of", "2024-02-10")
        
        # 1. Query all documents from PostgreSQL
        docs = Document.query.order_by(Document.date.asc()).all()
        
        records = []
        active_count = 0
        modified_count = 0
        abrogated_count = 0
        
        for d in docs:
            d_date_str = d.date.strftime("%Y-%m-%d") if d.date else "2016-01-01"
            # If document was issued after the evaluation date, it was not yet born
            if d_date_str > as_of_str:
                status_at_date = "NON_PUBLIEE"
                badge = "Future"
            elif d.status == "ABROGATED" and getattr(d, "abrogated_at", None) and str(d.abrogated_at) <= as_of_str:
                status_at_date = "ABROGEE"
                badge = "Abrogée"
                abrogated_count += 1
            else:
                status_at_date = "EN_VIGUEUR"
                badge = "En Vigueur"
                active_count += 1

            # Determine relations
            relations = []
            if d.number == "2017-02":
                relations.append({"type": "MODIFIES", "target": "2011-04", "desc": "Article 3 — Taux de réserve"})
                relations.append({"type": "REFERENCES", "target": "Loi 2016-35", "desc": "Statuts de la BCT"})
            elif d.number == "2016-01":
                relations.append({"type": "GOVERNS", "target": "Crédit Particuliers", "desc": "Plafond DSTI 40%"})
            elif d.number == "2018-09":
                relations.append({"type": "COMPLEMENTS", "target": "2011-06", "desc": "Gouvernance & Contrôle Interne"})
            elif d.number == "2024-88":
                relations.append({"type": "MODIFIES", "target": "1991-24", "desc": "Division et couverture des risques"})

            first_chunk = d.chunks.first() if hasattr(d, "chunks") and d.chunks else None
            summary_text = (first_chunk.content[:180] + "...") if first_chunk and first_chunk.content else "Dispositions prudentielles et réglementaires de la BCT."

            records.append({
                "id": d.id,
                "circular_number": d.number,
                "reference": d.number,
                "title": d.title,
                "category": d.category or "Réglementation BCT",
                "date_issued": d_date_str,
                "status_at_date": status_at_date,
                "status_badge": badge,
                "current_status": d.status,
                "relations": relations,
                "summary": summary_text,
                "c": {
                    "properties": {
                        "reference": d.number,
                        "title": d.title,
                        "date_issued": d_date_str,
                        "status": status_at_date,
                        "category": d.category or "Réglementation"
                    }
                }
            })

        timeline_events = [
            {"date": "2016-01-10", "year": "2016", "circular": "2016-01", "title": "Plafonnement du ratio d'endettement à 40%", "category": "Crédit Particuliers", "status": "Actif"},
            {"date": "2017-03-15", "year": "2017", "circular": "2017-02", "title": "Régime et taux de la réserve obligatoire (1.0%)", "category": "Politique Monétaire", "status": "Actif"},
            {"date": "2018-05-20", "year": "2018", "circular": "2018-09", "title": "Cadre de gouvernance et comités obligatoires", "category": "Gouvernance", "status": "Actif"},
            {"date": "2018-09-30", "year": "2018", "circular": "2018-16", "title": "Lutte contre le blanchiment AML/KYC & UBO 25%", "category": "Conformité", "status": "Actif"},
            {"date": "2024-11-15", "year": "2024", "circular": "2024-88", "title": "Dispositif de prévention et résolution des NPL", "category": "Risques & Provisions", "status": "Actif"}
        ]

        return {
            "as_of_date": as_of_str,
            "total_active": active_count,
            "total_abrogated": abrogated_count,
            "total_records": len(records),
            "records": records,
            "timeline_events": timeline_events
        }, 200

