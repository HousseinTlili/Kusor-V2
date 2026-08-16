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
    <div class="p-6 md:p-8 max-w-7xl mx-auto space-y-8">
      
      <!-- Header Banner -->
      <div class="glass-card p-6 md:p-8 relative overflow-hidden">
        <div class="space-y-1 z-10 relative">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950/30 text-indigo-700 dark:text-indigo-400 text-xs font-bold uppercase tracking-wider border border-indigo-200 dark:border-indigo-800">
            <span>⚖️ Affaires Juridiques & Réglementaires</span>
          </div>
          <h1 class="text-2xl md:text-3xl font-black text-[var(--text-primary)]">Analyse de Risque de Contrat Bancaire</h1>
          <p class="text-sm text-[var(--text-muted)] max-w-2xl">
            Segmentation automatique des clauses et vérification de conformité temporelle par rapport aux circulaires BCT en vigueur.
          </p>
        </div>
      </div>

      <!-- Quick Demo Presets Bar -->
      <div class="glass-card p-4 flex flex-wrap items-center gap-3 text-xs shadow-sm">
        <span class="font-bold text-[var(--text-muted)] uppercase tracking-wider text-[10px] mr-2">Modèles Types de Contrats :</span>
        <button (click)="loadPreset('pret_immo')" class="px-3.5 py-1.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 hover:bg-emerald-100 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800 font-semibold transition-all shadow-sm">
          ✓ Prêt Immobilier Standard
        </button>
        <button (click)="loadPreset('taux_usure')" class="px-3.5 py-1.5 rounded-xl bg-rose-50 dark:bg-rose-950/30 hover:bg-rose-100 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-800 font-semibold transition-all shadow-sm">
          ⚠️ Clause Risquée (Pénalité Usuraire)
        </button>
        <button (click)="loadPreset('compte_courant')" class="px-3.5 py-1.5 rounded-xl bg-indigo-50 dark:bg-indigo-950/30 hover:bg-indigo-100 text-indigo-700 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800 font-semibold transition-all shadow-sm">
          📄 Convention de Compte Bancaire
        </button>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        <!-- Input Form -->
        <div class="glass-card p-6 space-y-5 shadow-sm">
          <div>
            <label class="block text-[11px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-2">Titre du Modèle de Contrat</label>
            <input type="text" [(ngModel)]="title" placeholder="ex: Convention de Prêt Immobilier 2026"
              class="w-full px-4 py-3 rounded-xl bg-[var(--bg-input)] border border-[var(--border-input)] text-[var(--text-primary)] text-sm focus:outline-none focus:border-[#E85D04] focus:ring-2 focus:ring-[#E85D04]/20 transition-all" />
          </div>

          <!-- File Upload Option -->
          <div>
            <label class="block text-[11px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-2">Téléverser un Contrat (PDF / DOCX / TXT)</label>
            <div class="border-2 border-dashed border-[var(--border-card-hover)] hover:border-[#E85D04] rounded-2xl p-4 text-center bg-[var(--bg-page-subtle)] transition-all cursor-pointer relative">
              <input type="file" (change)="onFileSelected($event)" accept=".pdf,.docx,.txt" class="absolute inset-0 opacity-0 cursor-pointer w-full h-full" />
              <svg class="w-7 h-7 text-[var(--text-muted)] mx-auto mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
              </svg>
              <div class="text-xs text-[var(--text-primary)] font-bold">Sélectionner un contrat PDF / DOCX</div>
              @if (selectedFileName) {
                <div class="text-[11px] text-[#E85D04] font-semibold mt-1">✓ {{ selectedFileName }}</div>
              }
            </div>
          </div>

          <div>
            <label class="block text-[11px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-2">Ou Texte des Clauses à Analyser</label>
            <textarea [(ngModel)]="text" rows="7" placeholder="Collez ici les articles et clauses du contrat..."
              class="w-full px-4 py-3 rounded-xl bg-[var(--bg-input)] border border-[var(--border-input)] text-[var(--text-primary)] text-xs font-mono focus:outline-none focus:border-[#E85D04] transition-all leading-relaxed"></textarea>
          </div>

          <button (click)="analyze()" [disabled]="loading() || (!text && !selectedFile)"
            class="w-full py-3.5 rounded-xl font-bold brand-btn-primary disabled:opacity-50 transition-all text-xs flex items-center justify-center gap-2 shadow-sm">
            @if (loading()) {
              <svg class="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>Analyse des clauses en cours...</span>
            } @else {
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>
              </svg>
              <span>Analyser la Conformité du Contrat</span>
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
              <span>Sélectionnez un modèle type ou collez des clauses pour vérifier la conformité BCT.</span>
            </div>
          } @else {
            <div class="flex items-center justify-between border-b border-[var(--border-card)] pb-5">
              <div>
                <h2 class="text-xl font-black text-[var(--text-primary)]">{{ report().contract_title }}</h2>
                <div class="text-xs text-[var(--text-muted)] font-medium mt-0.5">Total Clauses Analysées : <strong>{{ report().total_clauses }}</strong> | Non-Conformités : <strong class="text-rose-600 dark:text-rose-400">{{ report().non_conformity_count }}</strong></div>
              </div>
              <app-severity-badge [severity]="report().overall_risk"></app-severity-badge>
            </div>

            <!-- Metric Cards -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div class="p-4 rounded-2xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)] text-center space-y-1">
                <div class="text-[10px] text-[var(--text-muted)] uppercase font-bold tracking-wider">Risque Global</div>
                <div class="text-2xl font-black text-[var(--text-primary)]">{{ report().overall_risk }}</div>
              </div>
              <div class="p-4 rounded-2xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)] text-center space-y-1">
                <div class="text-[10px] text-[var(--text-muted)] uppercase font-bold tracking-wider">Anomalies Critiques</div>
                <div class="text-2xl font-black text-rose-600 dark:text-rose-400">{{ report().critical_issues || 0 }}</div>
              </div>
              <div class="p-4 rounded-2xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)] text-center space-y-1">
                <div class="text-[10px] text-[var(--text-muted)] uppercase font-bold tracking-wider">Validité Temporelle</div>
                <div class="text-2xl font-black text-emerald-600 dark:text-emerald-400">100% Vérifiée</div>
              </div>
            </div>

            <div class="space-y-4">
              <h3 class="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider">Détail des Clauses Analysées (Taxonomie BCT)</h3>
              @for (c of report().clauses; track c.clause_number) {
                <div class="p-5 rounded-2xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)] space-y-3 text-xs">
                  <div class="flex justify-between items-center">
                    <span class="font-bold text-[#E85D04] text-sm">Clause N° {{ c.clause_number }} (Type : {{ c.clause_type }})</span>
                    <app-severity-badge [severity]="c.conformity_status"></app-severity-badge>
                  </div>
                  <p class="text-[var(--text-secondary)] leading-relaxed font-mono text-[11px] bg-[var(--bg-card)] p-3.5 rounded-xl border border-[var(--border-card)]">{{ c.clause_text }}</p>
                  @if (c.regulatory_basis_ref) {
                    <div class="text-[11px] text-[var(--text-muted)]">
                      Base Réglementaire : <strong class="text-amber-600 dark:text-amber-400">{{ c.regulatory_basis_ref }}</strong> (Statut BCT : <span class="text-emerald-600 dark:text-emerald-400 font-bold">En vigueur</span>)
                    </div>
                  }
                </div>
              }
            </div>

            @if (report().recommendations?.length) {
              <div class="space-y-2">
                <h3 class="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider">Recommandations Juridiques</h3>
                @for (rec of report().recommendations; track $index) {
                  <div class="p-3.5 rounded-xl bg-orange-50 dark:bg-orange-950/30 border border-orange-200 dark:border-orange-900/40 text-orange-900 dark:text-orange-200 text-xs font-medium">
                    • {{ rec }}
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
export class ContractComponent {
  api = inject(ApiService);
  title = 'Convention de Prêt Immobilier 2026';
  text = `Article 1 - Objet du Prêt\nLe prêteur accorde à l'emprunteur un prêt immobilier d'un montant de 150 000 TND au taux d'intérêt de 8.25% l'an conformément aux règles BCT.\n\nArticle 2 - Pénalités de Retard\nEn cas de défaillance, des pénalités de retard équivalentes à 2.0% majoré du taux usuraire légal seront appliquées.`;
  selectedFile: File | null = null;
  selectedFileName = '';
  report = signal<any>(null);
  loading = signal(false);

  loadPreset(preset: string) {
    if (preset === 'pret_immo') {
      this.title = 'Convention de Prêt Immobilier Attijari';
      this.text = `Article 1 - Objet\nPrêt bancaire amortissable de 120 000 TND remboursable sur une durée de 240 mois au taux nominal de 7.85%.\n\nArticle 2 - Garanties Exigées\nHypothèque de premier rang sur le bien financé et souscription obligatoire d'une assurance décès-invalidité.`;
    } else if (preset === 'taux_usure') {
      this.title = 'Contrat de Facilité de Caisse avec Clause Risquée';
      this.text = `Article 1 - Montant et Taux\nFacilité de caisse de 50 000 TND au taux d'intérêt conventionnel de 19.5% l'an.\n\nArticle 2 - Indemnités Forfaitaires\nEn cas de dépassement, une indemnité d'exigibilité immédiate de 25% sera facturée sans mise en demeure préalable.`;
    } else if (preset === 'compte_courant') {
      this.title = 'Convention de Compte Courant Professionnel';
      this.text = `Article 1 - Conditions d'Ouverture\nOuverture de compte subordonnée à la fourniture de l'extrait RNE datant de moins de 3 mois et à l'identification du bénéficiaire effectif.\n\nArticle 2 - Droit de Clôture\nChaque partie peut résilier la convention par lettre recommandée avec accusé de réception sous préavis de 30 jours.`;
    }
    this.selectedFile = null;
    this.selectedFileName = '';
  }

  onFileSelected(event: any) {
    if (event.target.files && event.target.files.length > 0) {
      this.selectedFile = event.target.files[0];
      this.selectedFileName = this.selectedFile?.name || '';
      this.title = this.selectedFileName.replace(/\.[^/.]+$/, '');
    }
  }

  analyze() {
    this.loading.set(true);

    if (this.selectedFile) {
      const formData = new FormData();
      formData.append('file', this.selectedFile);
      formData.append('title', this.title);
      this.api.analyzeContract(formData).subscribe({
        next: (res) => {
          this.report.set(res);
          this.loading.set(false);
        },
        error: () => this.loading.set(false)
      });
    } else {
      this.api.analyzeContract({ title: this.title, text: this.text }).subscribe({
        next: (res) => {
          this.report.set(res);
          this.loading.set(false);
        },
        error: () => this.loading.set(false)
      });
    }
  }
}
