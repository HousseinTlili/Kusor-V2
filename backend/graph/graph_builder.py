from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re
import os
from openai import OpenAI
import instructor
from pydantic import BaseModel, Field
from typing import Literal

from backend.graph.neo4j_manager import Neo4jManager
from backend.graph.cypher_queries import (
    CREATE_CIRCULAR_NODE,
    CREATE_ENTITY_NODE,
    LINK_ENTITY_TO_CIRCULAR,
    CREATE_ABROGATES_REL,
    CREATE_MODIFIES_REL,
    CREATE_REFERENCES_REL,
    CREATE_COMPLEMENTS_REL,
    CREATE_CONCERNS_REL,
    GET_CIRCULAR_BY_NUMBER,
    GET_CIRCULAR_RELATIONS,
    GET_MODIFICATION_CHAIN,
    SUBGRAPH_BY_CIRCULAR,
    SEARCH_BY_ENTITIES,
    SEARCH_BY_CIRCULAR_NUMBERS,
    TWO_HOP_TRAVERSAL,
    GET_ALL_CIRCULARS,
    GET_GRAPH_STATS
)

@dataclass
class CircularNode:
    id: str
    number: str
    title: str
    date: str  # ISO 8601 format: "YYYY-MM-DD"
    category: str
    url: str
    status: str  # "ACTIVE", "ABROGATED", "MODIFIED"

@dataclass
class ExtractedRelationship:
    source_number: str
    target_number: str
    relationship_type: str  # MODIFIES, ABROGATES, REFERENCES, COMPLEMENTS, CONCERNS
    article: Optional[str] = None  # For MODIFIES: which article is modified
    confidence: float = 1.0  # 0.0-1.0 — 1.0 for regex, lower for LLM-extracted
    extraction_method: str = "regex"  # "regex" or "llm"


# Pydantic schemas for Instructor extraction
class CircularRelationship(BaseModel):
    target_circular: str = Field(description="Circular number referenced, format YYYY-NN or YYYY-NNN")
    relationship_type: Literal["MODIFIES", "ABROGATES", "REFERENCES", "COMPLEMENTS", "CONCERNS"]
    article: Optional[str] = Field(None, description="Article number if applicable")
    justification: str = Field(description="Quote from text supporting this relationship")

class RelationshipExtractionResult(BaseModel):
    relationships: List[CircularRelationship]


class GraphBuilder:
    """
    Builds and maintains the Neo4j knowledge graph from processed documents.
    
    Two extraction methods:
    1. Regex-based: for explicit references in text (high confidence)
    2. LLM-based: via Instructor + Pydantic for implicit relationships
    """

    # Regex patterns for relationship extraction from document text
    ABROGATES_PATTERN: str = r"(?i)abrog[ée](?:e|s|ant)?\s+(?:la\s+)?circulaire\s+n[°o]\s*(\d{4}-\d+)"
    MODIFIES_PATTERN: str = r"(?i)modifi[ée](?:e|s|ant)?\s+(?:l['\u2019]article\s+(\d+[\w.-]*)\s+(?:de\s+)?)?(?:la\s+)?circulaire\s+n[°o]\s*(\d{4}-\d+)"
    REFERENCES_PATTERN: str = r"(?i)(?:en\s+application\s+de|(?:conform[ée]ment|en\s+vertu)\s+(?:de|à)\s+)?circulaire\s+n[°o]\s*(\d{4}-\d+)"
    COMPLEMENTS_PATTERN: str = r"(?i)compl[èeé]t(?:e|ant)\s+(?:la\s+)?circulaire\s+n[°o]\s*(\d{4}-\d+)"

    def __init__(
        self,
        neo4j_manager: "Neo4jManager",
        ollama_base_url: str = "http://localhost:11434",
        llm_model: str = "qwen2.5:7b",
    ) -> None:
        self.neo4j_manager = neo4j_manager
        self.ollama_base_url = ollama_base_url
        self.llm_model = llm_model

    def create_circular_node(self, circular: CircularNode) -> None:
        """Create or update a Circular node using MERGE."""
        self.neo4j_manager.execute_write(
            CREATE_CIRCULAR_NODE,
            {
                "id": circular.id,
                "number": circular.number,
                "title": circular.title,
                "date": circular.date,
                "category": circular.category,
                "url": circular.url,
                "status": circular.status
            }
        )

    def create_entity_nodes(
        self,
        circular_number: str,
        entities: List[Dict[str, str]],
    ) -> None:
        """
        Create Entity nodes and link them to the Circular via MENTIONS.
        Uses MERGE to avoid duplicates.
        """
        for ent in entities:
            # We support both dict keys: text/name, label/type
            name = ent.get("name") or ent.get("text")
            ent_type = ent.get("type") or ent.get("label")
            if name and ent_type:
                self.neo4j_manager.execute_write(
                    LINK_ENTITY_TO_CIRCULAR,
                    {
                        "circular_number": circular_number,
                        "entity_name": name,
                        "entity_type": ent_type
                    }
                )

    def extract_relationships_regex(
        self,
        source_number: str,
        document_text: str,
    ) -> List[ExtractedRelationship]:
        """
        Extract explicit inter-circular relationships from document text
        using regex patterns. Returns list of extracted relationships.
        """
        relationships = []
        
        # Abrogates
        for m in re.finditer(self.ABROGATES_PATTERN, document_text):
            target = m.group(1)
            if target != source_number:
                relationships.append(ExtractedRelationship(
                    source_number=source_number,
                    target_number=target,
                    relationship_type="ABROGATES",
                    confidence=1.0,
                    extraction_method="regex"
                ))
                
        # Modifies
        for m in re.finditer(self.MODIFIES_PATTERN, document_text):
            article = m.group(1)
            target = m.group(2)
            if target != source_number:
                relationships.append(ExtractedRelationship(
                    source_number=source_number,
                    target_number=target,
                    relationship_type="MODIFIES",
                    article=article,
                    confidence=1.0,
                    extraction_method="regex"
                ))
                
        # Complements
        for m in re.finditer(self.COMPLEMENTS_PATTERN, document_text):
            target = m.group(1)
            if target != source_number:
                relationships.append(ExtractedRelationship(
                    source_number=source_number,
                    target_number=target,
                    relationship_type="COMPLEMENTS",
                    confidence=1.0,
                    extraction_method="regex"
                ))
                
        # References
        for m in re.finditer(self.REFERENCES_PATTERN, document_text):
            target = m.group(1)
            if target != source_number:
                # Check if we already have a more specific relationship (e.g. Abrogates, Modifies, Complements)
                # to the same target circular to avoid duplicate extraction
                already_has_specific = any(
                    r.target_number == target and r.relationship_type in ("ABROGATES", "MODIFIES", "COMPLEMENTS")
                    for r in relationships
                )
                if not already_has_specific:
                    relationships.append(ExtractedRelationship(
                        source_number=source_number,
                        target_number=target,
                        relationship_type="REFERENCES",
                        confidence=1.0,
                        extraction_method="regex"
                    ))
                    
        return relationships

    def extract_relationships_llm(
        self,
        source_number: str,
        document_text: str,
    ) -> List[ExtractedRelationship]:
        """
        Extract implicit relationships using LLM via Instructor + Pydantic.
        Uses Qwen2.5-7B through Ollama.
        """
        # Initialize instructor client using OpenAI compatibility layer
        client = instructor.from_openai(
            OpenAI(
                base_url=f"{self.ollama_base_url}/v1",
                api_key="ollama"
            ),
            mode=instructor.Mode.JSON
        )
        
        prompt = f"""Analyse le texte suivant d'une circulaire BCT et identifie TOUTES les références à d'autres circulaires.
        
        Pour chaque référence trouvée, identifie :
        1. Le numéro de la circulaire référencée (format YYYY-NN)
        2. Le type de relation : MODIFIES, ABROGATES, REFERENCES, COMPLEMENTS, ou CONCERNS
        3. L'article concerné si applicable
        4. La citation exacte du texte justifiant cette relation
        
        Texte de la circulaire N° {source_number} :
        {document_text}"""
        
        try:
            response = client.chat.completions.create(
                model=self.llm_model,
                response_model=RelationshipExtractionResult,
                messages=[
                    {"role": "system", "content": "Tu es un expert juridique spécialisé dans la réglementation de la Banque Centrale de Tunisie."},
                    {"role": "user", "content": prompt}
                ],
                max_retries=3,
                temperature=0.3
            )
            
            relationships = []
            for rel in response.relationships:
                # Clean up target format (e.g. "2024-01")
                target = rel.target_circular.strip()
                if target != source_number:
                    relationships.append(ExtractedRelationship(
                        source_number=source_number,
                        target_number=target,
                        relationship_type=rel.relationship_type,
                        article=rel.article,
                        confidence=0.8,
                        extraction_method="llm"
                    ))
            return relationships
            
        except Exception:
            # Silently return empty list on failure, following the plan (robustness)
            return []

    def create_relationships(
        self,
        relationships: List[ExtractedRelationship],
    ) -> int:
        """
        Write extracted relationships to Neo4j.
        Returns count of relationships created.
        """
        count = 0
        
        queries = {
            "ABROGATES": CREATE_ABROGATES_REL,
            "MODIFIES": CREATE_MODIFIES_REL,
            "REFERENCES": CREATE_REFERENCES_REL,
            "COMPLEMENTS": CREATE_COMPLEMENTS_REL,
            "CONCERNS": CREATE_CONCERNS_REL
        }
        
        for rel in relationships:
            # Ensure target circular node exists in Neo4j first (idempotent MERGE)
            # This is critical so MATCH in the relationship query succeeds!
            self.neo4j_manager.execute_write(
                "MERGE (c:Circular {number: $number})",
                {"number": rel.target_number}
            )
            
            query = queries.get(rel.relationship_type)
            if query:
                params = {
                    "source_number": rel.source_number,
                    "target_number": rel.target_number
                }
                if rel.relationship_type == "MODIFIES":
                    params["article"] = rel.article or "all"
                    
                self.neo4j_manager.execute_write(query, params)
                count += 1
                
        return count

    def build_graph_for_document(
        self,
        circular: CircularNode,
        document_text: str,
        entities: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """
        Full graph construction pipeline for one document:
        1. Create/update Circular node
        2. Create Entity nodes + MENTIONS edges
        3. Extract relationships (regex first, then LLM)
        4. Deduplicate relationships (regex wins on conflict)
        5. Create relationship edges
        Returns summary dict.
        """
        # 1. Create Circular node
        self.create_circular_node(circular)
        
        # 2. Create Entities and MENTIONS edges
        self.create_entity_nodes(circular.number, entities)
        
        # 3. Extract relationships
        regex_rels = self.extract_relationships_regex(circular.number, document_text)
        llm_rels = self.extract_relationships_llm(circular.number, document_text)
        
        # 4. Deduplicate relationships: regex wins on conflict
        # Conflict definition: target is the same
        regex_targets = {r.target_number for r in regex_rels}
        
        final_rels = list(regex_rels)
        for lr in llm_rels:
            if lr.target_number not in regex_targets:
                final_rels.append(lr)
                
        # 5. Write to Neo4j
        created_count = self.create_relationships(final_rels)
        
        return {
            "circular_number": circular.number,
            "entities_linked": len(entities),
            "relationships_extracted": len(final_rels),
            "relationships_created": created_count,
            "regex_count": len(regex_rels),
            "llm_count": len(final_rels) - len(regex_rels)
        }

    def search_by_entities(
        self,
        entity_names: List[str],
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Find circulars mentioning given entities."""
        return self.neo4j_manager.execute_query(
            SEARCH_BY_ENTITIES,
            {"entity_names": entity_names, "limit": limit}
        )

    def get_connected_chunks(
        self,
        circular_numbers: List[str],
        max_hops: int = 2,
    ) -> List[Dict[str, Any]]:
        """
        Given a list of circular numbers, perform 2-hop traversal
        and return connected circular data as a chunk-compatible list.
        """
        results = self.neo4j_manager.execute_query(
            TWO_HOP_TRAVERSAL,
            {"start_numbers": circular_numbers}
        )
        
        all_numbers = set(circular_numbers)
        for r in results:
            if r.get("number"):
                all_numbers.add(r["number"])
                
        if not all_numbers:
            return []
            
        # Fetch chunks from ChromaDB
        import chromadb
        chroma_host = os.getenv("CHROMA_HOST", "localhost")
        chroma_port = int(os.getenv("CHROMA_PORT", "8001"))
        
        client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
        collection = client.get_or_create_collection("kusor_documents")
        
        numbers_list = list(all_numbers)
        if len(numbers_list) == 1:
            where_clause = {"circular_number": numbers_list[0]}
        else:
            where_clause = {"circular_number": {"$in": numbers_list}}
            
        chroma_results = collection.get(where=where_clause)
        
        chunks = []
        if chroma_results and chroma_results.get("documents"):
            for i in range(len(chroma_results["ids"])):
                metadata = chroma_results["metadatas"][i]
                chunks.append({
                    "content": chroma_results["documents"][i],
                    "document_id": metadata.get("document_id"),
                    "chunk_index": metadata.get("chunk_index"),
                    "page_number": metadata.get("page_number"),
                    "source_filename": metadata.get("source_filename"),
                    "circular_number": metadata.get("circular_number"),
                    "score": 1.0,
                    "retrieval_method": "graph"
                })
                
        return chunks

    def get_subgraph(
        self,
        circular_number: str,
        max_hops: int = 2,
    ) -> Dict[str, Any]:
        """
        Return subgraph centered on a circular for visualization.
        Returns: {nodes: [...], edges: [...]}
        """
        try:
            results = self.neo4j_manager.execute_query(
                SUBGRAPH_BY_CIRCULAR,
                {"number": circular_number, "max_hops": max_hops}
            )
        except Exception:
            # Fallback in case APOC is not available
            fallback_query = """
            MATCH (c:Circular {number: $number})
            OPTIONAL MATCH path = (c)-[*1..2]-(related)
            RETURN nodes(path) AS nodes, relationships(path) AS relationships
            """
            results = self.neo4j_manager.execute_query(
                fallback_query,
                {"number": circular_number}
            )
            
        nodes_dict = {}
        edges_list = []
        
        for record in results:
            nodes = record.get("nodes", [])
            relationships = record.get("relationships", [])
            
            if not isinstance(nodes, list):
                nodes = [nodes] if nodes else []
            if not isinstance(relationships, list):
                relationships = [relationships] if relationships else []
                
            for node in nodes:
                if node is None:
                    continue
                props = dict(node.items())
                node_id = props.get("number") or props.get("name") or getattr(node, "element_id", str(node.id))
                node_label = props.get("number") or props.get("name") or node_id
                node_type = list(node.labels)[0] if node.labels else "Circular"
                
                nodes_dict[node_id] = {
                    "id": node_id,
                    "label": node_label,
                    "type": node_type,
                    "properties": props
                }
                
            for rel in relationships:
                if rel is None:
                    continue
                start_node = rel.start_node
                end_node = rel.end_node
                
                start_props = dict(start_node.items())
                end_props = dict(end_node.items())
                
                start_id = start_props.get("number") or start_props.get("name") or getattr(start_node, "element_id", str(start_node.id))
                end_id = end_props.get("number") or end_props.get("name") or getattr(end_node, "element_id", str(end_node.id))
                
                edge = {
                    "source": start_id,
                    "target": end_id,
                    "type": rel.type,
                    "properties": dict(rel.items())
                }
                edge_key = f"{start_id}->{end_id}:{rel.type}"
                edges_list.append((edge_key, edge))
                
        seen_edges = set()
        deduped_edges = []
        for key, edge in edges_list:
            if key not in seen_edges:
                seen_edges.add(key)
                deduped_edges.append(edge)
                
        return {
            "nodes": list(nodes_dict.values()),
            "edges": deduped_edges
        }
