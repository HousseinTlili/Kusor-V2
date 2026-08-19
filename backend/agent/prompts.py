"""Prompt templates for the LangGraph agent."""

SYSTEM_PROMPT: str = """IMPORTANT — RÉPONDS EXCLUSIVEMENT EN FRANÇAIS. N'utilise jamais de caractères chinois, arabes ou anglais dans ta réponse, à aucun moment, même en fin de génération.

Tu es KUSOR, un assistant réglementaire intelligent spécialisé dans les circulaires de la Banque Centrale de Tunisie (BCT). Tu réponds UNIQUEMENT en te basant sur les documents fournis dans le contexte.

RÈGLES STRICTES :
1. Réponds UNIQUEMENT à partir des extraits de circulaires fournis dans le contexte. Ne génère JAMAIS d'information non présente dans le contexte.
2. Cite chaque affirmation avec la source exacte au format [Circulaire N° XXXX-XX, p. Y].
3. Si le contexte ne contient pas suffisamment d'information pour répondre, dis-le explicitement : "Les documents disponibles ne me permettent pas de répondre à cette question."
4. Si une circulaire a été abrogée ou modifiée selon le graphe de connaissances, signale-le clairement : "⚠️ Attention : cette circulaire a été [modifiée/abrogée] par la circulaire N° XXXX-XX."
5. Recopie le titre et le numéro exact de chaque source depuis le contexte fourni — ne les invente jamais.
6. Structure ta réponse avec des paragraphes clairs. Utilise des listes à puces pour les énumérations.
7. Pour les questions relationnelles (modifications, abrogations), présente la chaîne chronologique complète.
8. Indique ton niveau de confiance : élevé (>0.8) si plusieurs sources convergent, moyen (0.5-0.8) si une seule source, faible (<0.5) si le contexte est partiel.

CONTEXTE :
{context}

INFORMATIONS DU GRAPHE DE CONNAISSANCES :
{graph_context}

RAPPEL FINAL : réponds intégralement en français, du premier au dernier mot.
"""

CLASSIFICATION_PROMPT: str = """Classifie la question utilisateur dans exactement une de ces catégories :
- "factual" : question sur le contenu d'une circulaire (définitions, conditions, procédures)
- "relational" : question sur les liens entre circulaires (modifications, abrogations, références)
- "temporal" : question sur l'évolution dans le temps (changements, historique)
- "comparative" : question comparant plusieurs circulaires ou dispositions

Question : {question}

Réponds avec UNIQUEMENT le mot de la catégorie, sans explication."""

RELATIONSHIP_EXTRACTION_PROMPT: str = """Analyse le texte suivant d'une circulaire BCT et identifie TOUTES les références à d'autres circulaires.

Pour chaque référence trouvée, identifie :
1. Le numéro de la circulaire référencée (format YYYY-NN)
2. Le type de relation : MODIFIES, ABROGATES, REFERENCES, COMPLEMENTS, ou CONCERNS
3. L'article concerné si applicable
4. La citation exacte du texte justifiant cette relation

Texte de la circulaire N° {source_number} :
{document_text}
"""


def build_context_from_chunks(chunks: list[dict]) -> str:
    """
    Formate une liste de chunks récupérés (Module 5) en texte lisible
    à insérer dans SYSTEM_PROMPT à la place de {context}.
    """
    if not chunks:
        return "Aucun document pertinent trouvé."

    formatted = []
    for i, chunk in enumerate(chunks, 1):
        if isinstance(chunk, dict):
            page = chunk.get("page_number") or chunk.get("page", "?")
            doc_id = chunk.get("document_id", "")
            circ_num = chunk.get("circular_number") or (doc_id.replace("circulaire_", "").replace("_", "-") if doc_id else "?")
            text = chunk.get("text") or chunk.get("content", "")
        else:
            page = getattr(chunk, "page_number", getattr(chunk, "page", "?"))
            doc_id = getattr(chunk, "document_id", "")
            circ_num = getattr(chunk, "circular_number", "") or (doc_id.replace("circulaire_", "").replace("_", "-") if doc_id else "?")
            text = getattr(chunk, "content", getattr(chunk, "text", ""))

        formatted.append(
            f"[Extrait {i} — Circulaire N°{circ_num}, page {page}]\n{text}"
        )

    return "\n\n".join(formatted)


def build_graph_context(relations: list) -> str:
    """
    Formate les relations du graphe (Module 4) en texte lisible
    à insérer dans SYSTEM_PROMPT à la place de {graph_context}.
    """
    if not relations:
        return "Aucune relation trouvée dans le graphe de connaissances."

    formatted = []
    for rel in relations:
        if isinstance(rel, dict):
            source = rel.get("source_query") or rel.get("source", "?")
            target = rel.get("related_circular") or rel.get("target", "?")
        else:
            source = getattr(rel, "source_query", getattr(rel, "source", "?"))
            target = getattr(rel, "related_circular", getattr(rel, "target", "?"))
        formatted.append(f"La circulaire {source} est liée à la circulaire {target}.")

    return "\n".join(formatted)


if __name__ == "__main__":
    fake_chunks = [
        {"page_number": 3, "document_id": "circulaire_2022_01", "text": "Prévention : le traitement précoce et proactif des créances..."},
        {"page_number": 2, "document_id": "circulaire_2022_01", "text": "La présente circulaire vise à réduire le niveau des créances non performantes..."},
    ]

    fake_relations = [
        {"source_query": "2022-01", "related_circular": "2021-05"},
    ]

    context = build_context_from_chunks(fake_chunks)
    graph_context = build_graph_context(fake_relations)

    final_prompt = SYSTEM_PROMPT.format(context=context, graph_context=graph_context)

    print("✅ Prompt système construit avec succès\n")
    print(final_prompt)