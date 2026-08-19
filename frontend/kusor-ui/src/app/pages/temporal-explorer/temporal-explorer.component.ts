import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-temporal-explorer',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="p-6 md:p-8 max-w-7xl mx-auto space-y-8">
      
      <!-- Header Banner -->
      <div class="glass-card p-6 md:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 relative overflow-hidden shadow-sm">
        <div class="space-y-1 z-10 relative">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#E85D04]/10 text-[#E85D04] text-xs font-bold uppercase tracking-wider">
            <span>⏱️ Analyse Temporelle & Historique</span>
          </div>
          <h1 class="text-2xl md:text-3xl font-black text-[var(--text-primary)]">Explorateur Temporel du Graphe BCT</h1>
          <p class="text-sm text-[var(--text-muted)] max-w-2xl">
            Évaluez l'état exact des circulaires et obligations en vigueur à une date historique passée.
          </p>
        </div>

        <div class="flex items-center gap-3 z-10">
          <label class="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">Date d'évaluation :</label>
          <input type="date" [(ngModel)]="asOfDate" (change)="loadTemporalGraph()"
            class="px-4 py-2.5 rounded-xl bg-[var(--bg-input)] border border-[#E85D04]/40 text-[#E85D04] font-bold text-sm focus:outline-none focus:border-[#E85D04] shadow-sm transition-all" />
        </div>
      </div>

      <!-- Content Area -->
      <div class="glass-card p-6 md:p-8 min-h-[400px] shadow-sm">
        @if (loading()) {
          <div class="flex justify-center items-center h-64 text-[var(--text-muted)] font-medium gap-3">
            <svg class="animate-spin h-5 w-5 text-[#E85D04]" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>Chargement des données temporelles Neo4j...</span>
          </div>
        } @else {
          <div class="space-y-6">
            <div class="flex items-center justify-between border-b border-[var(--border-card)] pb-4">
              <h2 class="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider">
                Circulaires Valides au {{ asOfDate }} ({{ records().length }})
              </h2>
              <span class="text-xs text-[var(--text-muted)]">Reconstitution de l'état juridique</span>
            </div>

            @if (!records().length) {
              <div class="p-12 text-center text-[var(--text-muted)] italic font-medium">
                Aucun enregistrement trouvé pour cette date d'évaluation.
              </div>
            } @else {
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                @for (rec of records(); track $index) {
                  <div class="p-5 rounded-2xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)] text-xs space-y-2 hover:border-[#E85D04]/40 transition-all shadow-sm">
                    <div class="font-bold text-[#E85D04] text-sm">{{ rec.c?.properties?.title || rec.c?.properties?.reference || 'Circulaire BCT' }}</div>
                    <div class="text-[var(--text-muted)] font-medium">Date d'émission : <span class="text-[var(--text-secondary)] font-semibold">{{ rec.c?.properties?.date_issued || 'Non renseignée' }}</span></div>
                    <div class="text-[var(--text-muted)] font-medium">Statut : <span class="inline-flex px-2 py-0.5 rounded-md bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-400 font-bold border border-emerald-200 dark:border-emerald-800 text-[10px]">En vigueur</span></div>
                  </div>
                }
              </div>
            }
          </div>
        }
      </div>

    </div>
  `
})
export class TemporalExplorerComponent implements OnInit {
  api = inject(ApiService);
  asOfDate = '2024-02-10';
  records = signal<any[]>([]);
  loading = signal(false);

  ngOnInit() {
    this.loadTemporalGraph();
  }

  loadTemporalGraph() {
    this.loading.set(true);
    this.api.getTemporalGraph(this.asOfDate).subscribe({
      next: (res) => {
        this.records.set(res.records || []);
        this.loading.set(false);
      },
      error: () => this.loading.set(false)
    });
  }
}
