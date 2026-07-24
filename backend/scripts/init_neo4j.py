import sys
import os

# Add backend directory to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.graph.neo4j_manager import Neo4jManager

def init_neo4j():
    queries = [
        "CREATE CONSTRAINT circular_number_unique IF NOT EXISTS FOR (c:Circular) REQUIRE c.number IS UNIQUE;",
        "CREATE INDEX circular_date_index IF NOT EXISTS FOR (c:Circular) ON (c.date);",
        "CREATE INDEX circular_status_index IF NOT EXISTS FOR (c:Circular) ON (c.status);",
        "CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:Entity) ON (e.name);",
        "CREATE CONSTRAINT entity_unique IF NOT EXISTS FOR (e:Entity) REQUIRE (e.name, e.type) IS UNIQUE;"
    ]
    
    # We use credentials from env if loaded, otherwise defaults match backend config.py
    manager = Neo4jManager(
        uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        user=os.getenv("NEO4J_USER", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "kusor_password")
    )
    
    print("Connecting to Neo4j...")
    if not manager.health_check():
        print("Error: Could not connect to Neo4j!")
        sys.exit(1)
        
    print("Initializing Neo4j indexes and constraints...")
    for q in queries:
        try:
            manager.execute_write(q)
            print(f"Executed: {q}")
        except Exception as e:
            print(f"Failed to execute: {q}. Error: {e}")
            
    manager.close()
    print("Neo4j initialization completed.")

if __name__ == "__main__":
    init_neo4j()
