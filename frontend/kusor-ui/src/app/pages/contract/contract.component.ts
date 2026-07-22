import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { SeverityBadgeComponent } from '../../shared/components/severity-badge/severity-badge.component';

@Component({
  selector: 'app-contract',
  standalone: true,
  imports: [CommonModule, FormsModule, SeverityBadgeComponent],
  template: `
    <div class="max-w-7xl mx-auto p-6 space-y-6">
      <div class="glass-card p-6">
        <h1 class="text-2xl font-bold gold-gradient-text">Module 3: Analyse de Risque de Contrat</h1>
        <p class="text-sm text-slate-400 mt-1">Segmentation de clauses et vérification de validité temporelle des références BCT</p>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Input Form -->
        <div class="glass-card p-6 space-y-4">
          <div>
            <label class="block text-xs font-semibold text-slate-300 uppercase mb-1">Titre du Contrat</label>
            <input type="text" [(ngModel)]="title" placeholder="ex: Convention de Prêt Immobilier"
              class="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-amber-500" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-300 uppercase mb-1">Texte des Clauses du Contrat</label>
            <textarea [(ngModel)]="text" rows="8" placeholder="Collez les clauses ou articles du contrat..."
              class="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-amber-500"></textarea>
          </div>

          <button (click)="analyze()" [disabled]="loading() || !text"
            class="w-full py-3 rounded-xl font-bold text-slate-950 bg-gradient-to-r from-amber-400 to-amber-500 hover:from-amber-300 hover:to-amber-400 disabled:opacity-50 transition-all">
            {{ loading() ? 'Analyse des clauses...' : 'Analyser le Contrat' }}
          </button>
        </div>

        <!-- Output Report -->
        <div class="lg:col-span-2 glass-card p-6 space-y-6">
          @if (!report()) {
            <div class="flex flex-col items-center justify-center h-64 text-slate-500 italic">
              Entrez le texte des clauses du contrat et lancez l'analyse.
            </div>
          } @else {
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h2 class="text-lg font-bold text-slate-100">{{ report().contract_title }}</h2>
                <div class="text-xs text-slate-400">Total Clauses: {{ report().total_clauses }}</div>
              </div>
              <app-severity-badge [severity]="report().overall_risk"></app-severity-badge>
            </div>

            <div class="space-y-4">
              <h3 class="text-sm font-semibold text-slate-300">Détail des Clauses Analysées</h3>
              @for (c of report().clauses; track c.clause_number) {
                <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2 text-xs">
                  <div class="flex justify-between items-center">
                    <span class="font-bold text-amber-400">Clause N° {{ c.clause_number }} (Type: {{ c.clause_type }})</span>
                    <app-severity-badge [severity]="c.conformity_status"></app-severity-badge>
                  </div>
                  <p class="text-slate-300">{{ c.clause_text }}</p>
                </div>
              }
            </div>
          }
        </div>
      </div>
    </div>
  `
})
export class ContractComponent {
  api = inject(ApiService);
  title = 'Convention Prêt Immobilier 2024';
  text = `Article 1\nLe prêteur accorde un prêt d'un montant de 100 000 TND au taux d'intérêt de 7%.\n\nArticle 2\nEn cas de retard, des pénalités de retard de 2% seront appliquées.`;
  report = signal<any>(null);
  loading = signal(false);

  analyze() {
    if (!this.text) return;
    this.loading.set(true);

    this.api.analyzeContract({ title: this.title, text: this.text }).subscribe({
      next: (res) => {
        this.report.set(res);
        this.loading.set(false);
      },
      error: () => this.loading.set(false)
    });
  }
}
