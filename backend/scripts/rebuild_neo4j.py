import os
import sys

# Adjust Python path to allow importing from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app import create_app
from backend.extensions import db
from backend.models.document import Document
from backend.models.chunk import Chunk
from backend.graph.graph_builder import CircularNode

def main():
    print("Initializing Flask App context...")
    app = create_app("development")
    
    with app.app_context():
        # Clean graph first (just in case)
        print("Cleaning existing Neo4j graph...")
        app.neo4j_manager.execute_write("MATCH (n) DETACH DELETE n")
        
        # Initialize constraints/indexes again
        print("Initializing Neo4j schemas & indexes...")
        app.neo4j_manager.execute_write("CREATE CONSTRAINT circular_number_unique IF NOT EXISTS FOR (c:Circular) REQUIRE c.number IS UNIQUE;")
        app.neo4j_manager.execute_write("CREATE INDEX circular_date_index IF NOT EXISTS FOR (c:Circular) ON (c.date);")
        app.neo4j_manager.execute_write("CREATE INDEX circular_status_index IF NOT EXISTS FOR (c:Circular) ON (c.status);")
        app.neo4j_manager.execute_write("CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:Entity) ON (e.name);")
        app.neo4j_manager.execute_write("CREATE CONSTRAINT entity_unique IF NOT EXISTS FOR (e:Entity) REQUIRE (e.name, e.type) IS UNIQUE;")
        
        documents = db.session.query(Document).order_by(Document.date.asc()).all()
        total = len(documents)
        print(f"Found {total} documents in PostgreSQL. Rebuilding Neo4j graph...")
        
        for idx, doc in enumerate(documents, start=1):
            print(f"[{idx}/{total}] Rebuilding graph for Circular {doc.number}...")
            
            # 1. Create Circular Node
            circ_node = CircularNode(
                id=doc.id,
                number=doc.number,
                title=doc.title,
                date=doc.date.strftime("%Y-%m-%d"),
                category=doc.category,
                url=doc.url,
                status=doc.status
            )
            app.bct_scraper.graph_builder.create_circular_node(circ_node)
            
            # 2. Fetch chunks and reconstruct text
            chunks = db.session.query(Chunk).filter_by(document_id=doc.id).order_by(Chunk.chunk_index.asc()).all()
            full_text = "\n".join([c.content for c in chunks])
            
            # 3. Extract entities
            try:
                proc_entities = app.bct_scraper.document_processor._extract_entities(full_text)
                entities = [{"text": ent.text, "type": ent.label} for ent in proc_entities]
                app.bct_scraper.graph_builder.create_entity_nodes(doc.number, entities)
            except Exception as e:
                print(f"  Warning: failed to extract entities for {doc.number}: {e}")
                
            # 4. Extract relationships
            try:
                regex_rels = app.bct_scraper.graph_builder.extract_relationships_regex(doc.number, full_text)
                app.bct_scraper.graph_builder.create_relationships(regex_rels)
                
                llm_rels = app.bct_scraper.graph_builder.extract_relationships_llm(doc.number, full_text)
                app.bct_scraper.graph_builder.create_relationships(llm_rels)
            except Exception as e:
                print(f"  Warning: failed to extract relationships for {doc.number}: {e}")
                
        print("Neo4j graph rebuild complete!")

if __name__ == "__main__":
    main()
