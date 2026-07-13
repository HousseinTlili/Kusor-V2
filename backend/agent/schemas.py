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
