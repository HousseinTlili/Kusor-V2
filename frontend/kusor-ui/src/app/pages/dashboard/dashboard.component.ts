import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="p-8 space-y-8 max-w-7xl mx-auto bg-[#03071E]">
      <!-- Header Banner -->
      <div class="glass-card p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 relative overflow-hidden bg-[#070A18]">
        <div class="absolute -right-20 -bottom-20 w-80 h-80 bg-[#E85D04]/10 rounded-full blur-3xl pointer-events-none"></div>

        <div>
          <h1 class="text-3xl font-black tracking-tight brand-gradient-text">Vue Synthétique de Conformité</h1>
          <p class="text-slate-400 mt-1 text-sm">Plateforme d'intelligence et de surveillance réglementaire Banque Centrale de Tunisie</p>
        </div>

        <button (click)="loadStats()" class="px-5 py-3 rounded-xl bg-[#E85D04]/15 hover:bg-[#E85D04]/25 text-[#E85D04] border border-[#E85D04]/40 text-xs font-bold transition-all shadow-lg shadow-[#E85D04]/10">
          Actualiser les Données
        </button>
      </div>

      <!-- Stats Metric Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div class="glass-card-interactive p-6 space-y-3 bg-[#070A18]">
          <div class="flex items-center justify-between">
            <div class="text-[11px] uppercase font-black text-slate-400 tracking-wider">Circulaires BCT</div>
            <div class="p-2 rounded-xl bg-[#E85D04]/10 text-[#E85D04]">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
              </svg>
            </div>
          </div>
          <div class="text-4xl font-black text-white">{{ stats()?.documents_total || 0 }}</div>
          <div class="text-[11px] text-slate-500 font-medium">Indexés dans PostgreSQL & ChromaDB</div>
        </div>

        <div class="glass-card-interactive p-6 space-y-3 bg-[#070A18]">
          <div class="flex items-center justify-between">
            <div class="text-[11px] uppercase font-black text-slate-400 tracking-wider">Vecteurs Embeddings</div>
            <div class="p-2 rounded-xl bg-[#E85D04]/10 text-[#E85D04]">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/>
              </svg>
            </div>
          </div>
          <div class="text-4xl font-black text-amber-400">{{ stats()?.chromadb_vectors || 0 }}</div>
          <div class="text-[11px] text-slate-500 font-medium">Embeddings nomic-embed-text</div>
        </div>

        <div class="glass-card-interactive p-6 space-y-3 bg-[#070A18]">
          <div class="flex items-center justify-between">
            <div class="text-[11px] uppercase font-black text-slate-400 tracking-wider">Nœuds Neo4j Graph</div>
            <div class="p-2 rounded-xl bg-emerald-500/10 text-emerald-400">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
              </svg>
            </div>
          </div>
          <div class="text-4xl font-black text-emerald-400">{{ stats()?.neo4j_nodes || 0 }}</div>
          <div class="text-[11px] text-slate-500 font-medium">{{ stats()?.neo4j_relationships || 0 }} relations temporelles</div>
        </div>

        <div class="glass-card-interactive p-6 space-y-3 bg-[#070A18]">
          <div class="flex items-center justify-between">
            <div class="text-[11px] uppercase font-black text-slate-400 tracking-wider">Logs d'Audit Systèmes</div>
            <div class="p-2 rounded-xl bg-rose-500/10 text-rose-400">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
              </svg>
            </div>
          </div>
          <div class="text-4xl font-black text-rose-400">{{ stats()?.audit_logs_total || 0 }}</div>
          <div class="text-[11px] text-slate-500 font-medium">Traçabilité SHA-256</div>
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
