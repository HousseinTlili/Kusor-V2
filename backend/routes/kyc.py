# backend/routes/kyc.py
"""AML/KYC Compliance endpoints. Gated to compliance and admin roles."""

import os
import shutil
import uuid
from flask import request
from flask_jwt_extended import jwt_required
from flask_restx import Namespace, Resource
from werkzeug.utils import secure_filename

from backend.middleware.auth import role_required
from backend.middleware.audit_middleware import audit_action
from backend.agent.kyc_agent import KYCAgent

ns = Namespace("kyc", description="AML/KYC Compliance operations")

UPLOAD_TEMP_DIR = "/tmp/kusor_uploads/kyc"


@ns.route("/check")
class KYCCheck(Resource):
    @jwt_required()
    @role_required("compliance", "admin")
    @audit_action("KYC_CHECK_RUN", "kyc")
    def post(self):
        """Run KYC dossier completeness and sanctions check with multi-file PDF support."""
        session_id = str(uuid.uuid4())[:8]
        temp_dir = os.path.join(UPLOAD_TEMP_DIR, session_id)
        os.makedirs(temp_dir, exist_ok=True)
        uploaded_file_paths = []

        try:
            client_name = request.form.get("client_name")
            client_type = request.form.get("client_type", "individuel")
            deposit_amount = float(request.form.get("deposit_amount_tnd", 0.0))

            # Handle JSON fallback
            if not request.form and request.is_json:
                data = request.get_json() or {}
                client_name = data.get("client_name")
                client_type = data.get("client_type", "individuel")
                deposit_amount = float(data.get("deposit_amount_tnd", 0.0))
                dossier_files = data.get("dossier_files", [])
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

            agent = KYCAgent()
            report = agent.run_kyc_check(
                client_name=client_name,
                client_type=client_type,
                dossier_files=dossier_files,
                deposit_amount_tnd=deposit_amount,
            )
            return report.model_dump(), 200

        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
