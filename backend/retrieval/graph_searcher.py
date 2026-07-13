from typing import List, Optional
import re
import spacy
import chromadb
from backend.retrieval.schemas import RetrievedChunk
from backend.graph.neo4j_manager import Neo4jManager
from backend.graph.cypher_queries import SEARCH_BY_ENTITIES

class GraphSearcher:
    """
    Graph-based retrieval: extracts entities/circular numbers from the question,
    queries Neo4j for related circulars, retrieves their chunks from ChromaDB.
    """

    def __init__(
        self,
        neo4j_manager: Neo4jManager,
        chroma_host: str = "localhost",
        chroma_port: int = 8001,
        collection_name: str = "kusor_documents",
        spacy_model: str = "fr_core_news_lg",
    ) -> None:
        self.neo4j_manager = neo4j_manager
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.collection_name = collection_name
        self.spacy_model = spacy_model
        
        # Load spaCy model
        self.nlp = spacy.load(self.spacy_model)

    def search(
        self,
        query: str,
        top_k: int = 10,
    ) -> List[RetrievedChunk]:
        """
        1. Extract entities with spaCy (ORG, LAW) and circular numbers with regex
        2. Query Neo4j: find circulars mentioning those entities / matching numbers
        3. Perform 2-hop traversal from matched circulars
        4. Fetch chunk content from ChromaDB for found circulars
        5. Return top-k chunks scored by graph proximity
        """
        extracted = self._extract_query_entities(query)
        entity_names = extracted["entity_names"]
        circular_numbers = extracted["circular_numbers"]
        
        start_circulars = set(circular_numbers)
        
        # Query Neo4j for circulars mentioning the extracted entities
        if entity_names:
            entity_results = self.neo4j_manager.execute_query(
                SEARCH_BY_ENTITIES,
                {"entity_names": entity_names, "limit": 20}
            )
            for record in entity_results:
                c = record.get("c")
                if c:
                    num = None
                    if hasattr(c, "get"):
                        num = c.get("number")
                    elif isinstance(c, dict):
                        num = c.get("number")
                    else:
                        try:
                            num = c["number"]
                        except Exception:
                            pass
                    if num:
                        start_circulars.add(num)
                        
        if not start_circulars:
            return []
            
        distances = {}
        for num in start_circulars:
            distances[num] = 0
            
        # 2-hop traversal using Neo4j to find related circulars
        query_traverse = """
        UNWIND $start_numbers AS num
        MATCH (start:Circular {number: num})
        OPTIONAL MATCH (start)-[:ABROGATES|MODIFIES|REFERENCES|COMPLEMENTS|CONCERNS]-(c1:Circular)
        OPTIONAL MATCH (c1)-[:ABROGATES|MODIFIES|REFERENCES|COMPLEMENTS|CONCERNS]-(c2:Circular)
        RETURN start.number AS start, c1.number AS hop1, c2.number AS hop2
        """
        results = self.neo4j_manager.execute_query(
            query_traverse,
            {"start_numbers": list(start_circulars)}
        )
        
        # Distance 1
        for r in results:
            h1 = r.get("hop1")
            if h1 and h1 not in distances:
                distances[h1] = 1
                
        # Distance 2
        for r in results:
            h2 = r.get("hop2")
            if h2 and h2 not in distances:
                distances[h2] = 2
                
        # Retrieve chunks from ChromaDB for all identified circulars
        client = chromadb.HttpClient(host=self.chroma_host, port=self.chroma_port)
        collection = client.get_collection(name=self.collection_name)
        
        circulars_list = list(distances.keys())
        retrieved_chunks = []
        
        try:
            res = collection.get(
                where={"circular_number": {"$in": circulars_list}}
            )
        except Exception:
            # Fallback one-by-one query
            res = {"ids": [], "documents": [], "metadatas": []}
            for circ in circulars_list:
                try:
                    circ_res = collection.get(where={"circular_number": circ})
                    if circ_res:
                        res["ids"].extend(circ_res.get("ids", []))
                        res["documents"].extend(circ_res.get("documents", []))
                        res["metadatas"].extend(circ_res.get("metadatas", []))
                except Exception:
                    pass
                    
        if res and res.get("documents"):
            ids = res.get("ids", [])
            documents = res.get("documents", [])
            metadatas = res.get("metadatas", [])
            
            for doc, meta, cid in zip(documents, metadatas, ids):
                circ_num = meta.get("circular_number")
                dist = distances.get(circ_num, 2)
                
                # Proximity score calculation
                score = 1.0 / (1.0 + dist)
                
                retrieved_chunks.append(RetrievedChunk(
                    content=doc,
                    document_id=meta.get("document_id", ""),
                    chunk_index=int(meta.get("chunk_index", 0)),
                    page_number=int(meta.get("page_number", 1)),
                    source_filename=meta.get("source_filename", ""),
                    circular_number=circ_num,
                    score=score,
                    retrieval_method="graph"
                ))
                
        # Sort by score descending, then circular_number and chunk_index ascending
        retrieved_chunks.sort(key=lambda x: (-x.score, x.circular_number or "", x.chunk_index))
        
        return retrieved_chunks[:top_k]

    def _extract_query_entities(self, query: str) -> dict:
        """
        Returns: {
            "entity_names": List[str],
            "circular_numbers": List[str],
        }
        """
        circ_matches = re.findall(r"\b\d{4}-\d+\b", query)
        circular_numbers = list(set(circ_matches))
        
        doc = self.nlp(query)
        entity_names = []
        for ent in doc.ents:
            if ent.label_ in ["ORG", "LAW"]:
                entity_names.append(ent.text)
            elif ent.label_ == "MISC":
                lower_text = ent.text.lower()
                if any(k in lower_text for k in ["loi", "décret", "code", "arrêté", "circulaire"]):
                    entity_names.append(ent.text)
                else:
                    entity_names.append(ent.text)
                    
        return {
            "entity_names": list(set(entity_names)),
            "circular_numbers": circular_numbers
        }
