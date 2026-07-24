export interface GraphNode {
  id: string;
  label: string;
  type: 'Circular' | 'Entity';
  properties: Record<string, any>;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
  properties?: Record<string, any>;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface ClusterNode {
  id: string;
  label: string;
  circularCount: number;
  entityCount: number;
}

export interface ClusterEdge {
  source: string;
  target: string;
  type: string;
  count: number;
}

export interface ClusterData {
  clusters: ClusterNode[];
  clusterEdges: ClusterEdge[];
}

export interface ClusterSubgraphResponse extends GraphData {
  clusterLabel: string;
}
