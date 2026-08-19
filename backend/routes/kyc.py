# backend/routes/kyc.py
"""AML/KYC Compliance endpoints. Gated to compliance and admin roles."""

from flask import request
from flask_jwt_extended import jwt_required
from flask_restx import Namespace, Resource

from backend.middleware.auth import role_required
from backend.middleware.audit_middleware import audit_action
from backend.agent.kyc_agent import KYCAgent

ns = Namespace("kyc", description="AML/KYC Compliance operations")
api = ns


@ns.route("/check")
class KYCCheck(Resource):
    @jwt_required()
    @role_required("compliance", "admin")
    @audit_action("KYC_CHECK_RUN", "kyc")
    def post(self):
        """Run KYC dossier completeness and sanctions check."""
        data = request.get_json() or {}
        client_name = data.get("client_name") or request.form.get("client_name")
        client_type = data.get("client_type") or request.form.get("client_type", "individual")
        files = data.get("dossier_files") or [f.filename for f in request.files.getlist("dossier_files")]

        if not client_name:
            return {"error": "Nom du client requis"}, 400

        agent = KYCAgent()
        report = agent.run_kyc_check(client_name, client_type, files)
        return report.model_dump(), 200
