# backend/routes/credit.py
"""Credit Pre-Screening endpoints. Gated to credit and admin roles."""

import os
import shutil
import uuid
from flask import request
from flask_jwt_extended import jwt_required
from flask_restx import Namespace, Resource
from werkzeug.utils import secure_filename

from backend.middleware.auth import role_required
from backend.middleware.audit_middleware import audit_action
from backend.agent.credit_agent import CreditSupervisorAgent

ns = Namespace("credit", description="Credit Dossier Pre-Screening operations")

UPLOAD_TEMP_DIR = "/tmp/kusor_uploads/credit"


@ns.route("/prescreen")
class CreditPrescreen(Resource):
    @jwt_required()
    @role_required("credit", "admin")
    @audit_action("CREDIT_PRESCREEN_RUN", "credit")
    def post(self):
        """Run multi-agent credit dossier pre-screening with multi-file PDF extraction."""
        session_id = str(uuid.uuid4())[:8]
        temp_dir = os.path.join(UPLOAD_TEMP_DIR, session_id)
        os.makedirs(temp_dir, exist_ok=True)
        uploaded_file_paths = []

        try:
            dossier_id = request.form.get("dossier_id", f"cred_{session_id}")
            applicant_name = request.form.get("applicant_name", "Demandeur Inconnu")
            loan_type = request.form.get("loan_type", "hypothecaire")
            declared_amount = float(request.form.get("declared_amount", 0.0))
            declared_term = int(request.form.get("declared_term_months", 0) or request.form.get("declared_term", 0))
            kyc_risk = request.form.get("kyc_risk_profile", "LOW")

            financial_data = {
                "declared_income": float(request.form.get("declared_income", 0.0)),
                "existing_debts": float(request.form.get("existing_debts", 0.0)),
                "guarantor_age": int(request.form.get("guarantor_age")) if request.form.get("guarantor_age") else None,
            }

            # Handle JSON fallback
            if not request.form and request.is_json:
                data = request.get_json() or {}
                dossier_id = data.get("dossier_id", f"cred_{session_id}")
                applicant_name = data.get("applicant_name", "Demandeur Inconnu")
                loan_type = data.get("loan_type", "hypothecaire")
                declared_amount = float(data.get("declared_amount", 0.0))
                declared_term = int(data.get("declared_term_months", 0))
                financial_data = data.get("financial_data", {})
                kyc_risk = data.get("kyc_risk_profile", "LOW")
                dossier_files = data.get("files", [])
            else:
                dossier_files = []
                uploaded_files = request.files.getlist("files") or request.files.getlist("dossier_files")
                for f in uploaded_files:
                    if f and f.filename:
                        safe_name = secure_filename(f.filename)
                        dest_path = os.path.join(temp_dir, safe_name)
                        f.save(dest_path)
                        uploaded_file_paths.append(dest_path)
                        dossier_files.append({"path": dest_path, "name": safe_name})

            supervisor = CreditSupervisorAgent()
            report = supervisor.prescreen(
                dossier_id=dossier_id,
                applicant_name=applicant_name,
                loan_type=loan_type,
                files=dossier_files,
                financial_data=financial_data,
                kyc_risk_profile=kyc_risk,
                declared_amount=declared_amount,
                declared_term_months=declared_term,
            )
            return report.model_dump(), 200

        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
