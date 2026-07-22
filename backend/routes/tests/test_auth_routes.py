# backend/routes/tests/test_auth_routes.py
"""
Unit tests for Auth API routes (login, register, me).
"""

import uuid
from backend.app import create_app


def test_auth_registration_and_login():
    app = create_app()
    uid = uuid.uuid4().hex[:8]
    username = f"user_{uid}"
    email = f"user_{uid}@attijari.tn"

    with app.test_client() as client:
        with app.app_context():
            # 1. Register user
            reg_resp = client.post("/api/auth/register", json={
                "username": username,
                "email": email,
                "password": "Password123!",
                "role": "compliance",
            })
            assert reg_resp.status_code == 201
            assert "access_token" in reg_resp.json

            # 2. Login
            login_resp = client.post("/api/auth/login", json={
                "username": username,
                "password": "Password123!",
            })
            assert login_resp.status_code == 200
            token = login_resp.json["access_token"]

            # 3. Get /me
            me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
            assert me_resp.status_code == 200
            assert me_resp.json["role"] == "compliance"
