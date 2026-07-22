import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-temporal-explorer',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="max-w-7xl mx-auto p-6 space-y-6">
      <div class="glass-card p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold gold-gradient-text">Explorateur Temporel du Graphe</h1>
          <p class="text-sm text-slate-400 mt-1">Évaluez la réglementation en vigueur à une date historique choisie</p>
        </div>

        <div class="flex items-center gap-3">
          <label class="text-xs font-semibold uppercase text-slate-400">Date d'évaluation:</label>
          <input type="date" [(ngModel)]="asOfDate" (change)="loadTemporalGraph()"
            class="px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-amber-400 font-bold text-sm focus:outline-none focus:border-amber-500" />
        </div>
      </div>

      <div class="glass-card p-6 min-h-[400px]">
        @if (loading()) {
          <div class="flex justify-center items-center h-64 text-slate-400 font-medium">Chargement des données temporelles...</div>
        } @else {
          <div class="space-y-4">
            <h2 class="text-sm font-semibold text-slate-400 uppercase tracking-wider">Circulaires Vides/Valides au {{ asOfDate }}</h2>
            @if (!records().length) {
              <div class="p-8 text-center text-slate-500 italic">Aucun enregistrement trouvé pour cette date d'évaluation.</div>
            } @else {
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                @for (rec of records(); track $index) {
                  <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800 text-xs space-y-2">
                    <div class="font-bold text-amber-400 text-sm">{{ rec.c?.properties?.title || rec.c?.properties?.reference || 'Circulaire' }}</div>
                    <div class="text-slate-400">Date d'émission: {{ rec.c?.properties?.date_issued || 'Inconnue' }}</div>
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
