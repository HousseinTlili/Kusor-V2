import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-graph',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="max-w-7xl mx-auto p-6 space-y-6">
      <div class="glass-card p-6">
        <h1 class="text-2xl font-bold gold-gradient-text">Graphe de Connaissances Réglementaires Neo4j</h1>
        <p class="text-sm text-slate-400 mt-1">Structure des nœuds et relations circulaires, articles, et obligations BCT</p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="glass-card p-6 space-y-4">
          <h2 class="text-lg font-bold text-amber-400">Statistiques des Nœuds</h2>
          <div class="space-y-2">
            @for (item of nodeStats(); track item.key) {
              <div class="flex justify-between p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-sm">
                <span class="font-medium text-slate-300">{{ item.key }}</span>
                <span class="font-bold text-amber-400">{{ item.value }}</span>
              </div>
            }
          </div>
        </div>

        <div class="glass-card p-6 space-y-4">
          <h2 class="text-lg font-bold text-indigo-400">Statistiques des Relations</h2>
          <div class="space-y-2">
            @for (item of relStats(); track item.key) {
              <div class="flex justify-between p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-sm">
                <span class="font-medium text-slate-300">{{ item.key }}</span>
                <span class="font-bold text-indigo-400">{{ item.value }}</span>
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
