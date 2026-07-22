import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-temporal-explorer',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="p-8 max-w-7xl mx-auto space-y-8">
      <div class="glass-card p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 relative overflow-hidden">
        <div class="absolute -left-20 -bottom-20 w-80 h-80 bg-[#E85D04]/10 rounded-full blur-3xl pointer-events-none"></div>

        <div>
          <h1 class="text-3xl font-black brand-gradient-text">Explorateur Temporel du Graphe</h1>
          <p class="text-sm text-slate-400 mt-1">Évaluez la réglementation en vigueur à une date historique choisie</p>
        </div>

        <div class="flex items-center gap-3">
          <label class="text-xs font-bold uppercase tracking-wider text-slate-400">Date d'évaluation:</label>
          <input type="date" [(ngModel)]="asOfDate" (change)="loadTemporalGraph()"
            class="px-4 py-3 rounded-xl bg-[#090D28] border border-[#E85D04]/40 text-[#E85D04] font-black text-sm focus:outline-none focus:border-[#E85D04] shadow-lg shadow-[#E85D04]/10 transition-all" />
        </div>
      </div>

      <div class="glass-card p-8 min-h-[400px]">
        @if (loading()) {
          <div class="flex justify-center items-center h-64 text-slate-400 font-medium">Chargement des données temporelles...</div>
        } @else {
          <div class="space-y-6">
            <h2 class="text-xs font-black text-slate-400 uppercase tracking-widest">Circulaires Valides au {{ asOfDate }}</h2>
            @if (!records().length) {
              <div class="p-12 text-center text-slate-500 italic font-medium">Aucun enregistrement trouvé pour cette date d'évaluation.</div>
            } @else {
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                @for (rec of records(); track $index) {
                  <div class="p-5 rounded-2xl bg-[#090D28] border border-slate-800 text-xs space-y-2.5 hover:border-[#E85D04]/40 transition-all">
                    <div class="font-bold text-[#E85D04] text-sm">{{ rec.c?.properties?.title || rec.c?.properties?.reference || 'Circulaire BCT' }}</div>
                    <div class="text-slate-400 font-medium">Date d'émission: {{ rec.c?.properties?.date_issued || 'Inconnue' }}</div>
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
