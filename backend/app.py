from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from agent.agent_graph import build_agent_graph
from agent.schemas import AgentState

app = Flask(__name__)
CORS(app)
agent_executor = build_agent_graph()


# ------------------------------------------------------------------
# Routes qui servent les interfaces HTML (fichiers dans static/)
# ------------------------------------------------------------------
@app.route("/")
def home():
    return send_from_directory("static", "kusor_chat_final.html")


@app.route("/test")
def console():
    return send_from_directory("static", "kusor_console.html")


@app.route("/dashboard")
def dashboard():
    return send_from_directory("static", "kusor_dashboard.html")


@app.route("/admin")
def admin():
    return send_from_directory("static", "kusor_admin_validation.html")


# ------------------------------------------------------------------
# Routes API existantes (inchangées)
# ------------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200


@app.route("/api/agent/ask", methods=["POST"])
def ask_agent():
    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "Le champ 'question' est requis."}), 400

    try:
        initial_state = AgentState(question=question)
        final_state = agent_executor.invoke(initial_state)
    except Exception as e:
        app.logger.exception("Erreur dans l'agent LangGraph")
        return jsonify({"error": "Erreur interne de l'agent.", "detail": str(e)}), 500

    result = final_state["final_response"]

    score = result.confidence_score
    if score >= 0.8:
        confidence_label = "Confiance haute"
    elif score >= 0.6:
        confidence_label = "Confiance moyenne"
    else:
        confidence_label = "Confiance faible"

    escalade = None
    if score < 0.5 or final_state["question_type"].value == "hors_perimetre":
        escalade = {"text": "Réponse à confiance faible — vérifie les sources ou contacte l'équipe Conformité."}

    return jsonify({
        "classification": final_state["question_type"].value,
        "confidence": confidence_label,
        "confidence_score": score,
        "answer": {
            "text": result.answer,
            "sources": [
                f"{s.circular_number} — p.{s.page} — {s.title}" for s in result.sources
            ],
            "escalade": escalade,
        },
        "related_circulars": result.related_circulars,
        "graph_path_used": result.graph_path_used,
    })


# ------------------------------------------------------------------
# Routes "pont" pour le frontend Angular (Houssein) — utilisent notre
# agent_executor déjà fonctionnel, sans dépendre de SQLAlchemy/JWT.
# ------------------------------------------------------------------
@app.route("/api/chat/message", methods=["POST"])
def chat_message():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    session_id = data.get("session_id", "local-session")

    if not message:
        return jsonify({"error": "Le champ 'message' est requis."}), 400

    try:
        initial_state = AgentState(question=message)
        final_state = agent_executor.invoke(initial_state)
    except Exception as e:
        app.logger.exception("Erreur dans l'agent LangGraph")
        return jsonify({"error": "Erreur interne de l'agent.", "detail": str(e)}), 500

    result = final_state["final_response"]

    return jsonify({
        "session_id": session_id,
        "answer": result.answer,
        "sources": [
            {
                "circular_number": s.circular_number,
                "title": s.title,
                "page": s.page,
                "excerpt": s.excerpt,
            }
            for s in result.sources
        ],
        "confidence_score": result.confidence_score,
        "related_circulars": result.related_circulars,
        "graph_path_used": result.graph_path_used,
        "question_type": final_state["question_type"].value,
    })


@app.route("/api/chat/sessions", methods=["GET"])
def chat_sessions():
    # Pas de persistance de session pour l'instant — liste vide
    # pour éviter le 404 et permettre à l'UI de s'afficher normalement.
    return jsonify([])

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)