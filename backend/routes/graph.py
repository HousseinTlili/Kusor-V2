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
    @jwt_required()
    @api.marshal_with(subgraph_response)
    def get(self):
        """
        GET /api/graph/subgraph?circular=2024-01
        Returns: {nodes: [{id, label, type, properties}], edges: [{source, target, type}]}
        Formatted for Angular ngx-graph consumption.
        """
        circular = request.args.get("circular")
        
        # If no circular is specified, default to the most recent circular in the database
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
