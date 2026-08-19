import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { GraphData, GraphNode, GraphEdge, ClusterData, ClusterNode, ClusterEdge } from '../../core/models/graph.model';
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
  private router = inject(Router);

  // Raw API graph data
  rawGraphData = signal<GraphData>({ nodes: [], edges: [] });
  rawOverviewData = signal<ClusterData>({ clusters: [], clusterEdges: [] });
  isLoading = signal<boolean>(true);
  searchQuery = '';
  errorMessage = signal<string | null>(null);

  // Hierarchical view states
  viewLevel = signal<'overview' | 'detail'>('overview');
  selectedCluster = signal<string | null>(null);

  // Popular BCT Presets
  presets = [
    { id: '2018-16', label: '2018-16 (Réglementation Générale)' },
    { id: '2018-12', label: '2018-12 (Supervision Bancaire)' },
    { id: '2018-09', label: '2018-09 (Établissements Financiers)' },
    { id: '2018-01', label: '2018-01 (Ratio & Risques)' }
  ];

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

  // Computed nodes for ngx-graph with explicit dimensions based on node type
  nodes = computed(() => {
    if (this.viewLevel() === 'overview') {
      return this.rawOverviewData().clusters.map(cluster => {
        // Size scale based on circularCount
        const size = Math.min(100, Math.max(64, 50 + cluster.circularCount * 2));
        return {
          id: cluster.id,
          label: cluster.label,
          dimension: {
            width: size,
            height: size
          },
          data: {
            type: 'Cluster',
            circularCount: cluster.circularCount,
            entityCount: cluster.entityCount
          }
        };
      });
    } else {
      return this.rawGraphData().nodes.map(node => {
        const size = node.type === 'Circular' ? 48 : 36;
        return {
          id: node.id,
          label: node.label,
          dimension: {
            width: size,
            height: size
          },
          data: {
            type: node.type,
            properties: node.properties
          }
        };
      });
    }
  });

  // Computed links for ngx-graph, filtered by relationship types
  links = computed(() => {
    if (this.viewLevel() === 'overview') {
      return this.rawOverviewData().clusterEdges.map((edge, idx) => ({
        id: `cluster-edge-${idx}`,
        source: edge.source,
        target: edge.target,
        label: `${edge.type} (${edge.count})`,
        data: {
          type: edge.type,
          count: edge.count
        }
      }));
    } else {
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
    }
  });

  ngOnInit(): void {
    this.loadOverview();
  }

  loadOverview(): void {
    this.isLoading.set(true);
    this.errorMessage.set(null);
    this.selectedNode.set(null);
    this.selectedCluster.set(null);
    this.viewLevel.set('overview');

    this.apiService.getGraphOverview().subscribe({
      next: (data) => {
        this.rawOverviewData.set(data);
        this.isLoading.set(false);
      },
      error: (err) => {
        console.error('Error fetching graph overview', err);
        this.errorMessage.set("Impossible de charger la vue d'ensemble du graphe.");
        this.isLoading.set(false);
      }
    });
  }

  drillIntoCluster(year: string): void {
    this.isLoading.set(true);
    this.errorMessage.set(null);
    this.selectedNode.set(null);
    this.selectedCluster.set(year);
    this.viewLevel.set('detail');

    this.apiService.getClusterSubgraph(year).subscribe({
      next: (data) => {
        this.rawGraphData.set(data);
        this.isLoading.set(false);
      },
      error: (err) => {
        console.error('Error fetching cluster subgraph', err);
        this.errorMessage.set(`Impossible de charger le graphe pour l'année ${year}.`);
        this.isLoading.set(false);
      }
    });
  }

  loadGraph(circular?: string): void {
    this.isLoading.set(true);
    this.errorMessage.set(null);
    this.selectedNode.set(null);

    this.apiService.getSubgraph(circular).subscribe({
      next: (data) => {
        this.rawGraphData.set(data);
        if (circular) {
          const parts = circular.split('-');
          const year = parts[0];
          if (year && year.length === 4 && !isNaN(Number(year))) {
            this.selectedCluster.set(year);
          } else {
            this.selectedCluster.set('Recherche');
          }
          this.viewLevel.set('detail');
        }
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
      this.loadOverview();
    }
  }

  clearSearch(): void {
    this.searchQuery = '';
    this.loadOverview();
  }

  onNodeSelect(node: any): void {
    if (this.viewLevel() === 'overview') {
      this.drillIntoCluster(node.id);
    } else {
      const foundNode = this.rawGraphData().nodes.find(n => n.id === node.id);
      if (foundNode) {
        this.selectedNode.set(foundNode);
      }
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
    if (type === 'Cluster') {
      return '#6366f1'; // Indigo for clusters
    }
    return type === 'Circular' ? '#4f46e5' : '#fbbf24';
  }

  getEdgeColor(type: string): string {
    // Check if it has a count suffix e.g., "MODIFIES (3)"
    const cleanType = type.split(' ')[0].toUpperCase();
    switch (cleanType) {
      case 'MODIFIES': return '#f97316';
      case 'ABROGATES': return '#ef4444';
      case 'REFERENCES': return '#3b82f6';
      case 'COMPLEMENTS': return '#10b981';
      case 'CONCERNS': return '#a855f7';
      case 'MENTIONS': return '#64748b';
      default: return '#94a3b8';
    }
  }

  selectPreset(presetId: string): void {
    this.searchQuery = presetId;
    this.loadGraph(presetId);
  }

  askInChat(circularNumber: string): void {
    this.router.navigate(['/chat'], { queryParams: { q: `Que dit la circulaire BCT ${circularNumber} et quelles sont ses obligations principales ?` } });
  }

  viewImpact(circularNumber: string): void {
    this.router.navigate(['/impact-viewer'], { queryParams: { circularId: circularNumber } });
  }
}
