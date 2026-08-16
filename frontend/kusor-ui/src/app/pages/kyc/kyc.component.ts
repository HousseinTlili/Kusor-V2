import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { SeverityBadgeComponent } from '../../shared/components/severity-badge/severity-badge.component';

@Component({
  selector: 'app-kyc',
  standalone: true,
  imports: [CommonModule, FormsModule, SeverityBadgeComponent],
  template: `
    <div class="p-6 md:p-8 max-w-7xl mx-auto space-y-8">
      
      <!-- Header Banner -->
      <div class="glass-card p-6 md:p-8 relative overflow-hidden">
        <div class="space-y-1 z-10 relative">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#E85D04]/10 text-[#E85D04] text-xs font-bold uppercase tracking-wider">
            <span>🛡️ Conformité & Sécurité Financière</span>
          </div>
          <h1 class="text-2xl md:text-3xl font-black text-[var(--text-primary)]">Contrôle de Conformité AML / KYC</h1>
          <p class="text-sm text-[var(--text-muted)] max-w-2xl">
            Analyse des pièces de dossier d'ouverture de compte et filtrage sanctions (OFAC, UE, ONU, GAFI) selon les circulaires BCT.
          </p>
        </div>
      </div>

      <!-- Quick Demo Presets Bar -->
      <div class="glass-card p-4 flex flex-wrap items-center gap-3 text-xs shadow-sm">
        <span class="font-bold text-[var(--text-muted)] uppercase tracking-wider text-[10px] mr-2">Cas Types de Démonstration :</span>
        <button (click)="loadPreset('corporate_clean')" class="px-3.5 py-1.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 hover:bg-emerald-100 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800 font-semibold transition-all shadow-sm">
          ✓ Personne Morale Conforme
        </button>
        <button (click)="loadPreset('sanctions_hit')" class="px-3.5 py-1.5 rounded-xl bg-rose-50 dark:bg-rose-950/30 hover:bg-rose-100 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-800 font-semibold transition-all shadow-sm">
          ⚠️ Match Sanction OFAC
        </button>
        <button (click)="loadPreset('individual_incomplete')" class="px-3.5 py-1.5 rounded-xl bg-amber-50 dark:bg-amber-950/30 hover:bg-amber-100 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800 font-semibold transition-all shadow-sm">
          ⏳ Personne Physique Incomplète
        </button>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        <!-- Input Form -->
        <div class="glass-card p-6 space-y-5 shadow-sm">
          <div>
            <label class="block text-[11px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-2">Nom du Client / Raison Sociale</label>
            <input type="text" [(ngModel)]="clientName" placeholder="ex: Société Immobilière Tunisienne"
              class="w-full px-4 py-3 rounded-xl bg-[var(--bg-input)] border border-[var(--border-input)] text-[var(--text-primary)] text-sm focus:outline-none focus:border-[#E85D04] focus:ring-2 focus:ring-[#E85D04]/20 transition-all" />
          </div>

          <div>
            <label class="block text-[11px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-2">Type de Client</label>
            <select [(ngModel)]="clientType" class="w-full px-4 py-3 rounded-xl bg-[var(--bg-input)] border border-[var(--border-input)] text-[var(--text-primary)] text-sm focus:outline-none focus:border-[#E85D04] focus:ring-2 focus:ring-[#E85D04]/20 transition-all">
              <option value="individual">Personne Physique</option>
              <option value="corporate">Personne Morale</option>
            </select>
          </div>

          <!-- File Upload Section -->
          <div>
            <label class="block text-[11px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-2">Téléverser les Pièces du Dossier (PDF / Documents)</label>
            <div class="border-2 border-dashed border-[var(--border-card-hover)] hover:border-[#E85D04] rounded-2xl p-5 text-center bg-[var(--bg-page-subtle)] transition-all cursor-pointer relative">
              <input type="file" multiple (change)="onFilesSelected($event)" class="absolute inset-0 opacity-0 cursor-pointer w-full h-full" />
              <svg class="w-8 h-8 text-[var(--text-muted)] mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
              </svg>
              <div class="text-xs text-[var(--text-primary)] font-bold">Cliquez ou glissez-déposez des fichiers PDF</div>
              <div class="text-[10px] text-[var(--text-muted)] mt-1">Extraits RNE, CIN, Statuts, Déclaration BE...</div>
            </div>
            
            @if (uploadedFileNames.length > 0) {
              <div class="mt-3 space-y-1.5">
                <div class="text-[10px] uppercase font-bold text-[var(--text-muted)]">Fichiers sélectionnés ({{ uploadedFileNames.length }}) :</div>
                <div class="flex flex-wrap gap-1.5">
                  @for (file of uploadedFileNames; track $index) {
                    <span class="inline-flex items-center px-2.5 py-1 rounded-lg bg-[#E85D04]/10 border border-[#E85D04]/20 text-[#E85D04] text-[11px] font-medium">
                      📄 {{ file }}
                    </span>
                  }
                </div>
              </div>
            }
          </div>

          <div>
            <label class="block text-[11px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-2">Ou Liste Manuelle des Fichiers (séparés par des virgules)</label>
            <input type="text" [(ngModel)]="dossierFilesText" placeholder="ex: rne_extrait.pdf, cin_gerant.pdf"
              class="w-full px-4 py-3 rounded-xl bg-[var(--bg-input)] border border-[var(--border-input)] text-[var(--text-primary)] text-xs focus:outline-none focus:border-[#E85D04] transition-all" />
          </div>

          <button (click)="runCheck()" [disabled]="loading() || !clientName"
            class="w-full py-3.5 rounded-xl font-bold brand-btn-primary disabled:opacity-50 transition-all text-xs flex items-center justify-center gap-2">
            @if (loading()) {
              <svg class="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>Vérification AML / KYC en cours...</span>
            } @else {
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
              </svg>
              <span>Exécuter l'analyse KYC</span>
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
              <span>Sélectionnez un cas de démonstration ou remplissez le formulaire pour lancer le contrôle AML/KYC.</span>
            </div>
          } @else {
            <div class="flex items-center justify-between border-b border-[var(--border-card)] pb-5">
              <div>
                <h2 class="text-xl font-black text-[var(--text-primary)]">{{ report().client_name }}</h2>
                <div class="text-xs text-[var(--text-muted)] font-medium mt-0.5">ID Dossier: {{ report().dossier_id }} | Type: {{ report().client_type === 'corporate' ? 'Personne Morale' : 'Personne Physique' }}</div>
              </div>
              <app-severity-badge [severity]="report().overall_risk"></app-severity-badge>
            </div>

            <!-- Metric Cards -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div class="p-5 rounded-2xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)] text-center space-y-1">
                <div class="text-[10px] text-[var(--text-muted)] uppercase font-bold tracking-wider">Score de Complétude</div>
                <div class="text-3xl font-black text-[#E85D04]">{{ (report().completeness_score * 100).toFixed(0) }}%</div>
                <div class="text-[10px] text-[var(--text-muted)]">Verdict: <strong>{{ report().verdict }}</strong></div>
              </div>

              <div class="p-5 rounded-2xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)] text-center space-y-1">
                <div class="text-[10px] text-[var(--text-muted)] uppercase font-bold tracking-wider">Filtrage Sanctions</div>
                <div [class]="report().sanctions_hit ? 'text-rose-600 dark:text-rose-400 text-lg font-black' : 'text-emerald-600 dark:text-emerald-400 text-lg font-black'">
                  {{ report().sanctions_hit ? '⚠️ MATCH DETECTÉ' : '✅ CONFORME' }}
                </div>
                <div class="text-[10px] text-[var(--text-muted)]">Bases: OFAC, UE, ONU</div>
              </div>

              <div class="p-5 rounded-2xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)] text-center space-y-1">
                <div class="text-[10px] text-[var(--text-muted)] uppercase font-bold tracking-wider">Confiance de l'Agent</div>
                <div class="text-3xl font-black text-emerald-600 dark:text-emerald-400">{{ ((report().agent_confidence || 0.95) * 100).toFixed(0) }}%</div>
                <div class="text-[10px] text-[var(--text-muted)]">Vérifié par KUSOR v3</div>
              </div>
            </div>

            <!-- Document Checklist Status -->
            @if (report().document_checks?.length) {
              <div class="space-y-3">
                <h3 class="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider">Contrôle des Pièces Requises (Checklist BCT)</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                  @for (chk of report().document_checks; track chk.document_name) {
                    <div class="p-3.5 rounded-xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)] flex items-center justify-between text-xs">
                      <div class="font-medium text-[var(--text-secondary)]">{{ chk.document_name }}</div>
                      @if (chk.is_present) {
                        <span class="px-2 py-0.5 rounded-md bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800 text-[10px] font-bold">✓ Présent</span>
                      } @else {
                        <span class="px-2 py-0.5 rounded-md bg-rose-50 dark:bg-rose-950/30 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-800 text-[10px] font-bold">✗ Manquant</span>
                      }
                    </div>
                  }
                </div>
              </div>
            }

            <!-- Recommendations & Actions -->
            <div class="space-y-3">
              <h3 class="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider">Recommandations & Actions Conformité</h3>
              @for (rec of report().recommendations; track $index) {
                <div class="p-4 rounded-xl bg-orange-50 dark:bg-orange-950/30 border border-orange-200 dark:border-orange-900/40 text-orange-900 dark:text-orange-200 text-xs font-medium flex items-start gap-2.5">
                  <span class="text-base leading-none">📋</span>
                  <span>{{ rec }}</span>
                </div>
              }
            </div>
          }
        </div>
      </div>
    </div>
  `
})
export class KycComponent {
  api = inject(ApiService);
  clientName = 'Société Immobilière Tunisienne';
  clientType = 'corporate';
  dossierFilesText = 'rne_extrait.pdf, statuts_societe.pdf, cin_gerant.pdf, declaration_beneficiaire_effectif.pdf';
  uploadedFileNames: string[] = ['rne_extrait.pdf', 'statuts_societe.pdf', 'cin_gerant.pdf'];
  report = signal<any>(null);
  loading = signal(false);

  loadPreset(type: string) {
    if (type === 'corporate_clean') {
      this.clientName = 'Société Maghrébine de Distribution SARL';
      this.clientType = 'corporate';
      this.dossierFilesText = 'rne_extrait.pdf, statuts_societe.pdf, cin_gerant.pdf, declaration_beneficiaire_effectif.pdf, justificatif_adresse.pdf';
      this.uploadedFileNames = ['rne_extrait.pdf', 'statuts_societe.pdf', 'cin_gerant.pdf', 'declaration_beneficiaire_effectif.pdf', 'justificatif_adresse.pdf'];
    } else if (type === 'sanctions_hit') {
      this.clientName = 'Al-Baraka Trading International';
      this.clientType = 'corporate';
      this.dossierFilesText = 'rne_extrait.pdf, statuts.pdf';
      this.uploadedFileNames = ['rne_extrait.pdf', 'statuts.pdf'];
    } else if (type === 'individual_incomplete') {
      this.clientName = 'Mohamed Ali Gharbi';
      this.clientType = 'individual';
      this.dossierFilesText = 'cin_recto.pdf';
      this.uploadedFileNames = ['cin_recto.pdf'];
    }
  }

  onFilesSelected(event: any) {
    if (event.target.files && event.target.files.length > 0) {
      this.uploadedFileNames = Array.from(event.target.files).map((f: any) => f.name);
      this.dossierFilesText = this.uploadedFileNames.join(', ');
    }
  }

  runCheck() {
    if (!this.clientName) return;
    this.loading.set(true);

    const files = this.dossierFilesText.split(',').map(s => s.trim()).filter(Boolean);
    this.api.runKycCheck({
      client_name: this.clientName,
      client_type: this.clientType,
      dossier_files: files
    }).subscribe({
      next: (res) => {
        this.report.set(res);
        this.loading.set(false);
      },
      error: (err) => {
        console.error('KYC check error', err);
        this.loading.set(false);
      }
    });
  }
}
