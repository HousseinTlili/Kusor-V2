import instructor
from backend.config import Config
from openai import OpenAI

from backend.agent.schemas import AgentResponse, QuestionType
from backend.agent.prompts import SYSTEM_PROMPT


def get_instructor_client():
    return instructor.from_openai(
        OpenAI(
            base_url=f"{Config().OLLAMA_BASE_URL}/v1",
            api_key="ollama",
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
    """
    system_content = SYSTEM_PROMPT.format(context=context, graph_context=graph_context)
    user_prompt = f"Question : {question}\nQuestion type: {question_type.value}"
    inst_client = get_instructor_client()

    response = inst_client.chat.completions.create(
        model=model,
        response_model=AgentResponse,
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_prompt},
        ],
        max_retries=3,
        temperature=0.2,
    )

    response.question_type = question_type
    return response

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