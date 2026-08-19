from langgraph.graph import StateGraph, END

from agent.schemas import AgentState, QuestionType
from agent.tools import AgentTools
from agent.prompts import (
    SYSTEM_PROMPT, CLASSIFICATION_PROMPT,
    build_context_from_chunks, build_graph_context
)
from agent.generation import generate_structured_answer

import ollama


_tools = AgentTools()


def analyse_question_node(state: AgentState) -> AgentState:
    """Nœud 1 : classe la question pour orienter la stratégie de recherche."""
    prompt = CLASSIFICATION_PROMPT.format(question=state.question)

    response = ollama.chat(
        model="qwen2.5:7b",
        messages=[{"role": "user", "content": prompt}]
    )

    category_text = response["message"]["content"].strip().lower()

    try:
        state.question_type = QuestionType(category_text)
    except ValueError:
        state.question_type = QuestionType.FACTUAL

    return state


def search_node(state: AgentState) -> AgentState:
    """Nœud 2 : appelle les outils de recherche (Module 5) selon la classification."""
    chunks = _tools.search_hybrid(state.question, top_k=5)
    state.retrieved_chunks = chunks

    import re
    numbers = re.findall(r"\b(\d{4}-\d{2})\b", state.question)

    if numbers:
        relations = _tools.get_circular_relations(numbers[0])
        if relations:
            state.graph_path_used = True
            state.retrieved_chunks.append({"_graph_relations": relations})

    return state


def generate_answer_node(state: AgentState) -> AgentState:
    """Nœud 3 : génère la réponse structurée et validée via Instructor."""
    text_chunks = [c for c in state.retrieved_chunks if "text" in c]
    graph_relations = []
    for c in state.retrieved_chunks:
        if "_graph_relations" in c:
            graph_relations = c["_graph_relations"]

    context = build_context_from_chunks(text_chunks)
    graph_context = build_graph_context(graph_relations)

    result = generate_structured_answer(
        question=state.question,
        context=context,
        graph_context=graph_context,
        question_type=state.question_type or QuestionType.FACTUAL,
    )

    state.final_response = result
    return state


def build_agent_graph():
    """Assemble le graphe LangGraph complet : analyse -> search -> generate -> FIN"""
    graph = StateGraph(AgentState)

    graph.add_node("analyse_question", analyse_question_node)
    graph.add_node("search", search_node)
    graph.add_node("generate_answer", generate_answer_node)

    graph.set_entry_point("analyse_question")
    graph.add_edge("analyse_question", "search")
    graph.add_edge("search", "generate_answer")
    graph.add_edge("generate_answer", END)

    return graph.compile()


if __name__ == "__main__":
    agent = build_agent_graph()

    question = "Quelles sont les règles sur les créances non performantes de la circulaire 2022-01 ?"
    initial_state = AgentState(question=question)

    print(f"🤖 Question : {question}\n")
    print("⏳ Exécution du graphe LangGraph (classification → recherche → génération)...\n")

    final_state = agent.invoke(initial_state)

    print(f"📊 Type de question détecté : {final_state['question_type']}\n")
    print("✅ Réponse finale structurée :\n")
    print(final_state["final_response"].model_dump_json(indent=2))
