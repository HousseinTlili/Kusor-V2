import instructor
from config import Config
from openai import OpenAI

from agent.schemas import AgentResponse, QuestionType
from agent.prompts import SYSTEM_PROMPT


# Ollama expose une API compatible OpenAI sur /v1 — on peut donc utiliser
# le client OpenAI standard, juste pointé vers notre instance locale.
client = instructor.from_openai(
    OpenAI(
        base_url=f"{Config().OLLAMA_BASE_URL}/v1",
        api_key="ollama",  # valeur factice : Ollama ne vérifie pas de vraie clé
    ),
    mode=instructor.Mode.JSON,
)


def generate_structured_answer(
    question: str,
    context: str,
    graph_context: str,
    question_type: QuestionType = QuestionType.FACTUAL,
    model: str = "qwen2.5:7b",
) -> AgentResponse:
    """
    Génère une réponse STRUCTURÉE et VALIDÉE (conforme à AgentResponse)
    en utilisant Instructor pour forcer et vérifier le format de sortie.
    Si le LLM se trompe de structure, Instructor relance automatiquement
    la requête avec l'erreur de validation, jusqu'à 3 tentatives.

    temperature=0.2 : réduit la "créativité" du modèle pour limiter les
    dérives (ex. bascule vers une autre langue en fin de génération) et
    rendre les réponses plus stables/reproductibles — important pour un
    outil de conformité réglementaire.
    """
    system_content = SYSTEM_PROMPT.format(context=context, graph_context=graph_context)

    response = client.chat.completions.create(
        model=model,
        response_model=AgentResponse,
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": question},
        ],
        max_retries=3,
        temperature=0.2,
    )

    # On force le champ question_type puisque le prompt système
    # ne le demande pas explicitement au LLM (classification faite séparément)
    response.question_type = question_type

    return response


if __name__ == "__main__":
    from agent.tools import AgentTools
    from agent.prompts import build_context_from_chunks, build_graph_context

    tools = AgentTools()

    question = "Quelles sont les règles sur les créances non performantes ?"
    chunks = tools.search_hybrid(question, top_k=3)
    relations = tools.get_circular_relations("2022-01")

    context = build_context_from_chunks(chunks)
    graph_context = build_graph_context(relations)

    print("🤖 Génération d'une réponse structurée (avec validation automatique)...\n")

    result = generate_structured_answer(
        question=question,
        context=context,
        graph_context=graph_context,
        question_type=QuestionType.FACTUAL,
    )

    print("✅ Réponse structurée et validée :\n")
    print(result.model_dump_json(indent=2))

    tools.close()