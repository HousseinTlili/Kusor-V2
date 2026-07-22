import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="max-w-7xl mx-auto p-6 space-y-8">
      <!-- Header banner -->
      <div class="glass-card p-8 flex flex-col md:flex-row items-center justify-between gap-6">
        <div>
          <h1 class="text-3xl font-extrabold tracking-tight gold-gradient-text">Vue Synthétique de Conformité</h1>
          <p class="text-slate-400 mt-1">Plateforme d'intelligence et de surveillance réglementaire BCT</p>
        </div>
        <button (click)="loadStats()" class="px-5 py-2.5 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 text-sm font-semibold transition-all">
          Actualiser les Données
        </button>
      </div>

      <!-- Stats Metric Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div class="glass-card-interactive p-6 space-y-2">
          <div class="text-xs uppercase font-bold text-slate-400 tracking-wider">Circulaires & Textes</div>
          <div class="text-3xl font-extrabold text-amber-400">{{ stats()?.documents_total || 0 }}</div>
          <div class="text-xs text-slate-500">Indexés dans PostgreSQL & ChromaDB</div>
        </div>

        <div class="glass-card-interactive p-6 space-y-2">
          <div class="text-xs uppercase font-bold text-slate-400 tracking-wider">Vecteurs Embeddings</div>
          <div class="text-3xl font-extrabold text-indigo-400">{{ stats()?.chromadb_vectors || 0 }}</div>
          <div class="text-xs text-slate-500">Modèle nomic-embed-text</div>
        </div>

        <div class="glass-card-interactive p-6 space-y-2">
          <div class="text-xs uppercase font-bold text-slate-400 tracking-wider">Nœuds Neo4j Graph</div>
          <div class="text-3xl font-extrabold text-emerald-400">{{ stats()?.neo4j_nodes || 0 }}</div>
          <div class="text-xs text-slate-500">{{ stats()?.neo4j_relationships || 0 }} relations temporelles</div>
        </div>

        <div class="glass-card-interactive p-6 space-y-2">
          <div class="text-xs uppercase font-bold text-slate-400 tracking-wider">Logs d'Audit Systèmes</div>
          <div class="text-3xl font-extrabold text-rose-400">{{ stats()?.audit_logs_total || 0 }}</div>
          <div class="text-xs text-slate-500">Traçabilité avec hash SHA-256</div>
        </div>
      </div>
    </div>
  `
})
export class DashboardComponent implements OnInit {
  api = inject(ApiService);
  stats = signal<any>(null);

  ngOnInit() {
    this.loadStats();
  }

  loadStats() {
    this.api.getStats().subscribe({
      next: (res) => this.stats.set(res),
      error: (err) => console.error('Failed to load stats', err)
    });
  }
}
