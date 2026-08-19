"""
Évaluation RAGAS de l'agent KUSOR — 100% local via Ollama.

Mesure deux métriques sur un petit jeu de test :
- faithfulness (fidélité) : la réponse est-elle fondée sur le contexte récupéré,
  sans information inventée ?
- answer_relevancy (pertinence) : la réponse répond-elle vraiment à la question ?

Usage :
    python evaluate.py
"""

from datasets import Dataset
from langchain_ollama import ChatOllama, OllamaEmbeddings
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

from agent.agent_graph import build_agent_graph
from agent.schemas import AgentState


# ------------------------------------------------------------------
# Jeu de test — questions représentatives des cas d'usage réels
# ------------------------------------------------------------------
TEST_QUESTIONS = [
    "Quelles sont les règles sur les créances non performantes de la circulaire 2022-01 ?",
    "Quel est le seuil de créances non performantes qui déclenche une stratégie de résolution ?",
    "Qu'est-ce qu'un système d'alerte précoce selon la circulaire 2022-01 ?",
    "La circulaire 2022-01 est-elle liée à d'autres circulaires ?",
    "Quels documents doivent accompagner la stratégie de résolution des créances non performantes ?",
]


def run_agent_on_questions(questions: list[str]) -> dict:
    """Exécute l'agent sur chaque question et collecte réponses + contextes."""
    agent = build_agent_graph()

    data = {"question": [], "answer": [], "contexts": []}

    for i, question in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] {question}")

        initial_state = AgentState(question=question)
        final_state = agent.invoke(initial_state)
        result = final_state["final_response"]

        # RAGAS attend "contexts" comme une liste de chaînes de texte
        contexts = [s.excerpt for s in result.sources] if result.sources else ["Aucun contexte."]

        data["question"].append(question)
        data["answer"].append(result.answer)
        data["contexts"].append(contexts)

    return data


def main():
    print("🤖 Exécution de l'agent sur le jeu de test...\n")
    data = run_agent_on_questions(TEST_QUESTIONS)
    dataset = Dataset.from_dict(data)

    print("\n📊 Évaluation RAGAS (juge = qwen2.5:7b en local, pas d'appel externe)...\n")

    # Le juge RAGAS tourne sur ton propre Ollama local — aucune donnée ne sort.
    judge_llm = LangchainLLMWrapper(ChatOllama(model="qwen2.5:7b", temperature=0))
    judge_embeddings = LangchainEmbeddingsWrapper(OllamaEmbeddings(model="nomic-embed-text"))

    from ragas.run_config import RunConfig

    results = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy],
        llm=judge_llm,
        embeddings=judge_embeddings,
        run_config=RunConfig(timeout=300, max_workers=2),
    )


    print("\n✅ Résultats :\n")
    df = results.to_pandas()
    print("Colonnes disponibles :", list(df.columns))
    print(df.to_string(index=False))


    avg_faithfulness = df["faithfulness"].mean()
    avg_relevancy = df["answer_relevancy"].mean()

    print(f"\n📈 Moyenne fidélité : {avg_faithfulness:.2f}")
    print(f"📈 Moyenne pertinence : {avg_relevancy:.2f}")

    # Sauvegarde pour le rapport
    df.to_csv("ragas_evaluation_results.csv", index=False)
    print("\n💾 Résultats sauvegardés dans ragas_evaluation_results.csv")


if __name__ == "__main__":
    main()