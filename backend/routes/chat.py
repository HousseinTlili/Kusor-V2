# backend/routes/chat.py
"""
Chat endpoints: /chat/message with SSE token streaming, /chat/sessions.
"""

import json
import logging
from flask import request, Response, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restx import Namespace, Resource

from backend.extensions import db, get_hybrid_retriever
from backend.models.conversation import ConversationSession, ConversationMessage
from backend.agent.agent_graph import build_main_agent_graph
from backend.middleware.audit_middleware import audit_action

logger = logging.getLogger(__name__)

ns = Namespace("chat", description="RAG Agent Chat & SSE Streaming operations")


@ns.route("/message")
class ChatMessage(Resource):
    @jwt_required()
    @audit_action("CHAT_MESSAGE_SENT", "chat")
    def post(self):
        """Send message to RAG agent. Supports JSON response or SSE streaming when stream=true."""
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        message = data.get("message", "")
        session_id = data.get("session_id")
        stream = data.get("stream", False)

        if not message:
            return {"error": "Message requis"}, 400

        # Get or create conversation session
        if session_id:
            session = ConversationSession.query.filter_by(id=session_id, user_id=user_id).first()
            if not session:
                return {"error": "Session introuvable"}, 404
        else:
            session = ConversationSession(
                user_id=user_id,
                title=message[:30] + ("..." if len(message) > 30 else ""),
            )
            db.session.add(session)
            db.session.commit()
            session_id = session.id

        # Save user message
        user_msg = ConversationMessage(
            session_id=session_id,
            role="user",
            content=message,
        )
        db.session.add(user_msg)
        db.session.commit()

        # Build agent graph and execute
        retriever = get_hybrid_retriever()
        graph = build_main_agent_graph(retriever=retriever)

        state = {
            "question": message,
            "session_id": session_id,
            "chat_history": [],
        }

        res = graph.invoke(state)
        answer = res.get("answer", "")
        confidence = res.get("confidence_score", 0.0)
        sources = res.get("sources", [])

        # Save assistant response
        ast_msg = ConversationMessage(
            session_id=session_id,
            role="assistant",
            content=answer,
            confidence=confidence,
            sources_json=json.dumps(sources),
        )
        db.session.add(ast_msg)
        db.session.commit()

        if stream:
            def generate_sse():
                # 1. Stream token events
                words = answer.split()
                for word in words:
                    event_payload = json.dumps({"event": "token", "data": word + " "})
                    yield f"data: {event_payload}\n\n"

                # 2. Stream sources event
                sources_payload = json.dumps({"event": "sources", "data": sources})
                yield f"data: {sources_payload}\n\n"

                # 3. Stream completion event
                done_payload = json.dumps({
                    "event": "done",
                    "data": {
                        "confidence_score": confidence,
                        "session_id": session_id,
                    },
                })
                yield f"data: {done_payload}\n\n"

            return Response(
                stream_with_context(generate_sse()),
                mimetype="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                },
            )

        return {
            "session_id": session_id,
            "message": answer,
            "confidence_score": confidence,
            "sources": sources,
        }, 200


@ns.route("/sessions")
class ChatSessions(Resource):
    @jwt_required()
    def get(self):
        """List user chat sessions."""
        user_id = get_jwt_identity()
        sessions = ConversationSession.query.filter_by(user_id=user_id).order_by(ConversationSession.updated_at.desc()).all()
        return [
            {
                "id": s.id,
                "title": s.title,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            }
            for s in sessions
        ], 200


@ns.route("/sessions/<string:id>/history")
class ChatSessionHistory(Resource):
    @jwt_required()
    def get(self, id):
        """Get session message history."""
        user_id = get_jwt_identity()
        session = ConversationSession.query.filter_by(id=id, user_id=user_id).first()
        if not session:
            return {"error": "Session introuvable"}, 404

        msgs = ConversationMessage.query.filter_by(session_id=id).order_by(ConversationMessage.created_at.asc()).all()
        return [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "confidence": m.confidence,
                "sources": json.loads(m.sources_json) if m.sources_json else [],
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in msgs
        ], 200
