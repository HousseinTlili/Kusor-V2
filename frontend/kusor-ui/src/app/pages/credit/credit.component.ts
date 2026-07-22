import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { SeverityBadgeComponent } from '../../shared/components/severity-badge/severity-badge.component';

@Component({
  selector: 'app-credit',
  standalone: true,
  imports: [CommonModule, FormsModule, SeverityBadgeComponent],
  template: `
    <div class="max-w-7xl mx-auto p-6 space-y-6">
      <div class="glass-card p-6">
        <h1 class="text-2xl font-bold gold-gradient-text">Module 4: Pré-filtrage de Dossier de Crédit Multi-Agent</h1>
        <p class="text-sm text-slate-400 mt-1">Superviseur coordonnant 3 sous-agents (Complétude, Calculs financiers, Identité/KYC)</p>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Input Form -->
        <div class="glass-card p-6 space-y-4">
          <div>
            <label class="block text-xs font-semibold text-slate-300 uppercase mb-1">Nom du Demandeur</label>
            <input type="text" [(ngModel)]="applicantName" placeholder="ex: Ahmed Ben Ali"
              class="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-amber-500" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-300 uppercase mb-1">Revenu Mensuel (TND)</label>
            <input type="number" [(ngModel)]="income"
              class="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-amber-500" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-300 uppercase mb-1">Charges Dette Mensuelle (TND)</label>
            <input type="number" [(ngModel)]="monthlyDebt"
              class="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-amber-500" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-300 uppercase mb-1">Annuité Nouveau Prêt (TND)</label>
            <input type="number" [(ngModel)]="loanAnnuity"
              class="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-amber-500" />
          </div>

          <button (click)="prescreen()" [disabled]="loading() || !applicantName"
            class="w-full py-3 rounded-xl font-bold text-slate-950 bg-gradient-to-r from-amber-400 to-amber-500 hover:from-amber-300 hover:to-amber-400 disabled:opacity-50 transition-all">
            {{ loading() ? 'Pré-filtrage en cours...' : 'Exécuter le Pré-filtrage' }}
          </button>
        </div>

        <!-- Output Report -->
        <div class="lg:col-span-2 glass-card p-6 space-y-6">
          @if (!report()) {
            <div class="flex flex-col items-center justify-center h-64 text-slate-500 italic">
              Remplissez les détails financiers et lancez le pré-filtrage.
            </div>
          } @else {
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h2 class="text-lg font-bold text-slate-100">{{ report().applicant_name }}</h2>
                <div class="text-xs text-slate-400">Verdict Global: <strong class="text-amber-400 font-bold uppercase">{{ report().overall_verdict }}</strong></div>
              </div>
              <app-severity-badge [severity]="report().overall_verdict"></app-severity-badge>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div class="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                <div class="font-bold text-amber-400">Agent Complétude Documentaire</div>
                <div>Documents Présents: {{ report().document_completeness?.present_documents?.length || 0 }}</div>
                <div>Verdict: <span class="font-bold text-emerald-400">{{ report().document_completeness?.verdict }}</span></div>
              </div>

              <div class="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                <div class="font-bold text-indigo-400">Agent Calculs Financiers</div>
                <div>Taux d'Endettement: {{ ((report().numerical_validation?.debt_ratio || 0) * 100).toFixed(0) }}% (Norme BCT: &le; 40%)</div>
                <div>Verdict: <span class="font-bold text-amber-400">{{ report().numerical_validation?.verdict }}</span></div>
              </div>
            </div>

            @if (report().blocking_issues?.length) {
              <div class="space-y-2">
                <h3 class="text-sm font-semibold text-rose-400">Points Bloquants Identifiés</h3>
                @for (block of report().blocking_issues; track $index) {
                  <div class="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
                    ⚠️ {{ block }}
                  </div>
                }
              </div>
            }
          }
        </div>
      </div>
    </div>
  `
})
export class CreditComponent {
  api = inject(ApiService);
  applicantName = 'Jean Dupont';
  income = 3000;
  monthlyDebt = 400;
  loanAnnuity = 300;
  report = signal<any>(null);
  loading = signal(false);

  prescreen() {
    if (!this.applicantName) return;
    this.loading.set(true);

    this.api.prescreenCredit({
      dossier_id: 'cred_101',
      applicant_name: this.applicantName,
      loan_type: 'personal',
      files: ['cin.pdf', 'bulletin_paie.pdf', 'releve_bancaire.pdf', 'attestation_travail.pdf'],
      financial_data: {
        income: this.income,
        monthly_debt: this.monthlyDebt,
        loan_annuity: this.loanAnnuity
      }
    }).subscribe({
      next: (res) => {
        this.report.set(res);
        this.loading.set(false);
      },
      error: () => this.loading.set(false)
    });
  }
}
