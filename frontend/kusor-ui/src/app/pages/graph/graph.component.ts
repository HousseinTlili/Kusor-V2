import { Component, inject, OnInit, AfterViewInit, signal, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/services/api.service';
import { ThemeService } from '../../core/services/theme.service';

declare var vis: any;

@Component({
  selector: 'app-graph',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="p-6 md:p-8 max-w-7xl mx-auto space-y-8">
      
      <!-- Title Banner -->
      <div class="glass-card p-6 md:p-8 relative overflow-hidden">
        <div class="space-y-1 z-10 relative">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#E85D04]/10 text-[#E85D04] text-xs font-bold uppercase tracking-wider">
            <span>🌐 Base de Données Graphe Neo4j</span>
          </div>
          <h1 class="text-2xl md:text-3xl font-black text-[var(--text-primary)]">Graphe de Connaissances Réglementaires BCT</h1>
          <p class="text-sm text-[var(--text-muted)] max-w-2xl">
            Exploration visuelle et interactive du réseau des circulaires, obligations, articles et processus bancaires Attijari Bank.
          </p>
        </div>
      </div>

      <!-- Node Type Selection Filter Bar -->
      <div class="glass-card p-4 flex flex-wrap items-center justify-between gap-4 shadow-sm">
        <div class="flex items-center gap-2">
          <span class="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mr-2">Filtrer par type :</span>
          @for (lbl of ['Circular', 'Obligation', 'Process', 'ContractTemplate']; track lbl) {
            <button (click)="selectLabel(lbl)"
              [class]="selectedLabel() === lbl 
                ? 'px-4 py-2 rounded-xl brand-btn-primary text-xs shadow-sm font-bold' 
                : 'px-4 py-2 rounded-xl bg-[var(--bg-page-subtle)] text-[var(--text-secondary)] hover:text-[#E85D04] font-semibold text-xs border border-[var(--border-card)] transition-all'">
              {{ lbl }}
            </button>
          }
        </div>

        <div class="flex items-center gap-4 text-xs font-semibold text-[var(--text-muted)]">
          <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded-full bg-[#E85D04]"></span> Circulaire</span>
          <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded-full bg-[#DC2F02]"></span> Obligation</span>
          <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded-full bg-[#10B981]"></span> Processus</span>
          <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded-full bg-[#6366F1]"></span> Modèle Contrat</span>
        </div>
      </div>

      <!-- Interactive 2D Visual Network Canvas -->
      <div class="glass-card p-6 space-y-4 shadow-sm">
        <div class="flex justify-between items-center pb-2 border-b border-[var(--border-card)]">
          <h2 class="text-base font-bold text-[var(--text-primary)]">Visualisation du Réseau Graphique 2D</h2>
          <span class="text-xs text-[var(--text-muted)] font-medium">Glissez pour déplacer les nœuds • Molette pour zoomer • Cliquez pour inspecter</span>
        </div>

        <div #networkContainer class="w-full h-[520px] rounded-2xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)] relative">
          @if (loadingGraph()) {
            <div class="absolute inset-0 flex items-center justify-center text-[var(--text-muted)] text-sm font-semibold bg-[var(--bg-card)]/80 backdrop-blur-sm z-10">
              <svg class="animate-spin h-5 w-5 text-[#E85D04] mr-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>Chargement du sous-graphe Neo4j...</span>
            </div>
          }
        </div>
      </div>

      <!-- Selected Node Properties Drawer -->
      @if (selectedNode()) {
        <div class="glass-card p-6 space-y-3 border-l-4 border-[#E85D04] shadow-sm">
          <h3 class="text-sm font-bold text-[#E85D04] uppercase tracking-wider">Propriétés du Nœud Sélectionné</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
            @for (prop of getNodeProperties(); track prop.key) {
              <div class="p-3.5 rounded-xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)]">
                <div class="text-[10px] text-[var(--text-muted)] font-bold uppercase">{{ prop.key }}</div>
                <div class="text-[var(--text-primary)] font-semibold mt-1 break-words">{{ prop.value }}</div>
              </div>
            }
          </div>
        </div>
      }

      <!-- Numerical Summary Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="glass-card p-6 space-y-4 shadow-sm">
          <div class="flex items-center gap-3 pb-3 border-b border-[var(--border-card)]">
            <div class="p-2 rounded-xl bg-orange-50 dark:bg-orange-950/30 text-[#E85D04]">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
              </svg>
            </div>
            <h2 class="text-base font-bold text-[var(--text-primary)]">Répartition des Nœuds</h2>
          </div>

          <div class="space-y-2">
            @for (item of nodeStats(); track item.key) {
              <div class="flex justify-between p-3.5 rounded-xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)] text-xs">
                <span class="font-semibold text-[var(--text-secondary)]">{{ item.key }}</span>
                <span class="font-bold text-[#E85D04]">{{ item.value }}</span>
              </div>
            }
          </div>
        </div>

        <div class="glass-card p-6 space-y-4 shadow-sm">
          <div class="flex items-center gap-3 pb-3 border-b border-[var(--border-card)]">
            <div class="p-2 rounded-xl bg-indigo-50 dark:bg-indigo-950/30 text-indigo-600 dark:text-indigo-400">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/>
              </svg>
            </div>
            <h2 class="text-base font-bold text-[var(--text-primary)]">Répartition des Relations</h2>
          </div>

          <div class="space-y-2">
            @for (item of relStats(); track item.key) {
              <div class="flex justify-between p-3.5 rounded-xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)] text-xs">
                <span class="font-semibold text-[var(--text-secondary)]">{{ item.key }}</span>
                <span class="font-bold text-indigo-600 dark:text-indigo-400">{{ item.value }}</span>
              </div>
            }
          </div>
        </div>
      </div>
    </div>
  `
})
export class GraphComponent implements OnInit, AfterViewInit {
  api = inject(ApiService);
  theme = inject(ThemeService);

  @ViewChild('networkContainer') networkContainer!: ElementRef;

  nodeStats = signal<Array<{key: string; value: number}>>([]);
  relStats = signal<Array<{key: string; value: number}>>([]);
  selectedLabel = signal<string>('Circular');
  loadingGraph = signal<boolean>(false);
  selectedNode = signal<any>(null);

  private networkInstance: any;

  ngOnInit() {
    this.loadStats();
  }

  ngAfterViewInit() {
    this.renderVisualNetwork();
  }

  loadStats() {
    this.api.getGraphOverview().subscribe({
      next: (res) => {
        const nodes = Object.entries(res.node_counts || {}).map(([key, value]) => ({ key, value: value as number }));
        const rels = Object.entries(res.relationship_counts || {}).map(([key, value]) => ({ key, value: value as number }));
        this.nodeStats.set(nodes);
        this.relStats.set(rels);
      }
    });
  }

  selectLabel(label: string) {
    this.selectedLabel.set(label);
    this.renderVisualNetwork();
  }

  renderVisualNetwork() {
    this.loadingGraph.set(true);
    this.selectedNode.set(null);

    this.api.getGraphSubgraph(this.selectedLabel(), 50).subscribe({
      next: (res) => {
        this.loadingGraph.set(false);
        const records = res.records || [];
        this.buildVisNetwork(records);
      },
      error: () => this.loadingGraph.set(false)
    });
  }

  buildVisNetwork(records: any[]) {
    if (!this.networkContainer || typeof vis === 'undefined') return;

    const isDark = this.theme.isDark();
    const labelColor = isDark ? '#F8FAFC' : '#0F172A';
    const edgeColor = isDark ? '#94A3B8' : '#64748B';

    const nodesMap = new Map<string, any>();
    const edgesArray: any[] = [];

    const getColor = (labels: string[] = []) => {
      const main = labels[0] || '';
      if (main === 'Circular') return { background: '#E85D04', border: '#D95000' };
      if (main === 'Obligation') return { background: '#DC2F02', border: '#9D0208' };
      if (main === 'Process') return { background: '#10B981', border: '#059669' };
      if (main === 'ContractTemplate') return { background: '#6366F1', border: '#4F46E5' };
      return { background: '#F48C06', border: '#D95000' };
    };

    records.forEach((rec: any, idx: number) => {
      const nId = rec.n_id != null ? String(rec.n_id) : `n_${idx}`;
      const nProps = rec.n_props || {};
      const nLabels = rec.n_labels || [];
      const nTitle = nProps.title || nProps.name || nProps.circular_reference || nProps.reference || nProps.text || 'Nœud';

      if (!nodesMap.has(nId)) {
        nodesMap.set(nId, {
          id: nId,
          label: nTitle.length > 25 ? nTitle.slice(0, 22) + '...' : nTitle,
          color: getColor(nLabels),
          shape: 'dot',
          size: 20,
          font: { color: labelColor, size: 12, face: 'Inter' },
          properties: nProps,
        });
      }

      if (rec.m_id != null) {
        const mId = String(rec.m_id);
        const mProps = rec.m_props || {};
        const mLabels = rec.m_labels || [];
        const mTitle = mProps.title || mProps.name || mProps.circular_reference || mProps.reference || mProps.text || 'Nœud';

        if (!nodesMap.has(mId)) {
          nodesMap.set(mId, {
            id: mId,
            label: mTitle.length > 25 ? mTitle.slice(0, 22) + '...' : mTitle,
            color: getColor(mLabels),
            shape: 'dot',
            size: 16,
            font: { color: labelColor, size: 11, face: 'Inter' },
            properties: mProps,
          });
        }

        edgesArray.push({
          from: nId,
          to: mId,
          label: rec.rel_type || '',
          color: { color: '#E85D04', opacity: 0.6 },
          font: { color: edgeColor, size: 9, align: 'middle' },
          arrows: 'to',
        });
      }
    });

    const data = {
      nodes: Array.from(nodesMap.values()),
      edges: edgesArray,
    };

    const options = {
      nodes: {
        borderWidth: 2,
        shadow: true,
      },
      edges: {
        width: 1.5,
        smooth: { type: 'continuous' },
      },
      physics: {
        stabilization: false,
        barnesHut: {
          gravitationalConstant: -3000,
          springLength: 120,
        },
      },
      interaction: {
        hover: true,
        zoomView: true,
        dragView: true,
      },
    };

    if (this.networkInstance) {
      this.networkInstance.destroy();
    }

    this.networkInstance = new vis.Network(this.networkContainer.nativeElement, data, options);

    this.networkInstance.on('click', (params: any) => {
      if (params.nodes.length > 0) {
        const clickedId = String(params.nodes[0]);
        const selected = nodesMap.get(clickedId);
        if (selected) {
          this.selectedNode.set(selected);
        }
      } else {
        this.selectedNode.set(null);
      }
    });
  }

  getNodeProperties(): Array<{key: string; value: string}> {
    const node = this.selectedNode();
    if (!node || !node.properties) return [];
    return Object.entries(node.properties).map(([key, value]) => ({
      key,
      value: typeof value === 'object' ? JSON.stringify(value) : String(value),
    }));
  }
}
