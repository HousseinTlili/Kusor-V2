"""Chat namespace: messaging and session management."""
import uuid
import json
from flask import request, current_app
from flask_restx import Namespace, Resource, fields, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models.conversation import ConversationSession, ConversationMessage
from backend.extensions import db
from backend.middleware.auth import audit_action

api = Namespace("chat", description="Chat operations")

# RESTX Models for Swagger
source_citation_model = api.model("SourceCitation", {
    "circular_number": fields.String(description="BCT circular number"),
    "title": fields.String(description="Title of the circular"),
    "page": fields.Integer(description="Page number in the PDF"),
    "excerpt": fields.String(description="Excerpt supporting the claim"),
})

chat_message_request = api.model("ChatMessageRequest", {
    "session_id": fields.String(required=False, description="UUID of the chat session (creates new if omitted)"),
    "message": fields.String(required=True, description="The user's query or message"),
})

chat_response_model = api.model("ChatResponse", {
    "session_id": fields.String(description="The session UUID"),
    "answer": fields.String(description="The assistant's markdown response"),
    "sources": fields.List(fields.Nested(source_citation_model), description="Sources cited in the answer"),
    "confidence_score": fields.Float(description="Confidence score (0.0-1.0)"),
    "related_circulars": fields.List(fields.String, description="Related circular numbers"),
    "graph_path_used": fields.Boolean(description="Whether Neo4j graph search was utilized"),
    "question_type": fields.String(description="The classified question type"),
})

message_history_model = api.model("MessageHistoryItem", {
    "id": fields.String(description="Message UUID"),
    "role": fields.String(description="user or assistant"),
    "content": fields.String(description="Text of the message"),
    "sources": fields.List(fields.Nested(source_citation_model), description="Sources (for assistant messages)"),
    "confidence": fields.Float(description="Confidence score (for assistant messages)"),
    "created_at": fields.String(description="Creation timestamp"),
})

session_response_model = api.model("SessionResponse", {
    "id": fields.String(description="Session UUID"),
    "title": fields.String(description="Session title"),
    "created_at": fields.String(description="Creation timestamp"),
})

@api.route("/message")
class ChatMessage(Resource):
    @api.doc("send_message", security="Bearer")
    @jwt_required()
    @api.expect(chat_message_request, validate=True)
    @api.marshal_with(chat_response_model)
    @audit_action("CHAT_MESSAGE_SENT", "ConversationMessage")
    def post(self):
        """POST /api/chat/message — send message, receive agent response"""
        user_id = get_jwt_identity()
        data = request.json
        session_id = data.get("session_id")
        message_text = data.get("message")
        
        session = None
        if session_id:
            session = ConversationSession.query.filter_by(id=session_id, user_id=user_id).first()
            if not session:
                abort(404, "Session not found or access denied")
        else:
            # Create new session
            session_id = str(uuid.uuid4())
            title = message_text[:50] + ("..." if len(message_text) > 50 else "")
            session = ConversationSession(
                id=session_id,
                user_id=user_id,
                title=title
            )
            db.session.add(session)
            db.session.commit()
            
        # Save user message to Postgres
        user_msg = ConversationMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="user",
            content=message_text
        )
        db.session.add(user_msg)
        db.session.commit()
        
        # Invoke agent
        try:
            agent_res = current_app.kusor_agent.invoke(message_text)
        except Exception as e:
            # Handle failure gracefully by writing a fallback
            from backend.agent.schemas import AgentResponse, QuestionType
            agent_res = AgentResponse(
                answer=f"Désolé, une erreur s'est produite lors du traitement : {str(e)}",
                sources=[],
                confidence_score=0.0,
                related_circulars=[],
                graph_path_used=False,
                question_type=QuestionType.FACTUAL
            )
            
        # Save assistant message to Postgres
        sources_list = [s.model_dump() for s in agent_res.sources]
        assistant_msg = ConversationMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="assistant",
            content=agent_res.answer,
            sources_json=json.dumps(sources_list) if sources_list else None,
            confidence=agent_res.confidence_score
        )
        db.session.add(assistant_msg)
        db.session.commit()
        
        return {
            "session_id": session_id,
            "answer": agent_res.answer,
            "sources": sources_list,
            "confidence_score": agent_res.confidence_score,
            "related_circulars": agent_res.related_circulars,
            "graph_path_used": agent_res.graph_path_used,
            "question_type": agent_res.question_type.value if hasattr(agent_res.question_type, "value") else str(agent_res.question_type)
        }

@api.route("/history/<string:session_id>")
class ChatHistory(Resource):
    @api.doc("chat_history", security="Bearer")
    @jwt_required()
    @api.marshal_list_with(message_history_model)
    def get(self, session_id: str):
        """GET /api/chat/history/:session_id — returns all messages in a session"""
        user_id = get_jwt_identity()
        session = ConversationSession.query.filter_by(id=session_id, user_id=user_id).first()
        if not session:
            abort(404, "Session not found or access denied")
            
        messages = ConversationMessage.query.filter_by(session_id=session_id).order_by(ConversationMessage.created_at.asc()).all()
        
        history = []
        for msg in messages:
            sources = []
            if msg.sources_json:
                try:
                    sources = json.loads(msg.sources_json)
                except Exception:
                    pass
            history.append({
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "sources": sources,
                "confidence": msg.confidence,
                "created_at": msg.created_at.isoformat() if msg.created_at else None
            })
            
        return history

@api.route("/sessions")
class ChatSessions(Resource):
    @api.doc("list_sessions", security="Bearer")
    @jwt_required()
    @api.marshal_list_with(session_response_model)
    def get(self):
        """GET /api/chat/sessions — list all sessions for current user"""
        user_id = get_jwt_identity()
        sessions = ConversationSession.query.filter_by(user_id=user_id).order_by(ConversationSession.created_at.desc()).all()
        
        return [{
            "id": s.id,
            "title": s.title,
            "created_at": s.created_at.isoformat() if s.created_at else None
        } for s in sessions]
