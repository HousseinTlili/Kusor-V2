from typing import Any, Dict, List, Optional
from neo4j import GraphDatabase, Driver, Session

class Neo4jManager:
    """
    Manages Neo4j connection pool and Cypher execution.
    Thread-safe — uses neo4j driver's built-in connection pooling.
    """

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "kusor_password",
    ) -> None:
        self.driver: Driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self) -> None:
        """Close the driver and release all connections."""
        if self.driver:
            self.driver.close()

    def health_check(self) -> bool:
        """Returns True if Neo4j is reachable and responsive."""
        try:
            # Run a simple query to verify connectivity
            self.execute_query("RETURN 1 AS val")
            return True
        except Exception:
            return False

    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        write: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results as list of dicts.
        Uses read or write transaction based on `write` flag.
        """
        params = parameters or {}
        
        def work(tx):
            result = tx.run(query, **params)
            return [dict(record.items()) for record in result]
            
        with self.driver.session() as session:
            if write:
                return session.execute_write(work)
            else:
                return session.execute_read(work)

    def execute_write(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Shorthand for execute_query with write=True."""
        return self.execute_query(query, parameters, write=True)
