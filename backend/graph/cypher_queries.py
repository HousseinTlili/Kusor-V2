"""All Cypher queries used by the GraphRAG module."""

# --- Node creation ---
CREATE_CIRCULAR_NODE: str = """
MERGE (c:Circular {number: $number})
SET c.id = $id,
    c.title = $title,
    c.date = $date,
    c.category = $category,
    c.url = $url,
    c.status = $status
RETURN c
"""

CREATE_ENTITY_NODE: str = """
MERGE (e:Entity {name: $name, type: $type})
RETURN e
"""

LINK_ENTITY_TO_CIRCULAR: str = """
MATCH (c:Circular {number: $circular_number})
MERGE (e:Entity {name: $entity_name, type: $entity_type})
MERGE (c)-[:MENTIONS]->(e)
"""

# --- Relationship creation ---
CREATE_ABROGATES_REL: str = """
MATCH (source:Circular {number: $source_number})
MATCH (target:Circular {number: $target_number})
MERGE (source)-[:ABROGATES]->(target)
SET target.status = 'ABROGATED'
"""

CREATE_MODIFIES_REL: str = """
MATCH (source:Circular {number: $source_number})
MATCH (target:Circular {number: $target_number})
MERGE (source)-[r:MODIFIES]->(target)
SET r.article = $article
"""

CREATE_REFERENCES_REL: str = """
MATCH (source:Circular {number: $source_number})
MATCH (target:Circular {number: $target_number})
MERGE (source)-[:REFERENCES]->(target)
"""

CREATE_COMPLEMENTS_REL: str = """
MATCH (source:Circular {number: $source_number})
MATCH (target:Circular {number: $target_number})
MERGE (source)-[:COMPLEMENTS]->(target)
"""

CREATE_CONCERNS_REL: str = """
MATCH (source:Circular {number: $source_number})
MATCH (target:Circular {number: $target_number})
MERGE (source)-[:CONCERNS]->(target)
"""

# --- Graph queries ---
GET_CIRCULAR_BY_NUMBER: str = """
MATCH (c:Circular {number: $number})
RETURN c
"""

GET_CIRCULAR_RELATIONS: str = """
MATCH (c:Circular {number: $number})-[r]->(related:Circular)
RETURN c, type(r) AS relationship, r, related
UNION
MATCH (c:Circular {number: $number})<-[r]-(related:Circular)
RETURN c, type(r) AS relationship, r, related
"""

GET_MODIFICATION_CHAIN: str = """
MATCH path = (c:Circular {number: $number})-[:MODIFIES|ABROGATES*1..5]->(target:Circular)
RETURN path
"""

SUBGRAPH_BY_CIRCULAR: str = """
MATCH (c:Circular {number: $number})
CALL apoc.path.subgraphAll(c, {maxLevel: $max_hops})
YIELD nodes, relationships
RETURN nodes, relationships
"""

SEARCH_BY_ENTITIES: str = """
UNWIND $entity_names AS ename
MATCH (e:Entity)
WHERE toLower(e.name) CONTAINS toLower(ename)
MATCH (e)<-[:MENTIONS]-(c:Circular)
RETURN DISTINCT c
LIMIT $limit
"""

SEARCH_BY_CIRCULAR_NUMBERS: str = """
UNWIND $numbers AS num
MATCH (c:Circular {number: num})-[r*0..2]-(related)
RETURN DISTINCT c, related, r
"""

TWO_HOP_TRAVERSAL: str = """
UNWIND $start_numbers AS num
MATCH (start:Circular {number: num})
MATCH path = (start)-[*1..2]-(connected:Circular)
RETURN DISTINCT connected.number AS number,
       connected.title AS title,
       connected.id AS id
"""

GET_ALL_CIRCULARS: str = """
MATCH (c:Circular)
RETURN c
ORDER BY c.date DESC
"""

GET_GRAPH_STATS: str = """
MATCH (c:Circular) WITH count(c) AS circulars
MATCH (e:Entity) WITH circulars, count(e) AS entities
MATCH ()-[r]->() WITH circulars, entities, count(r) AS relationships
RETURN circulars, entities, relationships
"""

# --- Subgraph for visualization ---
GET_SUBGRAPH_FOR_VIS: str = """
MATCH (c:Circular {number: $number})
OPTIONAL MATCH (c)-[r]-(related)
RETURN c, r, related
"""

FULLTEXT_SEARCH_CIRCULARS: str = """
MATCH (c:Circular)
WHERE toLower(c.title) CONTAINS toLower($query)
   OR c.number CONTAINS $query
RETURN c
LIMIT $limit
"""

# --- Hierarchical Graph queries ---
GET_OVERVIEW_CLUSTERS: str = """
MATCH (c:Circular)
WITH c,
     CASE 
       WHEN c.date IS NOT NULL AND size(c.date) >= 4 THEN substring(c.date, 0, 4)
       WHEN c.number =~ '.*(19\\\\d{2}|20\\\\d{2}).*' THEN apoc.text.regexGroups(c.number, '(19\\\\d{2}|20\\\\d{2})')[0][0]
       WHEN c.number =~ '.*\\\\b(\\\\d{2})-\\\\d+.*' THEN 
         CASE 
           WHEN toInteger(apoc.text.regexGroups(c.number, '\\\\b(\\\\d{2})-\\\\d+')[0][1]) > 50 THEN "19" + apoc.text.regexGroups(c.number, '\\\\b(\\\\d{2})-\\\\d+')[0][1]
           ELSE "20" + apoc.text.regexGroups(c.number, '\\\\b(\\\\d{2})-\\\\d+')[0][1]
         END
       ELSE 'Autre'
     END AS year
OPTIONAL MATCH (c)-[:MENTIONS]->(e:Entity)
WITH year, count(DISTINCT c) AS circularCount, count(DISTINCT e) AS entityCount
RETURN year AS id, year AS label, circularCount, entityCount
ORDER BY year DESC
"""

GET_OVERVIEW_EDGES: str = """
MATCH (c1:Circular)-[r]->(c2:Circular)
WITH c1, c2, r,
     CASE 
       WHEN c1.date IS NOT NULL AND size(c1.date) >= 4 THEN substring(c1.date, 0, 4)
       WHEN c1.number =~ '.*(19\\\\d{2}|20\\\\d{2}).*' THEN apoc.text.regexGroups(c1.number, '(19\\\\d{2}|20\\\\d{2})')[0][0]
       WHEN c1.number =~ '.*\\\\b(\\\\d{2})-\\\\d+.*' THEN 
         CASE 
           WHEN toInteger(apoc.text.regexGroups(c1.number, '\\\\b(\\\\d{2})-\\\\d+')[0][1]) > 50 THEN "19" + apoc.text.regexGroups(c1.number, '\\\\b(\\\\d{2})-\\\\d+')[0][1]
           ELSE "20" + apoc.text.regexGroups(c1.number, '\\\\b(\\\\d{2})-\\\\d+')[0][1]
         END
       ELSE 'Autre'
     END AS y1,
     CASE 
       WHEN c2.date IS NOT NULL AND size(c2.date) >= 4 THEN substring(c2.date, 0, 4)
       WHEN c2.number =~ '.*(19\\\\d{2}|20\\\\d{2}).*' THEN apoc.text.regexGroups(c2.number, '(19\\\\d{2}|20\\\\d{2})')[0][0]
       WHEN c2.number =~ '.*\\\\b(\\\\d{2})-\\\\d+.*' THEN 
         CASE 
           WHEN toInteger(apoc.text.regexGroups(c2.number, '\\\\b(\\\\d{2})-\\\\d+')[0][1]) > 50 THEN "19" + apoc.text.regexGroups(c2.number, '\\\\b(\\\\d{2})-\\\\d+')[0][1]
           ELSE "20" + apoc.text.regexGroups(c2.number, '\\\\b(\\\\d{2})-\\\\d+')[0][1]
         END
       ELSE 'Autre'
     END AS y2
WHERE y1 <> y2
RETURN y1 AS source, y2 AS target, type(r) AS type, count(*) AS count
"""

GET_CLUSTER_SUBGRAPH: str = """
MATCH (c:Circular)
WHERE (c.date IS NOT NULL AND size(c.date) >= 4 AND substring(c.date, 0, 4) = $year)
   OR (c.date IS NULL AND c.number =~ '.*(19\\\\d{2}|20\\\\d{2}).*' AND apoc.text.regexGroups(c.number, '(19\\\\d{2}|20\\\\d{2})')[0][0] = $year)
   OR (c.date IS NULL AND NOT c.number =~ '.*(19\\\\d{2}|20\\\\d{2}).*' AND c.number =~ '.*\\\\b(\\\\d{2})-\\\\d+.*' AND 
       ((toInteger(apoc.text.regexGroups(c.number, '\\\\b(\\\\d{2})-\\\\d+')[0][1]) > 50 AND "19" + apoc.text.regexGroups(c.number, '\\\\b(\\\\d{2})-\\\\d+')[0][1] = $year) OR
        (toInteger(apoc.text.regexGroups(c.number, '\\\\b(\\\\d{2})-\\\\d+')[0][1]) <= 50 AND "20" + apoc.text.regexGroups(c.number, '\\\\b(\\\\d{2})-\\\\d+')[0][1] = $year)))
   OR ($year = 'Autre' AND c.date IS NULL AND NOT c.number =~ '.*(19\\\\d{2}|20\\\\d{2}).*' AND NOT c.number =~ '.*\\\\b(\\\\d{2})-\\\\d+.*')
WITH c
OPTIONAL MATCH (c)-[r]-(related)
RETURN c, r, related
"""
