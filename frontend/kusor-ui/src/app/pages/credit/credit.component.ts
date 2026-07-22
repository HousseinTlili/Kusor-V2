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
    <div class="p-8 max-w-7xl mx-auto space-y-8">
      <div class="glass-card p-8 relative overflow-hidden">
        <div class="absolute -right-20 -top-20 w-80 h-80 bg-[#E85D04]/10 rounded-full blur-3xl pointer-events-none"></div>
        <h1 class="text-3xl font-black brand-gradient-text">Module 4: Pré-filtrage de Dossier de Crédit Multi-Agent</h1>
        <p class="text-sm text-slate-400 mt-1">Superviseur coordonnant 3 sous-agents (Complétude, Calculs financiers, Identité/KYC)</p>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Input Form -->
        <div class="glass-card p-6 space-y-4">
          <div>
            <label class="block text-[11px] font-extrabold text-slate-300 uppercase tracking-wider mb-2">Nom du Demandeur</label>
            <input type="text" [(ngModel)]="applicantName" placeholder="ex: Ahmed Ben Ali"
              class="w-full px-4 py-3 rounded-xl bg-[#090D28] border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-[#E85D04] transition-all" />
          </div>

          <div>
            <label class="block text-[11px] font-extrabold text-slate-300 uppercase tracking-wider mb-2">Revenu Mensuel (TND)</label>
            <input type="number" [(ngModel)]="income"
              class="w-full px-4 py-3 rounded-xl bg-[#090D28] border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-[#E85D04] transition-all" />
          </div>

          <div>
            <label class="block text-[11px] font-extrabold text-slate-300 uppercase tracking-wider mb-2">Charges Dette Mensuelle (TND)</label>
            <input type="number" [(ngModel)]="monthlyDebt"
              class="w-full px-4 py-3 rounded-xl bg-[#090D28] border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-[#E85D04] transition-all" />
          </div>

          <div>
            <label class="block text-[11px] font-extrabold text-slate-300 uppercase tracking-wider mb-2">Annuité Nouveau Prêt (TND)</label>
            <input type="number" [(ngModel)]="loanAnnuity"
              class="w-full px-4 py-3 rounded-xl bg-[#090D28] border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-[#E85D04] transition-all" />
          </div>

          <button (click)="prescreen()" [disabled]="loading() || !applicantName"
            class="w-full py-3.5 rounded-xl font-bold text-white bg-gradient-to-r from-[#FAA307] via-[#E85D04] to-[#DC2F02] hover:from-[#E85D04] hover:to-[#9D0208] disabled:opacity-50 shadow-xl shadow-[#E85D04]/30 transition-all text-sm">
            {{ loading() ? 'Pré-filtrage en cours...' : 'Exécuter le Pré-filtrage' }}
          </button>
        </div>

        <!-- Output Report -->
        <div class="lg:col-span-2 glass-card p-8 space-y-6">
          @if (!report()) {
            <div class="flex flex-col items-center justify-center h-64 text-slate-500 italic font-medium">
              Remplissez les détails financiers et lancez le pré-filtrage.
            </div>
          } @else {
            <div class="flex items-center justify-between border-b border-slate-800 pb-5">
              <div>
                <h2 class="text-xl font-black text-white">{{ report().applicant_name }}</h2>
                <div class="text-xs text-slate-400 font-medium mt-0.5">Verdict Global: <strong class="text-[#E85D04] font-black uppercase">{{ report().overall_verdict }}</strong></div>
              </div>
              <app-severity-badge [severity]="report().overall_verdict"></app-severity-badge>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
              <div class="p-5 rounded-2xl bg-[#090D28] border border-slate-800 space-y-3">
                <div class="font-black text-[#E85D04] text-sm">Agent Complétude Documentaire</div>
                <div class="text-slate-300">Documents Présents: {{ report().document_completeness?.present_documents?.length || 0 }}</div>
                <div>Verdict: <span class="font-black text-emerald-400">{{ report().document_completeness?.verdict }}</span></div>
              </div>

              <div class="p-5 rounded-2xl bg-[#090D28] border border-slate-800 space-y-3">
                <div class="font-black text-indigo-400 text-sm">Agent Calculs Financiers</div>
                <div class="text-slate-300">Taux d'Endettement: {{ ((report().numerical_validation?.debt_ratio || 0) * 100).toFixed(0) }}% (Norme BCT: &le; 40%)</div>
                <div>Verdict: <span class="font-black text-[#E85D04]">{{ report().numerical_validation?.verdict }}</span></div>
              </div>
            </div>

            @if (report().blocking_issues?.length) {
              <div class="space-y-3">
                <h3 class="text-xs font-black text-rose-400 uppercase tracking-wider">Points Bloquants Identifiés</h3>
                @for (block of report().blocking_issues; track $index) {
                  <div class="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs font-semibold">
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
