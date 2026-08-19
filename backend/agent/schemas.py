from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class QuestionType(str, Enum):
    FACTUAL = "factual"          # "What are the reserve requirements?"
    RELATIONAL = "relational"    # "Has circular X been modified?"
    TEMPORAL = "temporal"        # "What changed between 2020 and 2023?"
    COMPARATIVE = "comparative"  # "How does circular X differ from Y?"

class SourceCitation(BaseModel):
    circular_number: str = Field(description="BCT circular number, e.g. '2024-01'")
    title: str = Field(description="Title of the circular")
    page: int = Field(description="Page number in the original PDF")
    excerpt: str = Field(description="Exact excerpt from the circular supporting the claim")

class AgentResponse(BaseModel):
    answer: str = Field(description="Complete answer in French, with inline citations")
    sources: List[SourceCitation] = Field(description="All sources cited in the answer")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence in answer completeness")
    related_circulars: List[str] = Field(description="Circular numbers related but not directly cited")
    graph_path_used: bool = Field(description="Whether graph traversal was used for this answer")
    question_type: QuestionType = Field(description="Classified type of the question")

class AgentState(BaseModel):
    """LangGraph state object passed between nodes."""
    question: str = ""
    question_type: Optional[QuestionType] = None
    selected_tools: List[str] = Field(default_factory=list)
    retrieved_chunks: List[dict] = Field(default_factory=list)
    reranked_chunks: List[dict] = Field(default_factory=list)
    graph_path_used: bool = False
    llm_response: Optional[str] = None
    final_response: Optional[AgentResponse] = None
    error: Optional[str] = None
    retry_count: int = 0
if __name__ == "__main__":
    citation = SourceCitation(
        circular_number="2022-01",
        title="Prévention et résolution des créances non performantes",
        page=3,
        excerpt="le traitement précoce et proactif des créances..."
    )

    response = AgentResponse(
        answer="La circulaire 2022-01 définit les règles de prévention des créances non performantes.",
        sources=[citation],
        confidence_score=0.85,
        related_circulars=["2021-05"],
        graph_path_used=True,
        question_type=QuestionType.FACTUAL
    )

    print("✅ AgentResponse validé avec succès\n")
    print(response.model_dump_json(indent=2))

    state = AgentState(question="Quelles sont les règles sur les créances non performantes ?")
    print("\n✅ AgentState initialisé avec succès")
    print(state.model_dump_json(indent=2))

    try:
        AgentResponse(
            answer="test",
            sources=[],
            confidence_score=1.5,
            related_circulars=[],
            graph_path_used=False,
            question_type=QuestionType.FACTUAL
        )
        print("\n❌ La validation aurait dû échouer")
    except Exception:
        print("\n✅ Validation Pydantic fonctionne (rejet attendu : score > 1.0 refusé)")