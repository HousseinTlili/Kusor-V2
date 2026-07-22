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
    <div class="max-w-7xl mx-auto p-6 space-y-6">
      <div class="glass-card p-6">
        <h1 class="text-2xl font-bold gold-gradient-text">Module 2: Contrôle de Conformité AML / KYC</h1>
        <p class="text-sm text-slate-400 mt-1">Analyse des pièces de dossier d'ouverture de compte et filtrage sanctions (OFAC/UE/ONU)</p>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Input Form -->
        <div class="glass-card p-6 space-y-4">
          <div>
            <label class="block text-xs font-semibold text-slate-300 uppercase mb-1">Nom du Client / Raison Sociale</label>
            <input type="text" [(ngModel)]="clientName" placeholder="ex: Société Immobilière X"
              class="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-amber-500" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-300 uppercase mb-1">Type de Client</label>
            <select [(ngModel)]="clientType" class="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-amber-500">
              <option value="individual">Personne Physique</option>
              <option value="corporate">Personne Morale</option>
            </select>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-300 uppercase mb-1">Fichiers du Dossier (Noms ou fichiers)</label>
            <input type="text" [(ngModel)]="dossierFilesText" placeholder="ex: rne_extrait.pdf, cin_gerant.pdf"
              class="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-amber-500" />
          </div>

          <button (click)="runCheck()" [disabled]="loading() || !clientName"
            class="w-full py-3 rounded-xl font-bold text-slate-950 bg-gradient-to-r from-amber-400 to-amber-500 hover:from-amber-300 hover:to-amber-400 disabled:opacity-50 transition-all">
            {{ loading() ? 'Vérification en cours...' : 'Exécuter l\'analyse KYC' }}
          </button>
        </div>

        <!-- Output Report -->
        <div class="lg:col-span-2 glass-card p-6 space-y-6">
          @if (!report()) {
            <div class="flex flex-col items-center justify-center h-64 text-slate-500 italic">
              Remplissez les détails du dossier et lancez la vérification.
            </div>
          } @else {
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h2 class="text-lg font-bold text-slate-100">{{ report().client_name }}</h2>
                <div class="text-xs text-slate-400">ID Dossier: {{ report().dossier_id }}</div>
              </div>
              <app-severity-badge [severity]="report().overall_risk"></app-severity-badge>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div class="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-center">
                <div class="text-xs text-slate-400 uppercase">Score de Complétude</div>
                <div class="text-2xl font-extrabold text-amber-400 mt-1">{{ (report().completeness_score * 100).toFixed(0) }}%</div>
              </div>

              <div class="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-center">
                <div class="text-xs text-slate-400 uppercase">Filtrage Sanctions</div>
                <div [class]="report().sanctions_hit ? 'text-rose-400 text-lg font-extrabold' : 'text-emerald-400 text-lg font-extrabold'" class="mt-1">
                  {{ report().sanctions_hit ? '⚠️ MATCH SANCTIONS' : '✅ CONFORME' }}
                </div>
              </div>
            </div>

            <div class="space-y-2">
              <h3 class="text-sm font-semibold text-slate-300">Recommandations & Actions</h3>
              @for (rec of report().recommendations; track $index) {
                <div class="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs">
                  • {{ rec }}
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
  clientName = '';
  clientType = 'corporate';
  dossierFilesText = 'rne_extrait.pdf, statuts_societe.pdf, cin_gerant.pdf';
  report = signal<any>(null);
  loading = signal(false);

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
      error: () => this.loading.set(false)
    });
  }
}
