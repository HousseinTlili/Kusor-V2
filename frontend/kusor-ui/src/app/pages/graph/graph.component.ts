import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-graph',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="p-8 max-w-7xl mx-auto space-y-8">
      <div class="glass-card p-8 relative overflow-hidden">
        <div class="absolute -right-20 -top-20 w-80 h-80 bg-[#E85D04]/10 rounded-full blur-3xl pointer-events-none"></div>
        <h1 class="text-3xl font-black brand-gradient-text">Graphe de Connaissances Réglementaires Neo4j</h1>
        <p class="text-sm text-slate-400 mt-1">Structure des nœuds et relations circulaires, articles, et obligations BCT</p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="glass-card p-6 space-y-4">
          <div class="flex items-center gap-3 pb-3 border-b border-slate-800">
            <div class="p-2 rounded-xl bg-[#E85D04]/10 text-[#E85D04]">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
              </svg>
            </div>
            <h2 class="text-lg font-black text-white">Statistiques des Nœuds</h2>
          </div>

          <div class="space-y-2">
            @for (item of nodeStats(); track item.key) {
              <div class="flex justify-between p-3.5 rounded-xl bg-[#090D28] border border-slate-800/80 text-xs">
                <span class="font-semibold text-slate-300">{{ item.key }}</span>
                <span class="font-black text-[#E85D04]">{{ item.value }}</span>
              </div>
            }
          </div>
        </div>

        <div class="glass-card p-6 space-y-4">
          <div class="flex items-center gap-3 pb-3 border-b border-slate-800">
            <div class="p-2 rounded-xl bg-indigo-500/10 text-indigo-400">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/>
              </svg>
            </div>
            <h2 class="text-lg font-black text-white">Statistiques des Relations</h2>
          </div>

          <div class="space-y-2">
            @for (item of relStats(); track item.key) {
              <div class="flex justify-between p-3.5 rounded-xl bg-[#090D28] border border-slate-800/80 text-xs">
                <span class="font-semibold text-slate-300">{{ item.key }}</span>
                <span class="font-black text-indigo-400">{{ item.value }}</span>
              </div>
            }
          </div>
        </div>
      </div>
    </div>
  `
})
export class GraphComponent implements OnInit {
  api = inject(ApiService);
  nodeStats = signal<Array<{key: string; value: number}>>([]);
  relStats = signal<Array<{key: string; value: number}>>([]);

  ngOnInit() {
    this.api.getGraphOverview().subscribe({
      next: (res) => {
        const nodes = Object.entries(res.node_counts || {}).map(([key, value]) => ({ key, value: value as number }));
        const rels = Object.entries(res.relationship_counts || {}).map(([key, value]) => ({ key, value: value as number }));
        this.nodeStats.set(nodes);
        this.relStats.set(rels);
      }
    });
  }
}
