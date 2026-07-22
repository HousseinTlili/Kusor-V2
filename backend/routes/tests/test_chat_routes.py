# backend/routes/tests/test_chat_routes.py
"""
Unit tests for Chat API routes and SSE streaming.
"""

import uuid
from backend.app import create_app


def test_chat_message_json_response():
    app = create_app()
    uid = uuid.uuid4().hex[:8]
    username = f"chat_{uid}"
    email = f"chat_{uid}@attijari.tn"

    with app.test_client() as client:
        with app.app_context():
            client.post("/api/auth/register", json={
                "username": username,
                "email": email,
                "password": "Password123!",
            })
            login = client.post("/api/auth/login", json={
                "username": username,
                "password": "Password123!",
            })
            token = login.json["access_token"]

            resp = client.post(
                "/api/chat/message",
                json={"message": "Quelle est la règle de liquidité ?"},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            assert "message" in resp.json
            assert "session_id" in resp.json
