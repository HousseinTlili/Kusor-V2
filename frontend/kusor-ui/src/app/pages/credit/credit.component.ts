import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';

interface CreditDocSlot {
  code: string;
  name: string;
  category: string;
  required: boolean;
  file: File | null;
  fileName: string;
  fileSize: number;
}

@Component({
  selector: 'app-credit',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
      
      <!-- Header Banner -->
      <div class="glass-card p-6 md:p-8 relative overflow-hidden">
        <div class="space-y-1 z-10 relative">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-400 text-xs font-bold uppercase tracking-wider border border-emerald-200 dark:border-emerald-800">
            <span>💳 Gestion des Engagements & Risques</span>
          </div>
          <h1 class="text-2xl md:text-3xl font-black text-[var(--text-primary)]">Pré-filtrage de Dossier de Crédit Multi-Agent</h1>
          <p class="text-sm text-[var(--text-muted)] max-w-3xl">
            Emplacements précis par pièce de crédit avec cross-validation automatique entre les 3 sous-agents : Complétude, Calculs financiers (Ratio ≤ 40%), et Concordance.
          </p>
        </div>
      </div>

      <!-- Quick Demo Presets Bar -->
      <div class="glass-card p-4 flex flex-wrap items-center justify-between gap-3 text-xs shadow-sm">
        <div class="flex items-center flex-wrap gap-2">
          <span class="font-bold text-[var(--text-muted)] uppercase tracking-wider text-[10px]">Cas Types Démonstration :</span>
          <button (click)="loadDemoPreset('hypothecaire_review')" class="px-3.5 py-1.5 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-500 border border-amber-500/20 font-semibold transition-all shadow-sm">
            ⏳ Prêt Hypothécaire 150k TND (Endettement 43% — À Réviser)
          </button>
          <button (click)="loadDemoPreset('personnel_approve')" class="px-3.5 py-1.5 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-500 border border-emerald-500/20 font-semibold transition-all shadow-sm">
            ✓ Prêt Personnel 30k TND (Endettement 22% — APPROUVÉ)
          </button>
          <button (click)="loadDemoPreset('reject_debt')" class="px-3.5 py-1.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 border border-rose-500/20 font-semibold transition-all shadow-sm">
            ⚠️ Rejet Endettement (54% &gt; 40% BCT)
          </button>
        </div>
        <div class="text-[11px] text-[var(--text-muted)] font-medium">
          Pièces chargées : <strong class="text-emerald-500">{{ getFilledSlotsCount() }}</strong> / {{ getActiveSlots().length }}
        </div>
      </div>

      <!-- TOP SECTION: Horizontal Inputs & Document Slots -->
      <div class="glass-card p-6 space-y-6 shadow-sm">
        
        <!-- Financial Parameters Row -->
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div>
            <label class="block text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1">Type de Prêt</label>
            <select [(ngModel)]="loanType" (change)="onLoanTypeChange()"
              class="w-full px-3 py-2 rounded-xl bg-[var(--bg-input)] border border-[var(--border-input)] text-[var(--text-primary)] text-xs font-semibold focus:outline-none focus:border-[#E85D04] transition-all">
              <option value="hypothecaire">Hypothécaire</option>
              <option value="personnel">Personnel</option>
              <option value="pme">Financement PME</option>
            </select>
          </div>

          <div>
            <label class="block text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1">Emprunteur</label>
            <input type="text" [(ngModel)]="applicantName" placeholder="Auto-extrait si vide"
              class="w-full px-3 py-2 rounded-xl bg-[var(--bg-input)] border border-[var(--border-input)] text-[var(--text-primary)] text-xs focus:outline-none focus:border-[#E85D04] transition-all" />
          </div>

          <div>
            <label class="block text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1">Montant Prêt (TND)</label>
            <input type="number" [(ngModel)]="declaredAmount" placeholder="150000"
              class="w-full px-3 py-2 rounded-xl bg-[var(--bg-input)] border border-[var(--border-input)] text-[var(--text-primary)] text-xs focus:outline-none focus:border-[#E85D04] transition-all" />
          </div>

          <div>
            <label class="block text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1">Durée (Mois)</label>
            <input type="number" [(ngModel)]="declaredTerm" placeholder="240"
              class="w-full px-3 py-2 rounded-xl bg-[var(--bg-input)] border border-[var(--border-input)] text-[var(--text-primary)] text-xs focus:outline-none focus:border-[#E85D04] transition-all" />
          </div>

          <div>
            <label class="block text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1">Revenu Déclaré (TND)</label>
            <input type="number" [(ngModel)]="declaredIncome" placeholder="2800"
              class="w-full px-3 py-2 rounded-xl bg-[var(--bg-input)] border border-[var(--border-input)] text-[var(--text-primary)] text-xs focus:outline-none focus:border-[#E85D04] transition-all" />
          </div>

          <div>
            <label class="block text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1">Dettes En Cours (TND)</label>
            <input type="number" [(ngModel)]="existingDebts" placeholder="0"
              class="w-full px-3 py-2 rounded-xl bg-[var(--bg-input)] border border-[var(--border-input)] text-[var(--text-primary)] text-xs focus:outline-none focus:border-[#E85D04] transition-all" />
          </div>
        </div>

        <!-- Horizontal Document Slots Grid (4 Columns) -->
        <div class="space-y-3 pt-2">
          <div class="text-[11px] font-bold text-[var(--text-secondary)] uppercase tracking-wider flex items-center justify-between">
            <span>Pièces Justificatives du Dossier de Prêt :</span>
            <span class="text-[10px] text-[var(--text-muted)]">Glissez ou déposez chaque document</span>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            @for (slot of getActiveSlots(); track slot.code) {
              <div class="p-4 rounded-2xl border transition-all flex flex-col justify-between"
                [ngClass]="{
                  'bg-emerald-500/5 border-emerald-500/30': slot.file !== null,
                  'bg-[var(--bg-page-subtle)] border-[var(--border-card)] hover:border-[#E85D04]/40': slot.file === null
                }">
                
                <div class="space-y-1.5 mb-3">
                  <div class="flex items-center justify-between gap-1">
                    <span class="text-sm">{{ getSlotIcon(slot.code) }}</span>
                    <span class="text-[9px] font-bold px-2 py-0.5 rounded-full uppercase bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                      Obligatoire
                    </span>
                  </div>
                  <div class="text-xs font-bold text-[var(--text-primary)] line-clamp-2 min-h-[32px]">{{ slot.name }}</div>
                </div>

                @if (slot.file) {
                  <div class="flex items-center justify-between gap-2 p-2 rounded-xl bg-[var(--bg-input)] border border-emerald-500/30 text-xs">
                    <div class="flex items-center gap-1.5 truncate">
                      <span class="text-emerald-500 font-bold text-xs">✓</span>
                      <span class="font-medium text-[var(--text-primary)] truncate text-[11px]">{{ slot.fileName }}</span>
                    </div>
                    <button (click)="clearSlot(slot)" class="text-rose-500 hover:text-rose-700 font-bold px-1 text-xs">✕</button>
                  </div>
                } @else {
                  <div class="relative border border-dashed border-[var(--border-card-hover)] hover:border-[#E85D04] rounded-xl p-3 text-center bg-[var(--bg-card)] transition-all cursor-pointer">
                    <input type="file" (change)="onSlotFileSelected($event, slot)" accept=".pdf,.png,.jpg,.jpeg" class="absolute inset-0 opacity-0 cursor-pointer w-full h-full" />
                    <div class="text-[11px] text-[var(--text-muted)] flex flex-col items-center gap-1">
                      <span class="text-base">📤</span>
                      <span class="text-[10px]">Déposer ou <strong>choisir</strong></span>
                    </div>
                  </div>
                }

              </div>
            }
          </div>
        </div>

        <!-- Action Button Row -->
        <div class="flex justify-end pt-2">
          <button (click)="submitCreditCheck()" [disabled]="isLoading()"
            class="py-3.5 px-8 rounded-xl bg-gradient-to-r from-[#E85D04] to-[#F48C06] hover:from-[#DC2F02] hover:to-[#E85D04] text-white font-bold text-sm shadow-lg shadow-[#E85D04]/25 transition-all flex items-center justify-center gap-2 disabled:opacity-50 min-w-[280px]">
            @if (isLoading()) {
              <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              <span>Évaluation des 3 Sous-Agents...</span>
            } @else {
              <span>📊 Lancer la Pré-qualification de Crédit</span>
            }
          </button>
        </div>

      </div>

      <!-- BOTTOM SECTION: Full-Width Results Display -->
      @if (report(); as r) {
        <div class="glass-card p-6 md:p-8 border-l-4 space-y-6 shadow-sm"
          [ngClass]="{
            'border-l-emerald-500': r.overall_verdict === 'APPROVE',
            'border-l-amber-500': r.overall_verdict === 'REVIEW',
            'border-l-rose-500': r.overall_verdict === 'REJECT'
          }">
          
          <!-- Supervisor Verdict Banner -->
          <div class="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[var(--border-card)]">
            <div>
              <div class="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Verdict Superviseur de Crédit</div>
              <h2 class="text-2xl md:text-3xl font-black text-[var(--text-primary)] mt-0.5">{{ r.applicant_name }}</h2>
              <div class="text-xs text-[var(--text-secondary)] mt-0.5">Type de Prêt : <span class="font-bold uppercase text-[var(--text-primary)]">{{ r.loan_type }}</span> | Dossier ID : <span class="font-mono text-[var(--text-muted)]">{{ r.dossier_id }}</span></div>
            </div>
            <div class="flex items-center gap-4">
              <div class="text-right">
                <div class="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider mb-1">Risque Global</div>
                <span class="px-3 py-1 rounded-full text-xs font-bold uppercase"
                  [ngClass]="r.overall_risk === 'LOW' ? 'bg-emerald-500/10 text-emerald-500' : (r.overall_risk === 'MEDIUM' ? 'bg-amber-500/10 text-amber-500' : 'bg-rose-500/10 text-rose-500')">
                  {{ r.overall_risk }}
                </span>
              </div>
              <div class="px-6 py-3 rounded-2xl text-base font-black tracking-wider uppercase border shadow-sm"
                [ngClass]="{
                  'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20': r.overall_verdict === 'APPROVE',
                  'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20': r.overall_verdict === 'REVIEW',
                  'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20': r.overall_verdict === 'REJECT'
                }">
                {{ r.overall_verdict }}
              </div>
            </div>
          </div>

          <!-- 3 Specialist Sub-Agents Multi-Card Row -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            <!-- Sub-Agent 1: Completeness -->
            <div class="p-5 rounded-2xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)] space-y-3">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider">1. Sous-Agent Complétude</span>
                <span class="text-xs font-black px-2 py-0.5 rounded-full"
                  [ngClass]="r.document_completeness.verdict === 'COMPLET' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-amber-500/10 text-amber-500'">
                  {{ r.document_completeness.verdict }}
                </span>
              </div>
              <div class="text-3xl font-black text-[var(--text-primary)]">
                {{ (r.document_completeness.completeness_ratio * 100) | number:'1.0-0' }}%
              </div>
              <div class="text-xs text-[var(--text-secondary)] space-y-1">
                <div>Pièces fournies : <strong>{{ r.document_completeness.present_documents.length }}</strong> sur {{ r.document_completeness.required_documents.length }}</div>
                @if (r.document_completeness.missing_documents.length > 0) {
                  <div class="text-rose-500 text-[11px]">Manquant : {{ r.document_completeness.missing_documents.join(', ') }}</div>
                }
              </div>
            </div>

            <!-- Sub-Agent 2: Numerical Validation -->
            <div class="p-5 rounded-2xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)] space-y-3">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider">2. Sous-Agent Financier</span>
                <span class="text-xs font-black px-2 py-0.5 rounded-full"
                  [ngClass]="r.numerical_validation.debt_ratio_compliant ? 'bg-emerald-500/10 text-emerald-500' : 'bg-rose-500/10 text-rose-500'">
                  {{ r.numerical_validation.debt_ratio_compliant ? '≤ 40% BCT' : '> 40% BCT' }}
                </span>
              </div>
              <div class="text-3xl font-black" [ngClass]="r.numerical_validation.debt_ratio_compliant ? 'text-emerald-500' : 'text-rose-500'">
                {{ r.numerical_validation.debt_ratio | number:'1.1-1' }}%
              </div>
              <div class="text-xs text-[var(--text-secondary)] space-y-1">
                <div>Revenu Vérifié : <strong>{{ r.numerical_validation.income_verified | number:'1.0-0' }} TND</strong></div>
                <div>Revenu Déclaré : <strong>{{ r.numerical_validation.income_declared | number:'1.0-0' }} TND</strong></div>
              </div>
            </div>

            <!-- Sub-Agent 3: Identity Cross-Ref -->
            <div class="p-5 rounded-2xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)] space-y-3">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider">3. Sous-Agent Concordance</span>
                <span class="text-xs font-black px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500">
                  {{ r.identity_cross_reference.verdict }}
                </span>
              </div>
              <div class="text-3xl font-black text-[var(--text-primary)]">
                {{ r.identity_cross_reference.name_consistent ? '✓ Validé' : '⚠️ Incohérent' }}
              </div>
              <div class="text-xs text-[var(--text-secondary)] space-y-1">
                <div>Profil Risque KYC : <strong class="text-emerald-500">{{ r.identity_cross_reference.kyc_risk_profile }}</strong></div>
                <div>Numéro ID Unique : <strong>{{ r.identity_cross_reference.id_number_consistent ? 'Concordant' : 'Anomalie' }}</strong></div>
              </div>
            </div>

          </div>

          <!-- Blocking Issues / Warnings Alert -->
          @if (r.blocking_issues && r.blocking_issues.length > 0) {
            <div class="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-600 dark:text-amber-400 space-y-2">
              <div class="font-bold text-xs flex items-center gap-2">
                <span>⚠️ Points d'Attention & Anomalies Détectées :</span>
              </div>
              <ul class="space-y-1 text-xs list-disc list-inside">
                @for (issue of r.blocking_issues; track issue) {
                  <li>{{ issue }}</li>
                }
              </ul>
            </div>
          }

          <!-- Regulatory References Footer -->
          @if (r.regulatory_references && r.regulatory_references.length > 0) {
            <div class="space-y-2 pt-2 border-t border-[var(--border-card)]">
              <div class="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Fondements Réglementaires BCT</div>
              <div class="flex flex-wrap gap-2">
                @for (ref of r.regulatory_references; track ref) {
                  <span class="px-3 py-1.5 rounded-xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)] text-xs text-[var(--text-secondary)]">
                    📜 {{ ref }}
                  </span>
                }
              </div>
            </div>
          }

        </div>
      }

    </div>
  `,
  styles: []
})
export class CreditComponent {
  private api = inject(ApiService);

  applicantName = '';
  loanType = 'hypothecaire';
  declaredAmount = 150000;
  declaredTerm = 240;
  declaredIncome = 2800;
  existingDebts = 0;

  mortgageSlots: CreditDocSlot[] = [
    { code: 'cin', name: "Carte d'Identité Emprunteur (CIN)", category: 'IDENTITE', required: true, file: null, fileName: '', fileSize: 0 },
    { code: 'salaire', name: "3 Derniers Bulletins de Salaire", category: 'REVENUS', required: true, file: null, fileName: '', fileSize: 0 },
    { code: 'expertise', name: "Rapport d'Expertise Vénale du Bien", category: 'GARANTIE', required: true, file: null, fileName: '', fileSize: 0 },
    { code: 'compromis', name: "Compromis de Vente Signé", category: 'OPERATION', required: true, file: null, fileName: '', fileSize: 0 },
  ];

  personalSlots: CreditDocSlot[] = [
    { code: 'cin', name: "Carte d'Identité Emprunteur (CIN)", category: 'IDENTITE', required: true, file: null, fileName: '', fileSize: 0 },
    { code: 'salaire', name: "3 Derniers Bulletins de Salaire", category: 'REVENUS', required: true, file: null, fileName: '', fileSize: 0 },
    { code: 'attestation', name: "Attestation Employeur Récente", category: 'PROFESSIONNEL', required: true, file: null, fileName: '', fileSize: 0 },
  ];

  pmeSlots: CreditDocSlot[] = [
    { code: 'rne', name: "Extrait RNE & Statuts de l'Entreprise", category: 'LEGAL', required: true, file: null, fileName: '', fileSize: 0 },
    { code: 'bilans', name: "États Financiers Certifiés (3 ans)", category: 'FINANCES', required: true, file: null, fileName: '', fileSize: 0 },
    { code: 'plan', name: "Business Plan & Plan de Trésorerie", category: 'PROJET', required: true, file: null, fileName: '', fileSize: 0 },
  ];

  report = signal<any | null>(null);
  isLoading = signal(false);

  getActiveSlots(): CreditDocSlot[] {
    if (this.loanType === 'hypothecaire') return this.mortgageSlots;
    if (this.loanType === 'personnel') return this.personalSlots;
    return this.pmeSlots;
  }

  getFilledSlotsCount(): number {
    return this.getActiveSlots().filter(s => s.file !== null).length;
  }

  getSlotIcon(code: string): string {
    switch (code) {
      case 'cin': return '🪪';
      case 'salaire': return '📑';
      case 'expertise': return '🏠';
      case 'compromis': return '🤝';
      case 'attestation': return '🏢';
      case 'rne': return '🏛️';
      case 'bilans': return '📊';
      case 'plan': return '📈';
      default: return '📄';
    }
  }

  onLoanTypeChange() {
    this.report.set(null);
  }

  onSlotFileSelected(event: any, slot: CreditDocSlot) {
    const file = event.target.files[0];
    if (file) {
      slot.file = file;
      slot.fileName = file.name;
      slot.fileSize = file.size;
    }
  }

  clearSlot(slot: CreditDocSlot) {
    slot.file = null;
    slot.fileName = '';
    slot.fileSize = 0;
  }

  loadDemoPreset(preset: string) {
    this.isLoading.set(true);
    let payload: any = {};

    if (preset === 'hypothecaire_review') {
      this.loanType = 'hypothecaire';
      this.applicantName = 'Mohamed Ben Salem';
      this.declaredAmount = 150000;
      this.declaredTerm = 240;
      this.declaredIncome = 2800;
      this.existingDebts = 0;

      this.mortgageSlots[0].fileName = 'fake_cin.pdf';
      this.mortgageSlots[0].fileSize = 58900;
      this.mortgageSlots[1].fileName = 'fake_salary_slips_3months.pdf';
      this.mortgageSlots[1].fileSize = 82400;
      this.mortgageSlots[2].fileName = 'fake_property_valuation.pdf';
      this.mortgageSlots[2].fileSize = 71300;
      this.mortgageSlots[3].fileName = 'fake_sale_agreement.pdf';
      this.mortgageSlots[3].fileSize = 65000;

      payload = {
        applicant_name: 'Mohamed Ben Salem',
        loan_type: 'hypothecaire',
        declared_amount: 150000,
        declared_term_months: 240,
        financial_data: { declared_income: 2800, verified_income: 2800, existing_debts: 0, monthly_repayment: 1208.5 },
        files: [
          { code: 'cin_valide', name: 'CIN valide', present: true },
          { code: 'bulletins_salaire_3', name: '3 derniers bulletins de salaire', present: true },
          { code: 'compromis_vente', name: 'Compromis de vente', present: true },
          { code: 'rapport_expertise_bien', name: "Rapport d'expertise du bien", present: true }
        ]
      };
    } else if (preset === 'personnel_approve') {
      this.loanType = 'personnel';
      this.applicantName = 'Karim Bouazizi';
      this.declaredAmount = 30000;
      this.declaredTerm = 60;
      this.declaredIncome = 3200;
      this.existingDebts = 0;

      this.personalSlots[0].fileName = 'cin_karim.pdf';
      this.personalSlots[0].fileSize = 51200;
      this.personalSlots[1].fileName = 'salaires_q3.pdf';
      this.personalSlots[1].fileSize = 74000;
      this.personalSlots[2].fileName = 'attestation_travail.pdf';
      this.personalSlots[2].fileSize = 46000;

      payload = {
        applicant_name: 'Karim Bouazizi',
        loan_type: 'personnel',
        declared_amount: 30000,
        declared_term_months: 60,
        financial_data: { declared_income: 3200, verified_income: 3200, existing_debts: 0, monthly_repayment: 608.0 },
        files: [
          { code: 'cin_valide', name: 'CIN valide', present: true },
          { code: 'bulletins_salaire_3', name: '3 derniers bulletins de salaire', present: true },
          { code: 'attestation_employeur', name: 'Attestation employeur', present: true }
        ]
      };
    } else if (preset === 'reject_debt') {
      this.loanType = 'personnel';
      this.applicantName = 'Sami Ben Amor';
      this.declaredAmount = 50000;
      this.declaredTerm = 48;
      this.declaredIncome = 2200;
      this.existingDebts = 400;

      this.personalSlots[0].fileName = 'cin_sami.pdf';
      this.personalSlots[0].fileSize = 49000;
      this.personalSlots[1].fileName = 'bulletins_salaire.pdf';
      this.personalSlots[1].fileSize = 62000;
      this.personalSlots[2].fileName = '';

      payload = {
        applicant_name: 'Sami Ben Amor',
        loan_type: 'personnel',
        declared_amount: 50000,
        declared_term_months: 48,
        financial_data: { declared_income: 2200, verified_income: 2200, existing_debts: 400, monthly_repayment: 1200.0 },
        files: [
          { code: 'cin_valide', name: 'CIN valide', present: true },
          { code: 'bulletins_salaire_3', name: '3 derniers bulletins de salaire', present: true }
        ]
      };
    }

    this.api.prescreenCredit(payload).subscribe({
      next: (res) => {
        this.report.set(res);
        this.isLoading.set(false);
      },
      error: () => this.isLoading.set(false)
    });
  }

  submitCreditCheck() {
    this.isLoading.set(true);
    const formData = new FormData();
    if (this.applicantName) formData.append('applicant_name', this.applicantName);
    formData.append('loan_type', this.loanType);
    formData.append('declared_amount', this.declaredAmount.toString());
    formData.append('declared_term_months', this.declaredTerm.toString());
    formData.append('declared_income', this.declaredIncome.toString());
    formData.append('existing_debts', this.existingDebts.toString());

    const slots = this.getActiveSlots();
    slots.forEach(slot => {
      if (slot.file) {
        formData.append('files', slot.file, slot.fileName);
      }
    });

    this.api.prescreenCredit(formData).subscribe({
      next: (res) => {
        this.report.set(res);
        this.isLoading.set(false);
      },
      error: () => this.isLoading.set(false)
    });
  }
}
