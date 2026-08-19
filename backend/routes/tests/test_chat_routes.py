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


def test_chat_session_crud_lifecycle():
    """Test Create, Read, Update, Delete for Chat Sessions."""
    app = create_app()
    uid = uuid.uuid4().hex[:8]
    username = f"crud_{uid}"
    email = f"crud_{uid}@attijari.tn"

    with app.test_client() as client:
        with app.app_context():
            # 1. Register & Login
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
            headers = {"Authorization": f"Bearer {token}"}

            # 2. CREATE session
            res_create = client.post(
                "/api/chat/sessions",
                json={"title": "Audit Conformité 2026"},
                headers=headers,
            )
            assert res_create.status_code == 201
            session_id = res_create.json["id"]
            assert res_create.json["title"] == "Audit Conformité 2026"

            # 3. READ all sessions
            res_list = client.get("/api/chat/sessions", headers=headers)
            assert res_list.status_code == 200
            assert any(s["id"] == session_id for s in res_list.json)

            # 4. READ single session
            res_get = client.get(f"/api/chat/session/{session_id}", headers=headers)
            assert res_get.status_code == 200
            assert res_get.json["title"] == "Audit Conformité 2026"

            # 5. UPDATE / Rename session
            res_update = client.put(
                f"/api/chat/session/{session_id}",
                json={"title": "Audit Conformité BCT - Mis à jour"},
                headers=headers,
            )
            assert res_update.status_code == 200
            assert res_update.json["title"] == "Audit Conformité BCT - Mis à jour"

            # 6. DELETE single session
            res_del = client.delete(f"/api/chat/session/{session_id}", headers=headers)
            assert res_del.status_code == 200
            assert res_del.json["id"] == session_id

            # Verify deleted
            res_get_deleted = client.get(f"/api/chat/session/{session_id}", headers=headers)
            assert res_get_deleted.status_code == 404
