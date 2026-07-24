export interface Neo4jStats {
  circular_nodes: number;
  entity_nodes: number;
  relationships: number;
}

export interface ChromaStats {
  count: number;
}

export interface AdminStats {
  document_count: number;
  circular_count: number;
  chunk_count: number;
  last_sync_at: string;
  neo4j_stats: Neo4jStats;
  chroma_stats: ChromaStats;
}

export interface SyncResult {
  total_found: number;
  new_count: number;
  ingested: number;
  errors: string[];
  message: string;
}
