# backend/graph/graphiti_manager.py
"""
GraphitiManager — integrates persistent conversation memory via graphiti-core.
Stores facts as nodes in Neo4j and retrieves relevant context at session start.
Synchronous wrappers (asyncio.run) bridge graphiti-core async methods into Flask's sync context.
"""

from __future__ import annotations

import asyncio
import logging
from typing import List, Dict, Any, Optional

from graphiti_core import Graphiti
from backend.config import Config

logger = logging.getLogger(__name__)


class GraphitiMemoryManager:
    """Manages conversational memory episodes using Graphiti over Neo4j."""

    def __init__(self, config: Optional[Config] = None):
        cfg = config or Config()
        try:
            self._graphiti = Graphiti(
                neo4j_uri=cfg.NEO4J_URI,
                neo4j_user=cfg.NEO4J_USER,
                neo4j_password=cfg.NEO4J_PASSWORD,
            )
            logger.info("Graphiti persistent memory initialized")
        except Exception as e:
            logger.warning("Graphiti initialization failed: %s", e)
            self._graphiti = None

    def add_conversation_turn(
        self, session_id: str, user_message: str, assistant_response: str
    ) -> None:
        """Add a conversation turn as a Graphiti episode (synchronous wrapper for Flask)."""
        if not self._graphiti:
            return

        try:
            episode_body = f"User: {user_message}\nAssistant: {assistant_response}"
            asyncio.run(
                self._graphiti.add_episode(
                    name=f"session_{session_id}",
                    episode_body=episode_body,
                    source_description="User-Assistant Chat Turn",
                )
            )
            logger.info("Saved conversation episode for session %s", session_id)
        except Exception as e:
            logger.error("Failed to add Graphiti episode: %s", e)

    def retrieve_session_facts(
        self, query: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant past facts for a query (synchronous wrapper for Flask)."""
        if not self._graphiti:
            return []

        try:
            results = asyncio.run(self._graphiti.search(query=query, top_k=limit))
            facts = []
            for item in results:
                facts.append({
                    "fact": getattr(item, "fact", str(item)),
                    "score": getattr(item, "score", 1.0),
                })
            return facts
        except Exception as e:
            logger.error("Failed querying Graphiti facts: %s", e)
            return []
