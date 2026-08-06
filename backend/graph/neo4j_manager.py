# backend/graph/neo4j_manager.py
"""
Neo4jManager — thread-safe Neo4j driver wrapper for executing Cypher queries.
COPY from v2 with thread pool cleanup & session context safety.
"""

import logging
from datetime import date, datetime, time
from typing import Any, Dict, List, Optional
from neo4j import GraphDatabase, Driver

logger = logging.getLogger(__name__)


def _sanitize_value(val: Any) -> Any:
    """Helper to convert Neo4j/Python date/time/tuple types into JSON-serializable types."""
    if isinstance(val, (date, datetime, time)):
        return val.isoformat()
    if hasattr(val, "iso_format"):
        return val.iso_format()
    if hasattr(val, "isoformat"):
        return val.isoformat()
    if isinstance(val, dict):
        return {k: _sanitize_value(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [_sanitize_value(v) for v in val]
    if hasattr(val, "__dict__"):
        return _sanitize_value(val.__dict__)
    return val


class Neo4jManager:
    """Wrapper for Neo4j Database operations."""

    def __init__(self, uri: str, user: str, password: str):
        self._uri = uri
        self._user = user
        self._password = password
        self._driver: Optional[Driver] = None
        self._connect()

    def _connect(self) -> None:
        try:
            self._driver = GraphDatabase.driver(
                self._uri, auth=(self._user, self._password)
            )
            self._driver.verify_connectivity()
            logger.info("Connected to Neo4j at %s", self._uri)
        except Exception as e:
            logger.error("Failed to connect to Neo4j: %s", e)
            self._driver = None

    def close(self) -> None:
        if self._driver:
            self._driver.close()
            logger.info("Closed Neo4j driver connection.")

    def run_query(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        if not self._driver:
            self._connect()
            if not self._driver:
                logger.error("Neo4j driver is unavailable.")
                return []

        try:
            with self._driver.session() as session:
                result = session.run(query, parameters or {})
                records = [record.data() for record in result]
                return _sanitize_value(records)
        except Exception as e:
            logger.error("Cypher execution failed: %s | Query: %s", e, query[:100])
            raise e
