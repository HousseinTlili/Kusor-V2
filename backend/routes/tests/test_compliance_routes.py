# backend/routes/tests/test_compliance_routes.py
"""
Unit tests for Compliance API routes (KYC, Contract, Credit, Impact).
"""

import uuid
from backend.app import create_app


def test_compliance_kyc_and_credit_routes():
    app = create_app()
    uid1 = uuid.uuid4().hex[:8]
    uid2 = uuid.uuid4().hex[:8]

    with app.test_client() as client:
        with app.app_context():
            # 1. Register compliance user
            client.post("/api/auth/register", json={
                "username": f"comp_{uid1}",
                "email": f"comp_{uid1}@attijari.tn",
                "password": "Password123!",
                "role": "compliance",
            })
            login = client.post("/api/auth/login", json={
                "username": f"comp_{uid1}",
                "password": "Password123!",
            })
            comp_token = login.json["access_token"]

            # KYC route check
            kyc_resp = client.post(
                "/api/kyc/check",
                json={"client_name": "SARL Test", "client_type": "corporate", "dossier_files": ["rne_extrait.pdf"]},
                headers={"Authorization": f"Bearer {comp_token}"},
            )
            assert kyc_resp.status_code == 200
            assert "completeness_score" in kyc_resp.json

            # 2. Register credit user
            client.post("/api/auth/register", json={
                "username": f"cred_{uid2}",
                "email": f"cred_{uid2}@attijari.tn",
                "password": "Password123!",
                "role": "credit",
            })
            login_cred = client.post("/api/auth/login", json={
                "username": f"cred_{uid2}",
                "password": "Password123!",
            })
            cred_token = login_cred.json["access_token"]

            # Credit route check
            cred_resp = client.post(
                "/api/credit/prescreen",
                json={
                    "dossier_id": "cred_999",
                    "applicant_name": "Jean Dupont",
                    "files": ["cin.pdf", "bulletin_paie.pdf", "releve_bancaire.pdf", "attestation_travail.pdf"],
                    "financial_data": {"income": 3000, "monthly_debt": 500, "loan_annuity": 300},
                },
                headers={"Authorization": f"Bearer {cred_token}"},
            )
            assert cred_resp.status_code == 200
            assert cred_resp.json["overall_verdict"] == "APPROVE"
