# backend/routes/credit.py
"""Credit Pre-Screening endpoints. Gated to credit and admin roles."""

from flask import request
from flask_jwt_extended import jwt_required
from flask_restx import Namespace, Resource

from backend.middleware.auth import role_required
from backend.middleware.audit_middleware import audit_action
from backend.agent.credit_agent import CreditSupervisorAgent

ns = Namespace("credit", description="Credit Dossier Pre-Screening operations")
api = ns


@ns.route("/prescreen")
class CreditPrescreen(Resource):
    @jwt_required()
    @role_required("credit", "admin")
    @audit_action("CREDIT_PRESCREEN_RUN", "credit")
    def post(self):
        """Run multi-agent credit dossier pre-screening."""
        data = request.get_json() or {}
        dossier_id = data.get("dossier_id", "cred_default")
        applicant_name = data.get("applicant_name", "Demandeur Inconnu")
        loan_type = data.get("loan_type", "personal")
        files = data.get("files", [])
        financial_data = data.get("financial_data", {})
        kyc_risk = data.get("kyc_risk_profile", "LOW")

        supervisor = CreditSupervisorAgent()
        report = supervisor.prescreen(
            dossier_id=dossier_id,
            applicant_name=applicant_name,
            loan_type=loan_type,
            files=files,
            financial_data=financial_data,
            kyc_risk_profile=kyc_risk,
        )
        return report.model_dump(), 200
