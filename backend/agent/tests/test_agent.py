import pytest
from unittest.mock import MagicMock, patch
from pydantic import BaseModel
from backend.agent.agent_graph import KusorAgent
from backend.agent.schemas import AgentResponse, QuestionType, SourceCitation, AgentState
from backend.retrieval.schemas import RetrievedChunk

class TestKusorAgent:
    @pytest.fixture(autouse=True)
    def mock_instructor(self, monkeypatch):
        mock_client = MagicMock()
        
        def side_effect(*args, **kwargs):
            response_model = kwargs.get("response_model")
            
            # Inspect response model fields to dynamically detect classification vs answer schemas
            fields = []
            if hasattr(response_model, "model_fields"):
                fields = list(response_model.model_fields.keys())
            elif hasattr(response_model, "__fields__"):
                fields = list(response_model.__fields__.keys())
                
            if "category" in fields:
                messages = kwargs.get("messages", [])
                user_msg = messages[-1]["content"] if messages else ""
                
                # Extract the actual question from the prompt to avoid matching on prompt template headers
                question_part = ""
                if "Question :" in user_msg:
                    question_part = user_msg.split("Question :")[1]
                else:
                    question_part = user_msg
                
                # Check actual question text for type classification
                category = QuestionType.FACTUAL
                if any(k in question_part.lower() for k in ["modifié", "abrogé", "relation", "chaîne"]):
                    category = QuestionType.RELATIONAL
                elif any(k in question_part.lower() for k in ["compar", "différ"]):
                    category = QuestionType.COMPARATIVE
                elif any(k in question_part.lower() for k in ["temps", "historique", "évolution"]):
                    category = QuestionType.TEMPORAL
                    
                return response_model(category=category)
                
            elif "answer" in fields:
                messages = kwargs.get("messages", [])
                user_msg = messages[-1]["content"] if messages else ""
                
                # Extract question type from user prompt if possible
                q_type = QuestionType.FACTUAL
                for qt in QuestionType:
                    if f"Question type: {qt.value}" in user_msg:
                        q_type = qt
                        break
                        
                return response_model(
                    answer="La réserve obligatoire est fixée à 2% pour les banques. [Circulaire N° 2024-01, p. 1]",
                    sources=[
                        SourceCitation(
                            circular_number="2024-01",
                            title="Circulaire de test",
                            page=1,
                            excerpt="La réserve obligatoire est de 2%"
                        )
                    ],
                    confidence_score=0.95,
                    related_circulars=["2024-02"],
                    graph_path_used=False,
                    question_type=q_type
                )
            raise ValueError(f"Unknown response model fields: {fields}")

        mock_client.chat.completions.create.side_effect = side_effect
        monkeypatch.setattr("instructor.from_openai", lambda *args, **kwargs: mock_client)
        return mock_client

    @pytest.fixture
    def mock_hybrid_retriever(self):
        hr = MagicMock()
        # Default mock retrieve value
        hr.retrieve.return_value = [
            RetrievedChunk(
                content="La reserve obligatoire est de 2%...",
                document_id="doc1",
                chunk_index=0,
                page_number=1,
                source_filename="circulaire_2024-01.pdf",
                circular_number="2024-01",
                score=0.9,
                retrieval_method="vector"
            )
        ]
        hr.graph_searcher = MagicMock()
        hr.graph_searcher.search.return_value = [
            RetrievedChunk(
                content="La reserve obligatoire est de 2%...",
                document_id="doc1",
                chunk_index=0,
                page_number=1,
                source_filename="circulaire_2024-01.pdf",
                circular_number="2024-01",
                score=0.9,
                retrieval_method="graph"
            )
        ]
        hr.bm25_searcher = MagicMock()
        hr.bm25_searcher.search.return_value = []
        hr.reranker = MagicMock()
        hr.reranker.rerank.side_effect = lambda q, chunks, top_k: chunks[:top_k]
        return hr

    @pytest.fixture
    def mock_neo4j_manager(self):
        nm = MagicMock()
        c_node = MagicMock()
        c_node.get.side_effect = lambda k: {
            "id": "uuid-123",
            "number": "2024-01",
            "title": "Circulaire 2024-01",
            "date": "2024-01-01",
            "category": "Reserve",
            "url": "http://bct.tn",
            "status": "ACTIVE"
        }.get(k)
        
        nm.execute_query.return_value = [
            {"c": c_node, "relationship": "MODIFIES", "related": c_node}
        ]
        return nm

    def test_factual_question_uses_vector(self, mock_hybrid_retriever, mock_neo4j_manager) -> None:
        """Factual question should use hybrid retrieval (vector path included)."""
        agent = KusorAgent(mock_hybrid_retriever, mock_neo4j_manager)
        response = agent.invoke("Quelles sont les conditions de la réserve obligatoire?")
        
        assert response.question_type == QuestionType.FACTUAL
        mock_hybrid_retriever.retrieve.assert_called_once()

    def test_factual_question_cites_sources(self, mock_hybrid_retriever, mock_neo4j_manager) -> None:
        """Answer to factual question must include source citations."""
        agent = KusorAgent(mock_hybrid_retriever, mock_neo4j_manager)
        response = agent.invoke("Quelles sont les conditions de la réserve obligatoire?")
        
        assert len(response.sources) > 0
        assert response.sources[0].circular_number == "2024-01"
        assert "[Circulaire N° 2024-01, p. 1]" in response.answer

    def test_relational_question_uses_graph(self, mock_hybrid_retriever, mock_neo4j_manager) -> None:
        """Relational question about modifications should use graph path."""
        agent = KusorAgent(mock_hybrid_retriever, mock_neo4j_manager)
        
        # Include keywords to trigger relational classification
        response = agent.invoke("Est-ce que la circulaire 2024-01 a été modifiée?")
        
        assert response.question_type == QuestionType.RELATIONAL
        mock_hybrid_retriever.graph_searcher.search.assert_called_once()
        mock_neo4j_manager.execute_query.assert_called()

    def test_relational_question_graph_path_flag(self, mock_hybrid_retriever, mock_neo4j_manager) -> None:
        """graph_path_used should be True for relational questions."""
        agent = KusorAgent(mock_hybrid_retriever, mock_neo4j_manager)
        response = agent.invoke("Est-ce que la circulaire 2024-01 a été modifiée?")
        
        assert response.graph_path_used is True

    def test_confidence_score_valid(self, mock_hybrid_retriever, mock_neo4j_manager) -> None:
        """Confidence score must be a float between 0.0 and 1.0."""
        agent = KusorAgent(mock_hybrid_retriever, mock_neo4j_manager)
        response = agent.invoke("Quelles sont les conditions de la réserve obligatoire?")
        
        assert isinstance(response.confidence_score, float)
        assert 0.0 <= response.confidence_score <= 1.0

    def test_output_schema_valid(self, mock_hybrid_retriever, mock_neo4j_manager) -> None:
        """Response must conform to AgentResponse Pydantic schema."""
        agent = KusorAgent(mock_hybrid_retriever, mock_neo4j_manager)
        response = agent.invoke("Quelles sont les conditions de la réserve obligatoire?")
        
        assert isinstance(response, AgentResponse)
        assert response.answer is not None
        assert response.sources is not None
        assert response.confidence_score is not None

    def test_malformed_json_retry(self, mock_instructor, mock_hybrid_retriever, mock_neo4j_manager) -> None:
        """Agent should retry up to 3 times on malformed JSON from LLM."""
        agent = KusorAgent(mock_hybrid_retriever, mock_neo4j_manager)
        agent.invoke("Quelles sont les conditions de la réserve obligatoire?")
        
        # Verify max_retries=3 is passed to Instructor completions create
        calls = mock_instructor.chat.completions.create.call_args_list
        assert len(calls) >= 2
        for call in calls:
            kwargs = call[1]
            assert kwargs["max_retries"] == 3

    def test_no_context_response(self, mock_hybrid_retriever, mock_neo4j_manager) -> None:
        """If no relevant chunks found, agent should indicate insufficient data."""
        # Empty retrieval results
        mock_hybrid_retriever.retrieve.return_value = []
        
        agent = KusorAgent(mock_hybrid_retriever, mock_neo4j_manager)
        response = agent.invoke("Une question farfelue sans aucun rapport.")
        
        assert "ne me permettent pas de répondre" in response.answer
        assert len(response.sources) == 0
        assert response.confidence_score == 0.0
