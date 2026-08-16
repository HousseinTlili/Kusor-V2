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
    <div class="p-6 md:p-8 max-w-7xl mx-auto space-y-8">
      
      <!-- Header Banner -->
      <div class="glass-card p-6 md:p-8 relative overflow-hidden">
        <div class="space-y-1 z-10 relative">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-400 text-xs font-bold uppercase tracking-wider border border-emerald-200 dark:border-emerald-800">
            <span>💳 Gestion des Engagements & Risques</span>
          </div>
          <h1 class="text-2xl md:text-3xl font-black text-[var(--text-primary)]">Pré-filtrage de Dossier de Crédit Multi-Agent</h1>
          <p class="text-sm text-[var(--text-muted)] max-w-2xl">
            Supervision automatique coordonnant 3 sous-agents : Complétude documentaire, Calculs financiers BCT (Ratio ≤ 40%), et Conformité Emprunteur.
          </p>
        </div>
      </div>

      <!-- Quick Demo Presets Bar -->
      <div class="glass-card p-4 flex flex-wrap items-center gap-3 text-xs shadow-sm">
        <span class="font-bold text-[var(--text-muted)] uppercase tracking-wider text-[10px] mr-2">Cas Types Emprunteurs :</span>
        <button (click)="loadPreset('approve')" class="px-3.5 py-1.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 hover:bg-emerald-100 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800 font-semibold transition-all shadow-sm">
          ✓ Dossier Éligible (Endettement 23%)
        </button>
        <button (click)="loadPreset('reject_debt')" class="px-3.5 py-1.5 rounded-xl bg-rose-50 dark:bg-rose-950/30 hover:bg-rose-100 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-800 font-semibold transition-all shadow-sm">
          ⚠️ Rejet Endettement (52% &gt; 40% BCT)
        </button>
        <button (click)="loadPreset('missing_docs')" class="px-3.5 py-1.5 rounded-xl bg-amber-50 dark:bg-amber-950/30 hover:bg-amber-100 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800 font-semibold transition-all shadow-sm">
          ⏳ Pièces Manquantes (Bulletin Incomplet)
        </button>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        <!-- Input Form -->
        <div class="glass-card p-6 space-y-4 shadow-sm">
          <div>
            <label class="block text-[11px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1.5">Nom de l'Emprunteur</label>
            <input type="text" [(ngModel)]="applicantName" placeholder="ex: Ahmed Ben Ali"
              class="w-full px-4 py-3 rounded-xl bg-[var(--bg-input)] border border-[var(--border-input)] text-[var(--text-primary)] text-sm focus:outline-none focus:border-[#E85D04] focus:ring-2 focus:ring-[#E85D04]/20 transition-all" />
          </div>

          <div>
            <label class="block text-[11px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1.5">Type de Prêt Demandé</label>
            <select [(ngModel)]="loanType" class="w-full px-4 py-3 rounded-xl bg-[var(--bg-input)] border border-[var(--border-input)] text-[var(--text-primary)] text-sm focus:outline-none focus:border-[#E85D04] focus:ring-2 focus:ring-[#E85D04]/20 transition-all">
              <option value="personal">Prêt Personnel / Consommation</option>
              <option value="mortgage">Prêt Immobilier / Habitat</option>
              <option value="corporate">Financement Entreprise / Équipement</option>
            </select>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-[11px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1.5">Revenu Net (TND)</label>
              <input type="number" [(ngModel)]="income"
                class="w-full px-3 py-2.5 rounded-xl bg-[var(--bg-input)] border border-[var(--border-input)] text-[var(--text-primary)] text-sm focus:outline-none focus:border-[#E85D04] transition-all" />
            </div>

            <div>
              <label class="block text-[11px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1.5">Dettes En Cours (TND)</label>
              <input type="number" [(ngModel)]="monthlyDebt"
                class="w-full px-3 py-2.5 rounded-xl bg-[var(--bg-input)] border border-[var(--border-input)] text-[var(--text-primary)] text-sm focus:outline-none focus:border-[#E85D04] transition-all" />
            </div>
          </div>

          <div>
            <label class="block text-[11px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1.5">Mensualité Nouveau Prêt (TND)</label>
            <input type="number" [(ngModel)]="loanAnnuity"
              class="w-full px-4 py-3 rounded-xl bg-[var(--bg-input)] border border-[var(--border-input)] text-[var(--text-primary)] text-sm focus:outline-none focus:border-[#E85D04] transition-all" />
          </div>

          <!-- Document Upload Box -->
          <div>
            <label class="block text-[11px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1.5">Justificatifs Financiers (PDF)</label>
            <div class="border-2 border-dashed border-[var(--border-card-hover)] hover:border-[#E85D04] rounded-2xl p-4 text-center bg-[var(--bg-page-subtle)] transition-all cursor-pointer relative">
              <input type="file" multiple (change)="onFilesSelected($event)" class="absolute inset-0 opacity-0 cursor-pointer w-full h-full" />
              <svg class="w-7 h-7 text-[var(--text-muted)] mx-auto mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
              </svg>
              <div class="text-xs text-[var(--text-primary)] font-bold">Sélectionner Bulletins de Paie / Relevés</div>
            </div>
            @if (uploadedFiles.length > 0) {
              <div class="mt-2 flex flex-wrap gap-1.5">
                @for (file of uploadedFiles; track $index) {
                  <span class="inline-flex items-center px-2 py-0.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-400 text-[10px] font-medium">
                    📄 {{ file }}
                  </span>
                }
              </div>
            }
          </div>

          <button (click)="prescreen()" [disabled]="loading() || !applicantName"
            class="w-full py-3.5 rounded-xl font-bold brand-btn-primary disabled:opacity-50 transition-all text-xs flex items-center justify-center gap-2 shadow-sm">
            @if (loading()) {
              <svg class="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>Vérification multi-agent en cours...</span>
            } @else {
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
              </svg>
              <span>Exécuter le Pré-filtrage Crédit</span>
            }
          </button>
        </div>

        <!-- Output Report -->
        <div class="lg:col-span-2 glass-card p-6 md:p-8 space-y-6 shadow-sm">
          @if (!report()) {
            <div class="flex flex-col items-center justify-center h-80 text-[var(--text-muted)] italic font-medium space-y-3">
              <svg class="w-12 h-12 text-[var(--text-faint)] opacity-60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
              </svg>
              <span>Sélectionnez un cas type ou entrez les paramètres financiers pour lancer l'analyse de risque crédit.</span>
            </div>
          } @else {
            <div class="flex items-center justify-between border-b border-[var(--border-card)] pb-5">
              <div>
                <h2 class="text-xl font-black text-[var(--text-primary)]">{{ report().applicant_name }}</h2>
                <div class="text-xs text-[var(--text-muted)] font-medium mt-0.5">Dossier N° {{ report().dossier_id }} | Décision Superviseur : <strong class="text-[#E85D04] font-black uppercase">{{ report().overall_verdict }}</strong></div>
              </div>
              <app-severity-badge [severity]="report().overall_verdict"></app-severity-badge>
            </div>

            <!-- Sub-Agents Results Cards -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div class="p-5 rounded-2xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)] space-y-2">
                <div class="font-bold text-[#E85D04] text-sm flex items-center justify-between">
                  <span>1. Agent Complétude</span>
                  <span class="text-xs text-[var(--text-muted)]">{{ ((report().document_completeness?.completeness_ratio || 1) * 100).toFixed(0) }}%</span>
                </div>
                <div class="text-[var(--text-secondary)]">Documents Requis : {{ report().document_completeness?.required_documents?.length || 4 }}</div>
                <div class="text-[var(--text-muted)]">Verdict : <strong class="text-emerald-600 dark:text-emerald-400">{{ report().document_completeness?.verdict }}</strong></div>
              </div>

              <div class="p-5 rounded-2xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)] space-y-2">
                <div class="font-bold text-indigo-600 dark:text-indigo-400 text-sm flex items-center justify-between">
                  <span>2. Agent Calculs Financiers</span>
                  <span class="text-xs text-[var(--text-muted)]">Norme BCT &le; 40%</span>
                </div>
                <div class="text-[var(--text-secondary)]">Taux d'Endettement : <strong class="text-2xl text-[var(--text-primary)] ml-1">{{ ((report().numerical_validation?.debt_ratio || 0) * 100).toFixed(0) }}%</strong></div>
                <div class="text-[var(--text-muted)]">Statut : <span [class]="report().numerical_validation?.debt_ratio_compliant ? 'text-emerald-600 dark:text-emerald-400 font-bold' : 'text-rose-600 dark:text-rose-400 font-bold'">{{ report().numerical_validation?.debt_ratio_compliant ? 'Conforme à la limite BCT' : 'Dépassement du seuil légal' }}</span></div>
              </div>
            </div>

            @if (report().blocking_issues?.length) {
              <div class="space-y-2">
                <h3 class="text-xs font-bold text-rose-700 dark:text-rose-400 uppercase tracking-wider">Points Bloquants Identifiés</h3>
                @for (block of report().blocking_issues; track $index) {
                  <div class="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-200 text-xs font-semibold flex items-center gap-2">
                    <span>⚠️</span>
                    <span>{{ block }}</span>
                  </div>
                }
              </div>
            }

            @if (report().regulatory_references?.length) {
              <div class="space-y-2">
                <h3 class="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Références Réglementaires BCT Appliquées</h3>
                <div class="flex flex-wrap gap-2">
                  @for (ref of report().regulatory_references; track $index) {
                    <span class="px-2.5 py-1 rounded-lg bg-[var(--bg-page-subtle)] border border-[var(--border-card)] text-[var(--text-secondary)] text-xs font-semibold">
                      📜 {{ ref }}
                    </span>
                  }
                </div>
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
  applicantName = 'Ahmed Ben Ali';
  loanType = 'personal';
  income = 3500;
  monthlyDebt = 350;
  loanAnnuity = 450;
  uploadedFiles: string[] = ['cin_recto_verso.pdf', 'bulletin_paie_recent.pdf', 'releve_bancaire_3mois.pdf', 'attestation_travail.pdf'];
  report = signal<any>(null);
  loading = signal(false);

  loadPreset(type: string) {
    if (type === 'approve') {
      this.applicantName = 'Karim Mansour';
      this.loanType = 'personal';
      this.income = 4000;
      this.monthlyDebt = 300;
      this.loanAnnuity = 600;
      this.uploadedFiles = ['cin.pdf', 'bulletin_paie.pdf', 'releve_bancaire.pdf', 'attestation_travail.pdf'];
    } else if (type === 'reject_debt') {
      this.applicantName = 'Sami Trabelsi';
      this.loanType = 'personal';
      this.income = 2000;
      this.monthlyDebt = 750;
      this.loanAnnuity = 300;
      this.uploadedFiles = ['cin.pdf', 'bulletin_paie.pdf', 'releve_bancaire.pdf', 'attestation_travail.pdf'];
    } else if (type === 'missing_docs') {
      this.applicantName = 'Leila Bouazizi';
      this.loanType = 'mortgage';
      this.income = 2800;
      this.monthlyDebt = 200;
      this.loanAnnuity = 500;
      this.uploadedFiles = ['cin.pdf'];
    }
  }

  onFilesSelected(event: any) {
    if (event.target.files && event.target.files.length > 0) {
      this.uploadedFiles = Array.from(event.target.files).map((f: any) => f.name);
    }
  }

  prescreen() {
    if (!this.applicantName) return;
    this.loading.set(true);

    this.api.prescreenCredit({
      dossier_id: `cred_${Date.now().toString().slice(-4)}`,
      applicant_name: this.applicantName,
      loan_type: this.loanType,
      files: this.uploadedFiles,
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
