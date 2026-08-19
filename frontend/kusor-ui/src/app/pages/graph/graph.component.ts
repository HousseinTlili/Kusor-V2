import { Component, inject, OnInit, AfterViewInit, signal, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { ThemeService } from '../../core/services/theme.service';

declare var vis: any;

@Component({
  selector: 'app-graph',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
      
      <!-- Title Banner -->
      <div class="glass-card p-6 md:p-8 relative overflow-hidden">
        <div class="space-y-1 z-10 relative">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#E85D04]/10 text-[#E85D04] text-xs font-bold uppercase tracking-wider">
            <span>🌐 Base de Données Graphe Neo4j</span>
          </div>
          <h1 class="text-2xl md:text-3xl font-black text-[var(--text-primary)]">Graphe de Connaissances Réglementaires BCT</h1>
          <p class="text-sm text-[var(--text-muted)] max-w-3xl">
            Exploration visuelle structurée du réseau des circulaires de la Banque Centrale de Tunisie, obligations de conformité, processus bancaires et modèles contractuels.
          </p>
        </div>
      </div>

      <!-- Domain Focus Bar (Presets) -->
      <div class="glass-card p-4 flex flex-wrap items-center justify-between gap-3 text-xs shadow-sm">
        <div class="flex items-center flex-wrap gap-2">
          <span class="font-bold text-[var(--text-muted)] uppercase tracking-wider text-[10px] mr-1">Vues Thématiques :</span>
          <button (click)="selectFocus('all')" 
            [class]="activeFocus() === 'all' ? 'px-3.5 py-1.5 rounded-xl brand-btn-primary font-bold shadow-sm' : 'px-3.5 py-1.5 rounded-xl bg-[var(--bg-page-subtle)] text-[var(--text-secondary)] hover:text-[#E85D04] font-semibold border border-[var(--border-card)] transition-all'">
            🌐 Écosystème Global (Tous Nœuds)
          </button>
          <button (click)="selectFocus('kyc')"
            [class]="activeFocus() === 'kyc' ? 'px-3.5 py-1.5 rounded-xl bg-orange-500 text-white font-bold shadow-sm' : 'px-3.5 py-1.5 rounded-xl bg-orange-500/10 text-[#E85D04] hover:bg-orange-500/20 font-semibold border border-[#E85D04]/30 transition-all'">
            🛡️ Focus AML / KYC (Circ. 2018-09)
          </button>
          <button (click)="selectFocus('credit')"
            [class]="activeFocus() === 'credit' ? 'px-3.5 py-1.5 rounded-xl bg-emerald-600 text-white font-bold shadow-sm' : 'px-3.5 py-1.5 rounded-xl bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 font-semibold border border-emerald-500/30 transition-all'">
            💳 Focus Crédit & Endettement (Circ. 2016-01)
          </button>
          <button (click)="selectFocus('temporal')"
            [class]="activeFocus() === 'temporal' ? 'px-3.5 py-1.5 rounded-xl bg-rose-600 text-white font-bold shadow-sm' : 'px-3.5 py-1.5 rounded-xl bg-rose-500/10 text-rose-500 hover:bg-rose-500/20 font-semibold border border-rose-500/30 transition-all'">
            ⏳ Relations Temporelles (Abrogations & Amendements)
          </button>
        </div>

        <div class="flex items-center gap-3 text-xs font-semibold">
          <span class="text-[var(--text-muted)]">Nœuds visibles : <strong class="text-[#E85D04]">{{ totalNodesCount() }}</strong></span>
          <span class="text-[var(--text-muted)]">Relations : <strong class="text-emerald-500">{{ totalEdgesCount() }}</strong></span>
        </div>
      </div>

      <!-- Controls & Search Toolbar -->
      <div class="glass-card p-4 flex flex-wrap items-center justify-between gap-4 text-xs shadow-sm">
        
        <!-- Search Bar -->
        <div class="relative flex-1 min-w-[240px] max-w-md">
          <input type="text" [(ngModel)]="searchQuery" (input)="onSearchChange()" placeholder="🔍 Rechercher (ex: 2018-09, Endettement, PEP, Sanction...)"
            class="w-full pl-9 pr-4 py-2 rounded-xl bg-[var(--bg-input)] border border-[var(--border-input)] text-[var(--text-primary)] text-xs focus:outline-none focus:border-[#E85D04] transition-all" />
          <svg class="w-4 h-4 text-[var(--text-muted)] absolute left-3 top-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
          </svg>
        </div>

        <!-- Graph Layout & Physics Controls -->
        <div class="flex items-center flex-wrap gap-2">
          <!-- Layout Switcher -->
          <div class="flex rounded-xl bg-[var(--bg-input)] p-1 border border-[var(--border-input)]">
            <button (click)="toggleLayout('physics')"
              [class]="layoutMode() === 'physics' ? 'px-3 py-1 rounded-lg bg-[var(--bg-card)] text-[#E85D04] font-bold shadow-xs' : 'px-3 py-1 text-[var(--text-muted)] hover:text-[var(--text-primary)] font-medium'">
              🕸️ Réseau Dynamique
            </button>
            <button (click)="toggleLayout('hierarchical')"
              [class]="layoutMode() === 'hierarchical' ? 'px-3 py-1 rounded-lg bg-[var(--bg-card)] text-[#E85D04] font-bold shadow-xs' : 'px-3 py-1 text-[var(--text-muted)] hover:text-[var(--text-primary)] font-medium'">
              🌳 Arbre Hiérarchique
            </button>
          </div>

          <!-- Freeze Physics Button -->
          <button (click)="togglePhysics()" 
            class="px-3 py-1.5 rounded-xl bg-[var(--bg-page-subtle)] hover:bg-[var(--bg-input)] text-[var(--text-secondary)] font-semibold border border-[var(--border-card)] transition-all">
            {{ isPhysicsFrozen() ? '▶️ Activer Physique' : '⏸️ Figer Nœuds' }}
          </button>

          <!-- Fit View Button -->
          <button (click)="fitNetwork()" 
            class="px-3 py-1.5 rounded-xl bg-[var(--bg-page-subtle)] hover:bg-[var(--bg-input)] text-[var(--text-secondary)] font-semibold border border-[var(--border-card)] transition-all">
            🎯 Recentrer
          </button>
        </div>

      </div>

      <!-- Legend Bar -->
      <div class="flex flex-wrap items-center justify-between px-2 text-xs font-semibold text-[var(--text-muted)]">
        <div class="flex items-center flex-wrap gap-4">
          <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded-full bg-[#E85D04]"></span> <strong>Circulaire BCT</strong></span>
          <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded-full bg-[#DC2F02]"></span> <strong>Obligation Légale</strong></span>
          <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded-full bg-[#10B981]"></span> <strong>Processus Métier</strong></span>
          <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded-full bg-[#6366F1]"></span> <strong>Modèle Contractuel</strong></span>
        </div>
        <div class="flex items-center gap-3 text-[11px]">
          <span class="text-[#E85D04] font-mono">── MANDATES ➔</span>
          <span class="text-rose-500 font-mono">╌╌ ABROGATES ➔</span>
          <span class="text-emerald-500 font-mono">── APPLIES_TO ➔</span>
        </div>
      </div>

      <!-- Interactive 2D Visual Network Canvas -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        <!-- Network Canvas Area (Full or 8 cols if node selected) -->
        <div [ngClass]="selectedNode() ? 'lg:col-span-8' : 'lg:col-span-12'" class="transition-all duration-300">
          <div class="glass-card p-4 space-y-2 shadow-sm">
            <div #networkContainer class="w-full h-[560px] rounded-2xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)] relative overflow-hidden">
              @if (loadingGraph()) {
                <div class="absolute inset-0 flex items-center justify-center text-[var(--text-muted)] text-sm font-semibold bg-[var(--bg-card)]/80 backdrop-blur-sm z-10">
                  <svg class="animate-spin h-6 w-6 text-[#E85D04] mr-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Optimisation et rendu du graphe de connaissances...</span>
                </div>
              }
            </div>
            <div class="text-[11px] text-[var(--text-muted)] flex items-center justify-between px-2 pt-1">
              <span>💡 Cliquez sur un nœud pour inspecter ses relations directes et ses propriétés réglementaires.</span>
              <span>Double-clic pour zoomer</span>
            </div>
          </div>
        </div>

        <!-- Node Inspector Drawer (Right Column) -->
        @if (selectedNode(); as node) {
          <div class="lg:col-span-4 space-y-4">
            <div class="glass-card p-6 space-y-4 border-l-4 border-[#E85D04] shadow-sm animate-fadeIn">
              
              <div class="flex items-start justify-between gap-2 pb-3 border-b border-[var(--border-card)]">
                <div>
                  <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider"
                    [ngClass]="getNodeBadgeClass(node.labels)">
                    {{ node.labels[0] || 'Nœud' }}
                  </span>
                  <h3 class="text-base font-black text-[var(--text-primary)] mt-1.5 leading-snug">{{ node.fullTitle }}</h3>
                </div>
                <button (click)="selectedNode.set(null); resetHighlight()" class="text-[var(--text-muted)] hover:text-rose-500 font-bold p-1 text-sm">✕</button>
              </div>

              <!-- Node Properties Table -->
              <div class="space-y-2">
                <div class="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Propriétés Réglementaires :</div>
                <div class="space-y-1.5 text-xs">
                  @for (prop of getNodeProperties(); track prop.key) {
                    <div class="p-2.5 rounded-xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)] flex flex-col gap-0.5">
                      <span class="text-[10px] text-[var(--text-muted)] font-bold uppercase">{{ prop.key }}</span>
                      <span class="text-[var(--text-primary)] font-semibold break-words">{{ prop.value }}</span>
                    </div>
                  }
                </div>
              </div>

              <!-- Connected Direct Neighbors -->
              @if (nodeNeighbors().length > 0) {
                <div class="space-y-2 pt-2 border-t border-[var(--border-card)]">
                  <div class="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Relations Directes ({{ nodeNeighbors().length }}) :</div>
                  <div class="space-y-1.5">
                    @for (neighbor of nodeNeighbors(); track neighbor.id) {
                      <div (click)="inspectNeighbor(neighbor.id)"
                        class="p-2.5 rounded-xl bg-[var(--bg-input)] hover:bg-[var(--bg-card)] border border-[var(--border-input)] cursor-pointer transition-all flex items-center justify-between text-xs group">
                        <div class="flex items-center gap-2 truncate">
                          <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[var(--bg-page-subtle)] text-[#E85D04] font-bold">{{ neighbor.rel }}</span>
                          <span class="font-semibold text-[var(--text-primary)] group-hover:text-[#E85D04] truncate">{{ neighbor.title }}</span>
                        </div>
                        <span class="text-[10px] text-[var(--text-muted)] group-hover:translate-x-0.5 transition-transform">➔</span>
                      </div>
                    }
                  </div>
                </div>
              }

            </div>
          </div>
        }

      </div>

      <!-- Graph Analytics Overview Footer -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="glass-card p-6 space-y-4 shadow-sm">
          <div class="flex items-center gap-3 pb-3 border-b border-[var(--border-card)]">
            <div class="p-2 rounded-xl bg-orange-50 dark:bg-orange-950/30 text-[#E85D04]">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
              </svg>
            </div>
            <h2 class="text-base font-bold text-[var(--text-primary)]">Distribution des Typologies de Nœuds</h2>
          </div>

          <div class="grid grid-cols-2 gap-3">
            @for (item of nodeStats(); track item.key) {
              <div class="p-3.5 rounded-xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)] text-xs flex items-center justify-between">
                <span class="font-semibold text-[var(--text-secondary)]">{{ item.key }}</span>
                <span class="font-black text-sm text-[#E85D04]">{{ item.value }}</span>
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
            <h2 class="text-base font-bold text-[var(--text-primary)]">Typologies des Liens Réglementaires</h2>
          </div>

          <div class="grid grid-cols-2 gap-3">
            @for (item of relStats(); track item.key) {
              <div class="p-3.5 rounded-xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)] text-xs flex items-center justify-between">
                <span class="font-semibold text-[var(--text-secondary)]">{{ item.key }}</span>
                <span class="font-black text-sm text-indigo-500">{{ item.value }}</span>
              </div>
            }
          </div>
        </div>
      </div>

    </div>
  `,
  styles: [`
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .animate-fadeIn {
      animation: fadeIn 0.25s ease-out forwards;
    }
  `]
})
export class GraphComponent implements OnInit, AfterViewInit {
  api = inject(ApiService);
  theme = inject(ThemeService);

  @ViewChild('networkContainer') networkContainer!: ElementRef;

  nodeStats = signal<Array<{key: string; value: number}>>([]);
  relStats = signal<Array<{key: string; value: number}>>([]);
  activeFocus = signal<string>('all');
  layoutMode = signal<'physics' | 'hierarchical'>('physics');
  isPhysicsFrozen = signal<boolean>(false);
  loadingGraph = signal<boolean>(false);
  selectedNode = signal<any>(null);
  nodeNeighbors = signal<Array<{id: string; title: string; rel: string}>>([]);
  searchQuery = '';

  totalNodesCount = signal<number>(0);
  totalEdgesCount = signal<number>(0);

  private networkInstance: any;
  private rawRecords: any[] = [];
  private nodesDataSet: any;
  private edgesDataSet: any;
  private nodesMap = new Map<string, any>();

  ngOnInit() {
    this.loadStats();
  }

  ngAfterViewInit() {
    this.fetchGraphData();
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

  selectFocus(focus: string) {
    this.activeFocus.set(focus);
    this.fetchGraphData();
  }

  toggleLayout(mode: 'physics' | 'hierarchical') {
    this.layoutMode.set(mode);
    this.buildVisNetwork(this.rawRecords);
  }

  togglePhysics() {
    const nextState = !this.isPhysicsFrozen();
    this.isPhysicsFrozen.set(nextState);
    if (this.networkInstance) {
      this.networkInstance.setOptions({
        physics: { enabled: !nextState }
      });
    }
  }

  fitNetwork() {
    if (this.networkInstance) {
      this.networkInstance.fit({ animation: { duration: 500, easingFunction: 'easeInOutQuad' } });
    }
  }

  fetchGraphData() {
    this.loadingGraph.set(true);
    this.selectedNode.set(null);
    this.nodeNeighbors.set([]);

    let label = 'ALL';
    if (this.activeFocus() === 'kyc') label = 'Circular';
    else if (this.activeFocus() === 'credit') label = 'Circular';

    this.api.getGraphSubgraph(label, 100).subscribe({
      next: (res) => {
        this.loadingGraph.set(false);
        this.rawRecords = res.records || [];
        this.buildVisNetwork(this.rawRecords);
      },
      error: () => this.loadingGraph.set(false)
    });
  }

  buildVisNetwork(records: any[]) {
    if (!this.networkContainer || typeof vis === 'undefined') return;

    const isDark = this.theme.isDark();
    const labelColor = isDark ? '#F8FAFC' : '#0F172A';

    this.nodesMap.clear();
    const edgesArray: any[] = [];

    const getNodeConfig = (labels: string[] = [], props: any = {}) => {
      const main = labels[0] || '';
      if (main === 'Circular') {
        const isAbrogated = props.status === 'ABROGATED';
        return {
          background: isAbrogated ? '#64748B' : '#E85D04',
          border: isAbrogated ? '#475569' : '#D95000',
          size: 26,
          shape: 'dot'
        };
      }
      if (main === 'Obligation') {
        const isCritical = props.severity === 'CRITICAL';
        return {
          background: isCritical ? '#DC2F02' : '#F48C06',
          border: isCritical ? '#9D0208' : '#D95000',
          size: 20,
          shape: 'diamond'
        };
      }
      if (main === 'Process') {
        return {
          background: '#10B981',
          border: '#059669',
          size: 18,
          shape: 'square'
        };
      }
      if (main === 'ContractTemplate') {
        return {
          background: '#6366F1',
          border: '#4F46E5',
          size: 18,
          shape: 'triangle'
        };
      }
      return { background: '#F48C06', border: '#D95000', size: 16, shape: 'dot' };
    };

    records.forEach((rec: any, idx: number) => {
      const nId = rec.n_id != null ? String(rec.n_id) : `n_${idx}`;
      const nProps = rec.n_props || {};
      const nLabels = rec.n_labels || ['Node'];
      const nTitle = nProps.number ? `BCT N° ${nProps.number}` : (nProps.title || nProps.name || nProps.code || 'Nœud');
      const nFull = nProps.title ? `${nTitle} — ${nProps.title}` : (nProps.name || nTitle);

      const nCfg = getNodeConfig(nLabels, nProps);

      if (!this.nodesMap.has(nId)) {
        this.nodesMap.set(nId, {
          id: nId,
          label: nTitle,
          fullTitle: nFull,
          labels: nLabels,
          color: { background: nCfg.background, border: nCfg.border, highlight: { background: '#FF9E00', border: '#FFFFFF' } },
          shape: nCfg.shape,
          size: nCfg.size,
          font: { color: labelColor, size: 12, face: 'Inter', bold: true },
          properties: nProps,
          originalColor: nCfg.background,
        });
      }

      if (rec.m_id != null) {
        const mId = String(rec.m_id);
        const mProps = rec.m_props || {};
        const mLabels = rec.m_labels || ['Node'];
        const mTitle = mProps.number ? `BCT N° ${mProps.number}` : (mProps.name || mProps.code || mProps.title || 'Nœud');
        const mFull = mProps.title ? `${mTitle} — ${mProps.title}` : (mProps.name || mTitle);

        const mCfg = getNodeConfig(mLabels, mProps);

        if (!this.nodesMap.has(mId)) {
          this.nodesMap.set(mId, {
            id: mId,
            label: mTitle,
            fullTitle: mFull,
            labels: mLabels,
            color: { background: mCfg.background, border: mCfg.border, highlight: { background: '#FF9E00', border: '#FFFFFF' } },
            shape: mCfg.shape,
            size: mCfg.size,
            font: { color: labelColor, size: 11, face: 'Inter' },
            properties: mProps,
            originalColor: mCfg.background,
          });
        }

        const relType = rec.rel_type || 'RELATES_TO';
        let edgeColor = '#E85D04';
        let isDashed = false;

        if (relType === 'ABROGATES' || relType === 'AMENDS') {
          edgeColor = '#EF4444';
          isDashed = true;
        } else if (relType === 'APPLIES_TO' || relType === 'GOVERNS') {
          edgeColor = '#10B981';
        }

        edgesArray.push({
          id: `e_${nId}_${mId}_${relType}`,
          from: nId,
          to: mId,
          label: relType,
          color: { color: edgeColor, opacity: 0.8 },
          dashes: isDashed,
          font: { color: edgeColor, size: 9, align: 'middle', background: isDark ? '#0F172A' : '#FFFFFF' },
          arrows: 'to',
        });
      }
    });

    const nodesArray = Array.from(this.nodesMap.values());
    this.totalNodesCount.set(nodesArray.length);
    this.totalEdgesCount.set(edgesArray.length);

    this.nodesDataSet = new vis.DataSet(nodesArray);
    this.edgesDataSet = new vis.DataSet(edgesArray);

    const isHierarchical = this.layoutMode() === 'hierarchical';

    const options: any = {
      nodes: {
        borderWidth: 2,
        shadow: { enabled: true, color: 'rgba(0,0,0,0.3)', size: 6 },
      },
      edges: {
        width: 1.8,
        smooth: { type: isHierarchical ? 'cubicBezier' : 'continuous' },
      },
      layout: isHierarchical ? {
        hierarchical: {
          direction: 'UD',
          sortMethod: 'directed',
          levelSeparation: 120,
          nodeSpacing: 160
        }
      } : {
        improvedLayout: true
      },
      physics: {
        enabled: !isHierarchical && !this.isPhysicsFrozen(),
        barnesHut: {
          gravitationalConstant: -4000,
          springLength: 140,
          springConstant: 0.04,
          damping: 0.09
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

    this.networkInstance = new vis.Network(
      this.networkContainer.nativeElement,
      { nodes: this.nodesDataSet, edges: this.edgesDataSet },
      options
    );

    this.networkInstance.on('click', (params: any) => {
      if (params.nodes.length > 0) {
        const clickedId = String(params.nodes[0]);
        this.selectAndHighlightNode(clickedId);
      } else {
        this.selectedNode.set(null);
        this.resetHighlight();
      }
    });
  }

  selectAndHighlightNode(nodeId: string) {
    const node = this.nodesMap.get(nodeId);
    if (!node) return;

    this.selectedNode.set(node);

    // Find direct connected neighbors
    const connectedEdges = this.edgesDataSet.get().filter((e: any) => e.from === nodeId || e.to === nodeId);
    const neighborMap = new Map<string, string>();

    connectedEdges.forEach((e: any) => {
      if (e.from === nodeId) {
        neighborMap.set(e.to, e.label);
      } else {
        neighborMap.set(e.from, `(in) ${e.label}`);
      }
    });

    const neighbors: Array<{id: string; title: string; rel: string}> = [];
    neighborMap.forEach((rel, id) => {
      const neighborNode = this.nodesMap.get(id);
      if (neighborNode) {
        neighbors.push({
          id,
          title: neighborNode.label,
          rel
        });
      }
    });

    this.nodeNeighbors.set(neighbors);

    // Dim unconnected nodes & highlight neighbors
    const allNodeIds = Array.from(this.nodesMap.keys());
    const connectedNodeIds = new Set<string>([nodeId, ...neighborMap.keys()]);

    const updateNodes: any[] = [];
    allNodeIds.forEach(id => {
      const isConnected = connectedNodeIds.has(id);
      updateNodes.push({
        id,
        opacity: isConnected ? 1 : 0.25
      });
    });

    this.nodesDataSet.update(updateNodes);
  }

  resetHighlight() {
    if (!this.nodesDataSet) return;
    const updateNodes = Array.from(this.nodesMap.keys()).map(id => ({
      id,
      opacity: 1
    }));
    this.nodesDataSet.update(updateNodes);
  }

  inspectNeighbor(neighborId: string) {
    this.selectAndHighlightNode(neighborId);
    if (this.networkInstance) {
      this.networkInstance.focus(neighborId, {
        scale: 1.2,
        animation: { duration: 500, easingFunction: 'easeInOutQuad' }
      });
    }
  }

  onSearchChange() {
    if (!this.searchQuery.trim() || !this.nodesDataSet) {
      this.resetHighlight();
      return;
    }

    const query = this.searchQuery.toLowerCase();
    const matchingIds: string[] = [];

    this.nodesMap.forEach((node, id) => {
      const fullText = `${node.label} ${node.fullTitle} ${JSON.stringify(node.properties)}`.toLowerCase();
      if (fullText.includes(query)) {
        matchingIds.push(id);
      }
    });

    if (matchingIds.length > 0) {
      const firstMatch = matchingIds[0];
      this.selectAndHighlightNode(firstMatch);
      if (this.networkInstance) {
        this.networkInstance.focus(firstMatch, {
          scale: 1.3,
          animation: { duration: 400, easingFunction: 'easeInOutQuad' }
        });
      }
    }
  }

  getNodeBadgeClass(labels: string[] = []): string {
    const main = labels[0] || '';
    if (main === 'Circular') return 'bg-orange-500/10 text-[#E85D04] border border-[#E85D04]/30';
    if (main === 'Obligation') return 'bg-rose-500/10 text-rose-500 border border-rose-500/30';
    if (main === 'Process') return 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/30';
    if (main === 'ContractTemplate') return 'bg-indigo-500/10 text-indigo-500 border border-indigo-500/30';
    return 'bg-[var(--bg-input)] text-[var(--text-secondary)]';
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
