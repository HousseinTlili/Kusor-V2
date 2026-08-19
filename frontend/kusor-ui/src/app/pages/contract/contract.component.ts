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
    <div class="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
      
      <!-- Header Banner -->
      <div class="glass-card p-6 md:p-8 relative overflow-hidden">
        <div class="space-y-1 z-10 relative">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950/30 text-indigo-700 dark:text-indigo-400 text-xs font-bold uppercase tracking-wider border border-indigo-200 dark:border-indigo-800">
            <span>⚖️ Affaires Juridiques & Réglementaires</span>
          </div>
          <h1 class="text-2xl md:text-3xl font-black text-[var(--text-primary)]">Analyse de Risque de Contrat Bancaire</h1>
          <p class="text-sm text-[var(--text-muted)] max-w-3xl">
            Emplacements dédiés pour contrat PDF et avenants avec segmentation automatique des clauses et validation temporelle des circulaires BCT via Neo4j.
          </p>
        </div>
      </div>

      <!-- Quick Demo Presets Bar -->
      <div class="glass-card p-4 flex flex-wrap items-center gap-3 text-xs shadow-sm">
        <span class="font-bold text-[var(--text-muted)] uppercase tracking-wider text-[10px] mr-2">Modèles Types de Contrats :</span>
        <button (click)="loadDemoPreset('pret_immo_pdf')" class="px-3.5 py-1.5 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-500 border border-emerald-500/20 font-semibold transition-all shadow-sm">
          ✓ Convention de Prêt Immobilier (Attijari Bank — 6 Clauses)
        </button>
        <button (click)="loadDemoPreset('taux_usure')" class="px-3.5 py-1.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 border border-rose-500/20 font-semibold transition-all shadow-sm">
          ⚠️ Clause Non-Conforme (Pénalité 5% & Taux Usuraire)
        </button>
      </div>

      <!-- TOP SECTION: Horizontal Inputs & Document Slots -->
      <div class="glass-card p-6 space-y-6 shadow-sm">
        
        <!-- Contract Metadata Row -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label class="block text-[11px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1.5">Titre de la Convention / Modèle</label>
            <input type="text" [(ngModel)]="title" placeholder="ex: Convention de Prêt Immobilier 2026"
              class="w-full px-3.5 py-2.5 rounded-xl bg-[var(--bg-input)] border border-[var(--border-input)] text-[var(--text-primary)] text-xs focus:outline-none focus:border-[#E85D04] transition-all" />
          </div>

          <div>
            <label class="block text-[11px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1.5">Date de Signature</label>
            <input type="date" [(ngModel)]="signingDate"
              class="w-full px-3.5 py-2.5 rounded-xl bg-[var(--bg-input)] border border-[var(--border-input)] text-[var(--text-primary)] text-xs focus:outline-none focus:border-[#E85D04] transition-all" />
          </div>

          <div>
            <label class="block text-[11px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1.5">Type de Contrat</label>
            <select [(ngModel)]="contractType" class="w-full px-3.5 py-2.5 rounded-xl bg-[var(--bg-input)] border border-[var(--border-input)] text-[var(--text-primary)] text-xs focus:outline-none focus:border-[#E85D04] transition-all">
              <option value="credit_immobilier">Prêt Immobilier</option>
              <option value="credit_consommation">Crédit Consommation</option>
              <option value="convention_compte">Convention Compte</option>
            </select>
          </div>
        </div>

        <!-- Horizontal Document Slots Grid (2 Columns) -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          
          <!-- Slot 1: Primary Contract PDF -->
          <div class="p-4 rounded-2xl border transition-all flex flex-col justify-between"
            [ngClass]="selectedFile ? 'bg-emerald-500/5 border-emerald-500/30' : 'bg-[var(--bg-page-subtle)] border-[var(--border-card)] hover:border-[#E85D04]/40'">
            <div class="flex items-center justify-between gap-2 mb-2">
              <div class="flex items-center gap-2">
                <span class="text-base">📜</span>
                <span class="text-xs font-bold text-[var(--text-primary)]">Contrat / Convention Principale (PDF)</span>
              </div>
              <span class="text-[9px] font-bold px-2 py-0.5 rounded-full uppercase bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                Obligatoire
              </span>
            </div>

            @if (selectedFile) {
              <div class="flex items-center justify-between gap-2 p-2.5 rounded-xl bg-[var(--bg-input)] border border-emerald-500/30 text-xs">
                <div class="flex items-center gap-2 truncate">
                  <span class="text-emerald-500 font-bold">✓</span>
                  <span class="font-medium text-[var(--text-primary)] truncate">{{ selectedFileName }}</span>
                </div>
                <button (click)="clearContractFile()" class="text-rose-500 hover:text-rose-700 font-bold px-1.5 text-xs">✕</button>
              </div>
            } @else {
              <div class="relative border border-dashed border-[var(--border-card-hover)] hover:border-[#E85D04] rounded-xl p-3 text-center bg-[var(--bg-card)] transition-all cursor-pointer">
                <input type="file" (change)="onFileSelected($event)" accept=".pdf,.txt" class="absolute inset-0 opacity-0 cursor-pointer w-full h-full" />
                <div class="text-[11px] text-[var(--text-muted)] flex flex-col items-center gap-1">
                  <span class="text-base">📤</span>
                  <span>Déposer le contrat PDF ou <strong>cliquer pour choisir</strong></span>
                </div>
              </div>
            }
          </div>

          <!-- Slot 2: Optional Annex / Fee Schedule -->
          <div class="p-4 rounded-2xl border transition-all flex flex-col justify-between"
            [ngClass]="annexFile ? 'bg-emerald-500/5 border-emerald-500/30' : 'bg-[var(--bg-page-subtle)] border-[var(--border-card)]'">
            <div class="flex items-center justify-between gap-2 mb-2">
              <div class="flex items-center gap-2">
                <span class="text-base">📑</span>
                <span class="text-xs font-bold text-[var(--text-primary)]">Avenant ou Barème Tarifaire BCT</span>
              </div>
              <span class="text-[9px] font-bold px-2 py-0.5 rounded-full uppercase bg-[var(--bg-input)] text-[var(--text-muted)]">
                Optionnel
              </span>
            </div>

            @if (annexFile) {
              <div class="flex items-center justify-between gap-2 p-2.5 rounded-xl bg-[var(--bg-input)] border border-emerald-500/30 text-xs">
                <span class="truncate text-xs font-medium text-[var(--text-primary)]">✓ {{ annexFileName }}</span>
                <button (click)="annexFile = null; annexFileName = ''" class="text-rose-500 hover:text-rose-700 font-bold px-1.5 text-xs">✕</button>
              </div>
            } @else {
              <div class="relative border border-dashed border-[var(--border-card-hover)] rounded-xl p-3 text-center bg-[var(--bg-card)] transition-all cursor-pointer">
                <input type="file" (change)="onAnnexSelected($event)" accept=".pdf,.txt" class="absolute inset-0 opacity-0 cursor-pointer w-full h-full" />
                <div class="text-[11px] text-[var(--text-muted)] flex flex-col items-center gap-1">
                  <span class="text-base">📎</span>
                  <span>Ajouter un avenant (optionnel)</span>
                </div>
              </div>
            }
          </div>

        </div>

        <!-- Or Textarea -->
        <div>
          <label class="block text-[11px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1.5">Ou Coller Directement le Texte des Clauses</label>
          <textarea [(ngModel)]="text" rows="3" placeholder="Collez ici les articles du contrat..."
            class="w-full px-3.5 py-2.5 rounded-xl bg-[var(--bg-input)] border border-[var(--border-input)] text-[var(--text-primary)] text-xs font-mono focus:outline-none focus:border-[#E85D04] transition-all leading-relaxed"></textarea>
        </div>

        <!-- Action Button Row -->
        <div class="flex justify-end pt-2">
          <button (click)="analyze()" [disabled]="loading() || (!text && !selectedFile)"
            class="py-3.5 px-8 rounded-xl bg-gradient-to-r from-[#E85D04] to-[#F48C06] hover:from-[#DC2F02] hover:to-[#E85D04] text-white font-bold text-sm shadow-lg shadow-[#E85D04]/25 transition-all flex items-center justify-center gap-2 disabled:opacity-50 min-w-[280px]">
            @if (loading()) {
              <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              <span>Segmentation & Analyse Temporelle...</span>
            } @else {
              <span>⚖️ Lancer l'Analyse Réglementaire</span>
            }
          </button>
        </div>

      </div>

      <!-- BOTTOM SECTION: Full-Width Results Display -->
      @if (report(); as r) {
        <div class="glass-card p-6 md:p-8 border-l-4 space-y-6 shadow-sm"
          [ngClass]="{
            'border-l-emerald-500': r.overall_risk === 'LOW',
            'border-l-amber-500': r.overall_risk === 'MEDIUM' || r.overall_risk === 'HIGH',
            'border-l-rose-500': r.overall_risk === 'CRITICAL'
          }">
          
          <!-- Executive Risk Banner Header -->
          <div class="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[var(--border-card)]">
            <div>
              <div class="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Rapport d'Analyse Juridique</div>
              <h2 class="text-2xl md:text-3xl font-black text-[var(--text-primary)] mt-0.5">{{ r.contract_title }}</h2>
              <div class="text-xs text-[var(--text-secondary)] mt-0.5">Date de signature : <span class="font-semibold text-[var(--text-primary)]">{{ r.contract_date || 'Non spécifiée' }}</span></div>
            </div>
            <div class="flex items-center gap-3">
              <div class="text-right">
                <div class="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider mb-1">Risque Juridique Global</div>
                <app-severity-badge [severity]="r.overall_risk"></app-severity-badge>
              </div>
            </div>
          </div>

          <!-- Metrics Overview (4 Columns) -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div class="p-4 rounded-xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)]">
              <div class="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Total Clauses</div>
              <div class="text-2xl font-black text-[var(--text-primary)] mt-1">{{ r.total_clauses }}</div>
            </div>
            <div class="p-4 rounded-xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)]">
              <div class="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Non-Conformités</div>
              <div class="text-2xl font-black mt-1" [ngClass]="r.non_conformity_count > 0 ? 'text-rose-500' : 'text-emerald-500'">{{ r.non_conformity_count }}</div>
            </div>
            <div class="p-4 rounded-xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)]">
              <div class="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Alertes Critiques</div>
              <div class="text-2xl font-black mt-1" [ngClass]="r.critical_issues > 0 ? 'text-rose-500' : 'text-emerald-500'">{{ r.critical_issues }}</div>
            </div>
            <div class="p-4 rounded-xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)]">
              <div class="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Validité Temporelle</div>
              <div class="text-base font-black mt-1.5" [ngClass]="r.temporal_issues > 0 ? 'text-amber-500' : 'text-emerald-500'">
                {{ r.temporal_issues > 0 ? r.temporal_issues + ' à réviser' : '✓ Conforme BCT' }}
              </div>
            </div>
          </div>

          <!-- Extracted Contract Metadata Card -->
          @if (r.contract_metadata) {
            <div class="p-5 rounded-2xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)] space-y-3 text-xs">
              <div class="font-bold text-[var(--text-primary)] uppercase tracking-wider">📄 Données Contractuelles Extraites :</div>
              <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-[var(--text-secondary)]">
                <div>• Prêteur : <strong class="text-[var(--text-primary)]">{{ r.contract_metadata.lender_name || 'Attijari Bank' }}</strong></div>
                <div>• Emprunteur : <strong class="text-[var(--text-primary)]">{{ r.contract_metadata.borrower_name || 'N/A' }}</strong></div>
                <div>• Montant : <strong class="text-emerald-500 font-bold">{{ r.contract_metadata.loan_amount_tnd | number:'1.2-2' }} TND</strong></div>
                <div>• Taux / Durée : <strong class="text-[var(--text-primary)]">{{ r.contract_metadata.interest_rate || 'N/A' }} — {{ r.contract_metadata.loan_term_months || 'N/A' }} mois</strong></div>
              </div>
            </div>
          }

          <!-- Clause-by-Clause Analysis Table -->
          <div class="space-y-3 pt-2">
            <h3 class="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider">Détail des Clauses Segmentées & Analysées</h3>
            <div class="grid grid-cols-1 gap-3">
              @for (clause of r.clauses; track clause.clause_number) {
                <div class="p-4 rounded-xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)] space-y-2.5 text-xs">
                  <div class="flex flex-wrap items-center justify-between gap-2">
                    <div class="flex items-center gap-2">
                      <span class="px-2.5 py-0.5 rounded-md bg-[var(--bg-card)] font-mono text-[10px] font-bold text-[var(--text-muted)] border border-[var(--border-card)]">
                        Clause #{{ clause.clause_number }}
                      </span>
                      <span class="px-3 py-0.5 rounded-full bg-indigo-500/10 text-indigo-500 text-[10px] font-bold uppercase">
                        {{ clause.clause_type }}
                      </span>
                    </div>
                    <div class="flex items-center gap-2">
                      <app-severity-badge [severity]="clause.severity"></app-severity-badge>
                      <span class="px-2.5 py-0.5 rounded-md text-[10px] font-bold"
                        [ngClass]="clause.conformity_status === 'CONFORMING' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-rose-500/10 text-rose-500'">
                        {{ clause.conformity_status }}
                      </span>
                    </div>
                  </div>

                  <p class="text-[var(--text-primary)] font-mono text-[11px] bg-[var(--bg-input)] p-3 rounded-xl border border-[var(--border-input)] whitespace-pre-wrap leading-relaxed">
                    {{ clause.clause_text }}
                  </p>

                  <div class="flex flex-wrap items-center justify-between gap-2 text-[11px] text-[var(--text-muted)]">
                    <div>Base Réglementaire BCT : <strong class="text-[var(--text-secondary)] font-mono">{{ clause.regulatory_basis_ref }}</strong></div>
                    <div [ngClass]="clause.regulatory_basis_still_valid ? 'text-emerald-500' : 'text-rose-500'">
                      {{ clause.regulatory_basis_still_valid ? '✓ Circulaire toujours en vigueur' : '⚠️ Modifiée/Abrogée par : ' + clause.superseding_circular }}
                    </div>
                  </div>
                </div>
              }
            </div>
          </div>

          <!-- Recommendations -->
          @if (r.recommendations && r.recommendations.length > 0) {
            <div class="space-y-2 pt-2 border-t border-[var(--border-card)]">
              <h3 class="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider">Recommandations Juridiques</h3>
              <ul class="space-y-1.5 text-xs text-[var(--text-secondary)]">
                @for (rec of r.recommendations; track rec) {
                  <li class="flex items-start gap-2">
                    <span class="text-[#E85D04] font-bold">•</span>
                    <span>{{ rec }}</span>
                  </li>
                }
              </ul>
            </div>
          }

        </div>
      }

    </div>
  `,
  styles: []
})
export class ContractComponent {
  private api = inject(ApiService);

  title = 'Convention de Prêt Immobilier Particulier';
  text = '';
  signingDate = '2019-01-15';
  contractType = 'credit_immobilier';
  selectedFile: File | null = null;
  selectedFileName = '';
  annexFile: File | null = null;
  annexFileName = '';

  report = signal<any | null>(null);
  loading = signal(false);

  onFileSelected(event: any) {
    const file = event.target.files[0];
    if (file) {
      this.selectedFile = file;
      this.selectedFileName = file.name;
    }
  }

  clearContractFile() {
    this.selectedFile = null;
    this.selectedFileName = '';
  }

  onAnnexSelected(event: any) {
    const file = event.target.files[0];
    if (file) {
      this.annexFile = file;
      this.annexFileName = file.name;
    }
  }

  loadDemoPreset(preset: string) {
    this.loading.set(true);

    if (preset === 'pret_immo_pdf') {
      this.title = 'Convention de Crédit Immobilier Particulier';
      this.signingDate = '2019-01-15';
      this.contractType = 'credit_immobilier';
      this.selectedFileName = 'fake_credit_contract.pdf';
      const payload = {
        title: 'Convention de Crédit Immobilier Particulier',
        signing_date: '2019-01-15',
        contract_type: 'credit_immobilier',
        text: `Article 1 : Objet du crédit — Le prêt est consenti exclusivement pour l'acquisition du bien immobilier à La Marsa.
Article 2 : Taux d'intérêt et Révision — Les intérêts sont calculés sur le capital restant dû au taux nominal de 7.50%.
Article 3 : Remboursement anticipé — L'emprunteur peut rembourser par anticipation sans indemnité supérieure à 2 mois d'intérêts selon la Circulaire BCT N° 2016-01.
Article 4 : Garantie et Hypothèque — Inscription d'hypothèque de 1er rang sur le titre foncier 15487/Tunis au profit de la banque.
Article 5 : Résiliation et Déchéance du terme — En cas de défaut de paiement de 3 échéances consécutives, la banque exigera le remboursement intégral.
Article 6 : Juridiction compétente — Tout litige relatif au présent contrat sera soumis aux tribunaux de Tunis.`
      };

      this.api.analyzeContract(payload).subscribe({
        next: (res) => {
          this.report.set(res);
          this.loading.set(false);
        },
        error: () => this.loading.set(false)
      });
    } else if (preset === 'taux_usure') {
      this.title = 'Contrat de Financement avec Pénalités Forfaitaires';
      this.signingDate = '2023-05-10';
      const payload = {
        title: 'Contrat de Financement avec Pénalités Forfaitaires',
        signing_date: '2023-05-10',
        text: `Article 1 : Remboursement anticipé — En cas de remboursement anticipé, l'emprunteur versera une indemnité forfaitaire de 6 mois d'intérêts plus une pénalité de 5% du capital restant dû.
Article 2 : Déchéance — Le taux d'intérêt révisable sans préavis sera majoré unilatéralement par la banque en cas de retard de 15 jours.`
      };

      this.api.analyzeContract(payload).subscribe({
        next: (res) => {
          this.report.set(res);
          this.loading.set(false);
        },
        error: () => this.loading.set(false)
      });
    }
  }

  analyze() {
    this.loading.set(true);

    if (this.selectedFile) {
      const formData = new FormData();
      formData.append('contract_file', this.selectedFile, this.selectedFileName);
      if (this.title) formData.append('title', this.title);
      if (this.signingDate) formData.append('signing_date', this.signingDate);
      if (this.contractType) formData.append('contract_type', this.contractType);
      if (this.annexFile) formData.append('annex_file', this.annexFile, this.annexFileName);

      this.api.analyzeContract(formData).subscribe({
        next: (res) => {
          this.report.set(res);
          this.loading.set(false);
        },
        error: () => this.loading.set(false)
      });
    } else {
      const payload = {
        title: this.title,
        text: this.text,
        signing_date: this.signingDate,
        contract_type: this.contractType
      };

      this.api.analyzeContract(payload).subscribe({
        next: (res) => {
          this.report.set(res);
          this.loading.set(false);
        },
        error: () => this.loading.set(false)
      });
    }
  }
}
