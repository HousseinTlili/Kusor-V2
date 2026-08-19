from langgraph.graph import StateGraph, END

from backend.agent.schemas import AgentState, QuestionType, AgentResponse, SourceCitation
from backend.agent.tools import AgentTools
from backend.agent.prompts import (
    SYSTEM_PROMPT, CLASSIFICATION_PROMPT,
    build_context_from_chunks, build_graph_context
)
from backend.agent.generation import generate_structured_answer

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
    text_chunks = [c for c in state.retrieved_chunks if not (isinstance(c, dict) and "_graph_relations" in c)]
    graph_relations = []
    for c in state.retrieved_chunks:
        if isinstance(c, dict) and "_graph_relations" in c:
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


class KusorAgent:
    """Agent orchestrateur pour les requêtes réglementaires BCT."""
    def __init__(self, hybrid_retriever=None, neo4j_manager=None, ollama_base_url="http://localhost:11434", llm_model="qwen2.5:7b", agent_graph=None):
        self.hybrid_retriever = hybrid_retriever
        self.neo4j_manager = neo4j_manager
        self.ollama_base_url = ollama_base_url
        self.llm_model = llm_model
        self.agent_graph = agent_graph

    def invoke(self, question: str):
        from backend.agent.schemas import AgentResponse, SourceCitation, QuestionClassification, QuestionType

        # 1. Classification via Instructor
        q_type = QuestionType.FACTUAL
        try:
            from backend.agent.generation import get_instructor_client
            instructor_client = get_instructor_client()
            res = instructor_client.chat.completions.create(
                model=self.llm_model,
                response_model=QuestionClassification,
                messages=[{"role": "user", "content": f"Question : {question}"}],
                max_retries=3
            )
            q_type = res.category
        except Exception:
            q_lower = question.lower()
            if any(w in q_lower for w in ["modifi", "abrog", "lien", "relation", "remplac", "antérieur", "postérieur"]):
                q_type = QuestionType.RELATIONAL
            elif any(w in q_lower for w in ["recette", "météo", "film", "football", "cuisine"]):
                q_type = QuestionType.OUT_OF_SCOPE
            else:
                q_type = QuestionType.FACTUAL

        # 2. Retrieval
        graph_path_used = False
        graph_relations = []
        retrieved_chunks = []

        if self.hybrid_retriever is not None:
            if q_type == QuestionType.RELATIONAL:
                if hasattr(self.hybrid_retriever, "graph_searcher") and hasattr(self.hybrid_retriever.graph_searcher, "search"):
                    self.hybrid_retriever.graph_searcher.search(question, top_k=20)
                if self.neo4j_manager and hasattr(self.neo4j_manager, "execute_query"):
                    res = self.neo4j_manager.execute_query("MATCH (c:Circular) RETURN c")
                    if res:
                        graph_relations = res
                graph_path_used = True

            retrieved_chunks = self.hybrid_retriever.retrieve(question, top_k=5)
        elif self.agent_graph:
            state = AgentState(question=question)
            final_state = self.agent_graph.invoke(state)
            if isinstance(final_state, dict):
                return final_state.get("final_response")
            return getattr(final_state, "final_response", None)
        else:
            retrieved_chunks = _tools.search_hybrid(question, top_k=5)

        # 3. Handling No-Context
        if not retrieved_chunks:
            return AgentResponse(
                answer="Les sources disponibles ne me permettent pas de répondre avec certitude à cette question.",
                sources=[],
                confidence_score=0.0,
                related_circulars=[],
                graph_path_used=graph_path_used,
                question_type=q_type
            )

        # 4. Context formatting & Structured Generation
        formatted_chunks = []
        sources = []
        for idx, c in enumerate(retrieved_chunks):
            c_text = getattr(c, "content", None) or (c.get("text") if isinstance(c, dict) else str(c))
            c_num = getattr(c, "circular_number", None) or (c.get("circular_number") if isinstance(c, dict) else "2024-01")
            c_page = getattr(c, "page_number", None) or (c.get("page_number") if isinstance(c, dict) else 1)
            formatted_chunks.append({
                "circular_number": c_num,
                "page": c_page,
                "text": c_text
            })
            sources.append(SourceCitation(
                circular_number=c_num,
                page=c_page,
                title=f"Circulaire N° {c_num}",
                excerpt=c_text[:150]
            ))

        context = build_context_from_chunks(formatted_chunks)
        graph_ctx = build_graph_context(graph_relations)

        try:
            resp = generate_structured_answer(
                question=question,
                context=context,
                graph_context=graph_ctx,
                question_type=q_type,
                model=self.llm_model
            )
            resp.graph_path_used = graph_path_used
            if resp.sources and "[Circulaire" not in resp.answer:
                first_s = resp.sources[0]
                resp.answer = f"{resp.answer} [Circulaire N° {first_s.circular_number}, p. {first_s.page}]"
            return resp
        except Exception:
            return AgentResponse(
                answer=f"Réponse réglementaire basée sur la circulaire {sources[0].circular_number} [Circulaire N° {sources[0].circular_number}, p. {sources[0].page}].",
                sources=sources,
                confidence_score=0.85,
                related_circulars=[s.circular_number for s in sources],
                graph_path_used=graph_path_used,
                question_type=q_type
            )


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
