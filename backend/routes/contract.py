# backend/routes/contract.py
"""Contract Risk Analysis endpoints. Gated to legal and admin roles."""

import os
import shutil
import uuid
from flask import request
from flask_jwt_extended import jwt_required
from flask_restx import Namespace, Resource
from werkzeug.utils import secure_filename

from backend.extensions import get_neo4j_manager
from backend.middleware.auth import role_required
from backend.middleware.audit_middleware import audit_action
from backend.agent.contract_agent import ContractAgent

ns = Namespace("contract", description="Contract Risk Analysis operations")

UPLOAD_TEMP_DIR = "/tmp/kusor_uploads/contract"


@ns.route("/analyze")
class ContractAnalyze(Resource):
    @jwt_required()
    @role_required("legal", "admin")
    @audit_action("CONTRACT_ANALYZED", "contract")
    def post(self):
        """Analyze contract PDF/text for regulatory compliance and temporal risk."""
        session_id = str(uuid.uuid4())[:8]
        temp_dir = os.path.join(UPLOAD_TEMP_DIR, session_id)
        os.makedirs(temp_dir, exist_ok=True)
        pdf_path = None

        try:
            signing_date = request.form.get("signing_date")
            contract_type = request.form.get("contract_type", "credit_immobilier")
            title = request.form.get("title", "Contrat de Crédit")
            text = request.form.get("text", "")

            if "contract_file" in request.files or "file" in request.files:
                file = request.files.get("contract_file") or request.files.get("file")
                if file and file.filename:
                    safe_name = secure_filename(file.filename)
                    pdf_path = os.path.join(temp_dir, safe_name)
                    file.save(pdf_path)
                    title = safe_name

            elif not request.form and request.is_json:
                data = request.get_json() or {}
                text = data.get("text", "")
                title = data.get("title", "Contrat Sans Titre")
                signing_date = data.get("signing_date")
                contract_type = data.get("contract_type", "credit_immobilier")

            if not pdf_path and not text:
                return {"error": "Fichier PDF ou texte de contrat requis"}, 400

            agent = ContractAgent(neo4j=get_neo4j_manager())
            report = agent.analyze_contract(
                contract_input=pdf_path if pdf_path else text,
                contract_title=title,
                contract_date=signing_date,
                contract_type=contract_type,
            )
            return report.model_dump(), 200

        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
