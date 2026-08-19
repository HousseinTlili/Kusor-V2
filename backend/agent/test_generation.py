import ollama
from agent.tools import AgentTools
from agent.prompts import SYSTEM_PROMPT, build_context_from_chunks, build_graph_context


def test_simple_generation():
    tools = AgentTools()

    question = "Quelles sont les règles sur les créances non performantes ?"

    # Étape 1 : récupérer le contexte via nos outils déjà testés
    chunks = tools.search_hybrid(question, top_k=3)
    relations = tools.get_circular_relations("2022-01")

    # Étape 2 : formater le contexte pour le prompt
    context = build_context_from_chunks(chunks)
    graph_context = build_graph_context(relations)
    system_prompt = SYSTEM_PROMPT.format(context=context, graph_context=graph_context)

    # Étape 3 : appeler le LLM local via Ollama
    print("🤖 Envoi de la question au LLM (qwen2.5:7b)...\n")

    response = ollama.chat(
        model="qwen2.5:7b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
    )

    print("📝 Réponse du LLM :\n")
    print(response["message"]["content"])

    tools.close()


if __name__ == "__main__":
    test_simple_generation()