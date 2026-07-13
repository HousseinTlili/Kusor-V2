import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { GraphData, GraphNode, GraphEdge } from '../../core/models/graph.model';
import { LoadingSpinnerComponent } from '../../shared/components/loading-spinner/loading-spinner.component';
import { NgxGraphModule } from '@swimlane/ngx-graph';

@Component({
  selector: 'app-graph',
  standalone: true,
  imports: [CommonModule, FormsModule, LoadingSpinnerComponent, NgxGraphModule],
  templateUrl: './graph.component.html',
  styleUrl: './graph.component.scss'
})
export class GraphComponent implements OnInit {
  private apiService = inject(ApiService);

  // Raw API graph data
  rawGraphData = signal<GraphData>({ nodes: [], edges: [] });
  isLoading = signal<boolean>(true);
  searchQuery = '';
  errorMessage = signal<string | null>(null);

  // Checkbox filters for relationship types
  relationshipFilters = signal({
    MODIFIES: true,
    ABROGATES: true,
    REFERENCES: true,
    COMPLEMENTS: true,
    CONCERNS: true,
    MENTIONS: true
  });

  // Selected Node Details drawer
  selectedNode = signal<GraphNode | null>(null);

  // Computed nodes for ngx-graph (we can map properties or modify if needed)
  nodes = computed(() => {
    return this.rawGraphData().nodes.map(node => ({
      id: node.id,
      label: node.label,
      data: {
        type: node.type,
        properties: node.properties
      }
    }));
  });

  // Computed links for ngx-graph, filtered by relationship types
  links = computed(() => {
    const filters = this.relationshipFilters();
    return this.rawGraphData().edges
      .filter(edge => {
        const type = edge.type.toUpperCase() as keyof typeof filters;
        return filters[type] === undefined ? true : filters[type];
      })
      .map((edge, idx) => ({
        id: `edge-${idx}`,
        source: edge.source,
        target: edge.target,
        label: edge.type,
        data: {
          type: edge.type
        }
      }));
  });

  ngOnInit(): void {
    this.loadGraph();
  }

  loadGraph(circular?: string): void {
    this.isLoading.set(true);
    this.errorMessage.set(null);
    this.selectedNode.set(null);

    this.apiService.getSubgraph(circular).subscribe({
      next: (data) => {
        this.rawGraphData.set(data);
        this.isLoading.set(false);
      },
      error: (err) => {
        console.error('Error fetching subgraph', err);
        this.errorMessage.set('Impossible de charger le graphe de connaissances.');
        this.isLoading.set(false);
      }
    });
  }

  searchCircular(): void {
    const query = this.searchQuery.trim();
    if (query) {
      this.loadGraph(query);
    } else {
      this.loadGraph();
    }
  }

  clearSearch(): void {
    this.searchQuery = '';
    this.loadGraph();
  }

  onNodeSelect(node: any): void {
    const foundNode = this.rawGraphData().nodes.find(n => n.id === node.id);
    if (foundNode) {
      this.selectedNode.set(foundNode);
    }
  }

  closeDetails(): void {
    this.selectedNode.set(null);
  }

  toggleFilter(key: 'MODIFIES' | 'ABROGATES' | 'REFERENCES' | 'COMPLEMENTS' | 'CONCERNS' | 'MENTIONS'): void {
    this.relationshipFilters.update(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  }

  getNodeColor(type: string): string {
    return type === 'Circular' ? '#4f46e5' : '#fbbf24';
  }

  getEdgeColor(type: string): string {
    switch (type.toUpperCase()) {
      case 'MODIFIES': return '#f97316';
      case 'ABROGATES': return '#ef4444';
      case 'REFERENCES': return '#3b82f6';
      case 'COMPLEMENTS': return '#10b981';
      case 'CONCERNS': return '#a855f7';
      case 'MENTIONS': return '#64748b';
      default: return '#94a3b8';
    }
  }
}
