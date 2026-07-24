import os
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
import instructor
from backend.retrieval.schemas import RetrievedChunk
from backend.agent.schemas import AgentResponse
from backend.agent.prompts import SYSTEM_PROMPT
from backend.graph.cypher_queries import GET_CIRCULAR_RELATIONS, GET_CIRCULAR_BY_NUMBER

def _chunk_to_dict(c: RetrievedChunk) -> Dict[str, Any]:
    return {
        "content": c.content,
        "document_id": c.document_id,
        "chunk_index": c.chunk_index,
        "page_number": c.page_number,
        "source_filename": c.source_filename,
        "circular_number": c.circular_number,
        "score": c.score,
        "retrieval_method": c.retrieval_method
    }

def search_hybrid(
    hybrid_retriever: Any,
    question: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Full hybrid search: vector + BM25 + graph, fused with RRF, reranked.
    Use for: factual questions, general queries.
    """
    chunks = hybrid_retriever.retrieve(question, top_k=top_k)
    return [_chunk_to_dict(c) for c in chunks]

def search_graph_only(
    graph_searcher: Any,
    question: str,
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    """
    Graph-only search: entity extraction → Neo4j traversal → chunk retrieval.
    Use for: relational questions about circular connections.
    """
    chunks = graph_searcher.search(question, top_k=top_k)
    return [_chunk_to_dict(c) for c in chunks]

def search_bm25_only(
    bm25_searcher: Any,
    question: str,
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    """
    BM25-only keyword search.
    Use for: exact term lookups, specific article numbers.
    """
    chunks = bm25_searcher.search(question, top_k=top_k)
    return [_chunk_to_dict(c) for c in chunks]

def get_circular_relations(
    neo4j_manager: Any,
    circular_number: str,
) -> Dict[str, Any]:
    """
    Get all relationships for a specific circular from Neo4j.
    Returns: incoming and outgoing relationships with types.
    Use for: "has this circular been modified/abrogated?"
    """
    results = neo4j_manager.execute_query(
        GET_CIRCULAR_RELATIONS,
        {"number": circular_number}
    )
    relationships = []
    for r in results:
        rel_type = r.get("relationship")
        related_node = r.get("related")
        related_num = None
        if related_node:
            if hasattr(related_node, "get"):
                related_num = related_node.get("number")
            elif isinstance(related_node, dict):
                related_num = related_node.get("number")
        if related_num:
            relationships.append({
                "type": rel_type,
                "circular": related_num
            })
    return {
        "circular_number": circular_number,
        "relationships": relationships
    }

def get_circular_details(
    neo4j_manager: Any,
    circular_number: str,
) -> Dict[str, Any]:
    """
    Get full metadata for a circular from Neo4j.
    Returns: number, title, date, category, status, all relationships.
    """
    results = neo4j_manager.execute_query(
        GET_CIRCULAR_BY_NUMBER,
        {"number": circular_number}
    )
    if not results:
        return {}
    c = results[0].get("c")
    details = {}
    if c:
        if hasattr(c, "get"):
            details = {k: c.get(k) for k in ["id", "number", "title", "date", "category", "url", "status"]}
        elif isinstance(c, dict):
            details = {k: c.get(k) for k in ["id", "number", "title", "date", "category", "url", "status"]}
            
    rels = get_circular_relations(neo4j_manager, circular_number)
    details["relationships"] = rels.get("relationships", [])
    return details

def generate_answer(
    question: str,
    context_chunks: List[Dict[str, Any]],
    graph_context: Optional[str] = None,
    question_type: str = "factual",
) -> str:
    """
    Generate an answer using Qwen2.5-7B via Ollama.
    Uses format="json" and Instructor for structured output.
    Retries up to 3 times on malformed JSON.
    """
    from backend.agent.schemas import QuestionType
    if not context_chunks:
        # Return fallback response as JSON string
        resp = AgentResponse(
            answer="Les documents disponibles ne me permettent pas de répondre à cette question.",
            sources=[],
            confidence_score=0.0,
            related_circulars=[],
            graph_path_used=False,
            question_type=QuestionType(question_type) if isinstance(question_type, str) else question_type
        )
        return resp.model_dump_json()

    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    llm_model = os.getenv("LLM_MODEL", "qwen2.5:7b")
    
    client = instructor.from_openai(
        OpenAI(
            base_url=f"{ollama_base_url}/v1",
            api_key="ollama"
        ),
        mode=instructor.Mode.JSON
    )
    
    # Format context
    context = ""
    for idx, chunk in enumerate(context_chunks):
        circ_num = chunk.get("circular_number") or "Inconnu"
        page = chunk.get("page_number") or 1
        filename = chunk.get("source_filename") or "Document"
        context += f"Extrait {idx+1} [Circulaire N° {circ_num}, p. {page}, Source: {filename}]:\n{chunk.get('content')}\n\n"
        
    graph_ctx = graph_context or "Aucune information additionnelle du graphe de connaissances."
    system_content = SYSTEM_PROMPT.format(context=context, graph_context=graph_ctx)
    
    response = client.chat.completions.create(
        model=llm_model,
        response_model=AgentResponse,
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": f"Question type: {question_type}\nQuestion: {question}"}
        ],
        max_retries=3,
        temperature=0.3
    )
    
    return response.model_dump_json()
