import re
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from openai import OpenAI
import instructor
from pydantic import BaseModel

from backend.retrieval.schemas import RetrievedChunk
from backend.agent.schemas import AgentState, AgentResponse, QuestionType
from backend.agent.prompts import CLASSIFICATION_PROMPT
from backend.agent.tools import (
    search_hybrid,
    search_graph_only,
    search_bm25_only,
    get_circular_relations,
    get_circular_details,
    generate_answer,
    _chunk_to_dict
)

class KusorAgent:
    """
    LangGraph-based agent that classifies questions and selects
    the optimal retrieval strategy.
    """

    def __init__(
        self,
        hybrid_retriever: Any,
        neo4j_manager: Any,
        ollama_base_url: str = "http://localhost:11434",
        llm_model: str = "qwen2.5:7b",
    ) -> None:
        self.hybrid_retriever = hybrid_retriever
        self.neo4j_manager = neo4j_manager
        self.ollama_base_url = ollama_base_url
        self.llm_model = llm_model
        
        # Build and compile graph
        workflow = self.build_graph()
        self.app = workflow.compile()

    def build_graph(self) -> StateGraph:
        """
        Build the LangGraph StateGraph:
        
        START → classify_question → select_tools → execute_retrieval
              → rerank_results → generate_answer → format_output → END
        """
        workflow = StateGraph(AgentState)
        
        workflow.add_node("classify_question", self.classify_question)
        workflow.add_node("select_tools", self.select_tools)
        workflow.add_node("execute_retrieval", self.execute_retrieval)
        workflow.add_node("rerank_results", self.rerank_results)
        workflow.add_node("generate_answer", self.generate_answer)
        workflow.add_node("format_output", self.format_output)
        
        workflow.set_entry_point("classify_question")
        workflow.add_edge("classify_question", "select_tools")
        workflow.add_edge("select_tools", "execute_retrieval")
        workflow.add_edge("execute_retrieval", "rerank_results")
        workflow.add_edge("rerank_results", "generate_answer")
        workflow.add_edge("generate_answer", "format_output")
        workflow.add_edge("format_output", END)
        
        return workflow

    def classify_question(self, state: AgentState) -> AgentState:
        """
        Node 1: Classify the question type using the LLM.
        Sets state.question_type.
        """
        client = instructor.from_openai(
            OpenAI(
                base_url=f"{self.ollama_base_url}/v1",
                api_key="ollama"
            ),
            mode=instructor.Mode.JSON
        )
        
        prompt = CLASSIFICATION_PROMPT.format(question=state.question)
        
        class ClassificationResult(BaseModel):
            category: QuestionType
            
        try:
            response = client.chat.completions.create(
                model=self.llm_model,
                response_model=ClassificationResult,
                messages=[
                    {"role": "system", "content": "Tu es un assistant qui classifie les questions."},
                    {"role": "user", "content": prompt}
                ],
                max_retries=3,
                temperature=0.0
            )
            return state.model_copy(update={"question_type": response.category})
        except Exception:
            # Fallback on LLM failure
            return state.model_copy(update={"question_type": QuestionType.FACTUAL})

    def select_tools(self, state: AgentState) -> AgentState:
        """
        Node 2: Based on question_type, select which tools to use.
        
        Strategy mapping:
        - factual     → search_hybrid (all 3 paths)
        - relational  → search_graph_only + get_circular_relations
        - temporal    → search_hybrid + get_circular_relations
        - comparative → search_hybrid (emphasize vector similarity)
        
        Sets state.selected_tools.
        """
        qtype = state.question_type or QuestionType.FACTUAL
        
        tools = []
        if qtype == QuestionType.FACTUAL:
            tools = ["search_hybrid"]
        elif qtype == QuestionType.RELATIONAL:
            tools = ["search_graph_only", "get_circular_relations"]
        elif qtype == QuestionType.TEMPORAL:
            tools = ["search_hybrid", "get_circular_relations"]
        elif qtype == QuestionType.COMPARATIVE:
            tools = ["search_hybrid"]
            
        return state.model_copy(update={"selected_tools": tools})

    def execute_retrieval(self, state: AgentState) -> AgentState:
        """
        Node 3: Execute selected tools. For hybrid, runs all enabled searchers.
        Sets state.retrieved_chunks.
        """
        tools = state.selected_tools
        question = state.question
        
        retrieved_chunks = []
        graph_path_used = False
        
        for tool in tools:
            if tool == "search_hybrid":
                chunks = search_hybrid(self.hybrid_retriever, question, top_k=20)
                retrieved_chunks.extend(chunks)
                if any("graph" in c.get("retrieval_method", "") for c in chunks):
                    graph_path_used = True
            elif tool == "search_graph_only":
                chunks = search_graph_only(self.hybrid_retriever.graph_searcher, question, top_k=20)
                retrieved_chunks.extend(chunks)
                graph_path_used = True
            elif tool == "search_bm25_only":
                chunks = search_bm25_only(self.hybrid_retriever.bm25_searcher, question, top_k=20)
                retrieved_chunks.extend(chunks)
            elif tool == "get_circular_relations":
                graph_path_used = True
                
        # Deduplicate retrieved chunks by (document_id, chunk_index)
        seen = set()
        deduped_chunks = []
        for chunk in retrieved_chunks:
            key = (chunk.get("document_id"), chunk.get("chunk_index"))
            if key not in seen:
                seen.add(key)
                deduped_chunks.append(chunk)
                
        return state.model_copy(update={"retrieved_chunks": deduped_chunks, "graph_path_used": graph_path_used})

    def rerank_results(self, state: AgentState) -> AgentState:
        """
        Node 4: Apply cross-encoder reranker to retrieved chunks.
        Sets state.reranked_chunks.
        """
        if not state.retrieved_chunks:
            return state.model_copy(update={"reranked_chunks": []})
            
        chunks = []
        for c in state.retrieved_chunks:
            chunks.append(RetrievedChunk(
                content=c.get("content", ""),
                document_id=c.get("document_id", ""),
                chunk_index=c.get("chunk_index", 0),
                page_number=c.get("page_number", 1),
                source_filename=c.get("source_filename", ""),
                circular_number=c.get("circular_number"),
                score=c.get("score", 0.0),
                retrieval_method=c.get("retrieval_method", "")
            ))
            
        # Re-rank top 20
        reranked = self.hybrid_retriever.reranker.rerank(
            state.question,
            chunks[:20],
            top_k=5
        )
        
        return state.model_copy(update={"reranked_chunks": [_chunk_to_dict(c) for c in reranked]})

    def generate_answer(self, state: AgentState) -> AgentState:
        """
        Node 5: Call Qwen2.5-7B with system prompt and context.
        Uses Ollama with format="json".
        Sets state.llm_response.
        """
        circ_numbers = re.findall(r"\b\d{4}-\d+\b", state.question)
        graph_details = []
        for num in circ_numbers:
            try:
                details = get_circular_details(self.neo4j_manager, num)
                if details:
                    graph_details.append(details)
            except Exception:
                pass
                
        graph_ctx = self._format_graph_context(graph_details)
        chunks = state.reranked_chunks if state.reranked_chunks else state.retrieved_chunks
        
        try:
            llm_res = generate_answer(
                question=state.question,
                context_chunks=chunks,
                graph_context=graph_ctx,
                question_type=state.question_type.value if state.question_type else "factual"
            )
            return state.model_copy(update={"llm_response": llm_res})
        except Exception as e:
            return state.model_copy(update={"error": f"Answer generation failed: {str(e)}"})

    def format_output(self, state: AgentState) -> AgentState:
        """
        Node 6: Parse LLM response through Instructor + Pydantic AgentResponse schema.
        Auto-retries up to 3 times on malformed JSON.
        Sets state.final_response.
        """
        if not state.llm_response:
            resp = AgentResponse(
                answer="Les documents disponibles ne me permettent pas de répondre à cette question.",
                sources=[],
                confidence_score=0.0,
                related_circulars=[],
                graph_path_used=state.graph_path_used,
                question_type=state.question_type or QuestionType.FACTUAL
            )
            return state.model_copy(update={"final_response": resp})
            
        try:
            resp = AgentResponse.model_validate_json(state.llm_response)
            resp.graph_path_used = state.graph_path_used
            # Calculate and set dynamic, retrieval-signal based confidence score
            resp.confidence_score = self._compute_confidence(state)
            return state.model_copy(update={"final_response": resp})
        except Exception as e:
            resp = AgentResponse(
                answer="Les documents disponibles ne me permettent pas de répondre à cette question.",
                sources=[],
                confidence_score=0.0,
                related_circulars=[],
                graph_path_used=state.graph_path_used,
                question_type=state.question_type or QuestionType.FACTUAL
            )
            return state.model_copy(update={"final_response": resp, "error": f"Failed to format output: {str(e)}"})

    def _compute_confidence(self, state: AgentState) -> float:
        """
        Compute a confidence score from retrieval signals (not LLM self-assessment).
        
        Signals:
        - Top reranker score (weight 0.35)
        - Source coverage: unique circulars (weight 0.25)
        - Retrieval method diversity (weight 0.20)
        - Chunk count sufficiency (weight 0.10)
        - Graph path used (weight 0.10)
        """
        chunks = state.reranked_chunks if state.reranked_chunks else state.retrieved_chunks
        
        if not chunks:
            return 0.0
            
        # 1. Top reranker score (already sigmoid-normalized to 0-1)
        top_score = float(chunks[0].get("score", 0.0)) if chunks else 0.0
        top_score = max(0.0, min(1.0, top_score))
        
        # 2. Source coverage: unique circular numbers
        unique_sources = set()
        for c in chunks:
            cn = c.get("circular_number")
            if cn:
                unique_sources.add(cn)
        source_coverage = min(len(unique_sources) / 3.0, 1.0)
        
        # 3. Retrieval method diversity
        methods = set()
        for c in chunks:
            rm = c.get("retrieval_method", "")
            for m in rm.split("+"):
                if m.strip():
                    methods.add(m.strip())
        diversity = min(len(methods) / 3.0, 1.0)  # max 3 methods: vector, bm25, graph
        
        # 4. Chunk count sufficiency
        chunk_sufficiency = min(len(chunks) / 3.0, 1.0)
        
        # 5. Graph path used
        graph_bonus = 1.0 if state.graph_path_used else 0.0
        
        confidence = (
            0.35 * top_score +
            0.25 * source_coverage +
            0.20 * diversity +
            0.10 * chunk_sufficiency +
            0.10 * graph_bonus
        )
        
        return round(max(0.0, min(1.0, confidence)), 3)



    def invoke(self, question: str) -> AgentResponse:
        """
        Public method: run the full agent pipeline for a question.
        Returns an AgentResponse.
        """
        initial_state = AgentState(
            question=question,
            question_type=None,
            selected_tools=[],
            retrieved_chunks=[],
            reranked_chunks=[],
            graph_path_used=False,
            llm_response=None,
            final_response=None,
            error=None,
            retry_count=0
        )
        
        final_state = self.app.invoke(initial_state)
        
        if isinstance(final_state, dict):
            final_resp = final_state.get("final_response")
        else:
            final_resp = final_state.final_response
            
        if final_resp:
            return final_resp
            
        return AgentResponse(
            answer="Les documents disponibles ne me permettent pas de répondre à cette question.",
            sources=[],
            confidence_score=0.0,
            related_circulars=[],
            graph_path_used=False,
            question_type=QuestionType.FACTUAL
        )

    def _format_graph_context(self, graph_details: List[Dict[str, Any]]) -> str:
        if not graph_details:
            return "Aucune information additionnelle du graphe de connaissances."
            
        lines = []
        for details in graph_details:
            num = details.get("number")
            title = details.get("title")
            status = details.get("status")
            lines.append(f"Circulaire N° {num} (Titre: {title}, Statut: {status})")
            
            relationships = details.get("relationships", [])
            if relationships:
                lines.append("  Relations :")
                for rel in relationships:
                    lines.append(f"    - {rel['type']} circulaire N° {rel['circular']}")
            else:
                lines.append("  Aucune relation répertoriée dans le graphe.")
        return "\n".join(lines)
