# backend/routes/impact.py
"""Regulation Change Impact endpoints. Gated to compliance and admin roles."""

from flask_jwt_extended import jwt_required
from flask_restx import Namespace, Resource

from backend.extensions import get_neo4j_manager
from backend.middleware.auth import role_required
from backend.middleware.audit_middleware import audit_action
from backend.agent.propagation_agent import ChangePropagationAgent

ns = Namespace("impact", description="Regulation Change Impact operations")


@ns.route("/<string:circular_id>")
class CircularImpact(Resource):
    @jwt_required()
    @role_required("compliance", "admin")
    @audit_action("CIRCULAR_IMPACT_ANALYZED", "impact")
    def get(self, circular_id):
        """Get downstream regulatory change propagation for a circular."""
        agent = ChangePropagationAgent(neo4j=get_neo4j_manager())
        report = agent.analyze_impact(circular_id)
        return report.model_dump(), 200
