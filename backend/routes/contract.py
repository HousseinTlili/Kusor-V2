# backend/routes/contract.py
"""Contract Risk Analysis endpoints. Gated to legal and admin roles."""

from flask import request
from flask_jwt_extended import jwt_required
from flask_restx import Namespace, Resource

from backend.extensions import get_neo4j_manager
from backend.middleware.auth import role_required
from backend.middleware.audit_middleware import audit_action
from backend.agent.contract_agent import ContractAgent

ns = Namespace("contract", description="Contract Risk Analysis operations")


@ns.route("/analyze")
class ContractAnalyze(Resource):
    @jwt_required()
    @role_required("legal", "admin")
    @audit_action("CONTRACT_ANALYZED", "contract")
    def post(self):
        """Analyze contract PDF/text for regulatory compliance and temporal risk."""
        data = request.get_json() or {}
        text = data.get("text", "")
        title = data.get("title", "Contrat Sans Titre")

        if not text and "file" in request.files:
            file = request.files["file"]
            text = file.read().decode("utf-8", errors="ignore")
            title = file.filename

        if not text:
            return {"error": "Texte ou fichier de contrat requis"}, 400

        agent = ContractAgent(neo4j=get_neo4j_manager())
        report = agent.analyze_contract(text, title)
        return report.model_dump(), 200
