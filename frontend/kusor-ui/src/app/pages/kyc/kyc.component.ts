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
    <div class="p-8 max-w-7xl mx-auto space-y-8">
      <div class="glass-card p-8 relative overflow-hidden">
        <div class="absolute -right-20 -top-20 w-80 h-80 bg-[#E85D04]/10 rounded-full blur-3xl pointer-events-none"></div>
        <h1 class="text-3xl font-black brand-gradient-text">Module 2: Contrôle de Conformité AML / KYC</h1>
        <p class="text-sm text-slate-400 mt-1">Analyse des pièces de dossier d'ouverture de compte et filtrage sanctions (OFAC/UE/ONU)</p>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Input Form -->
        <div class="glass-card p-6 space-y-5">
          <div>
            <label class="block text-[11px] font-extrabold text-slate-300 uppercase tracking-wider mb-2">Nom du Client / Raison Sociale</label>
            <input type="text" [(ngModel)]="clientName" placeholder="ex: Société Immobilière X"
              class="w-full px-4 py-3 rounded-xl bg-[#090D28] border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-[#E85D04] transition-all" />
          </div>

          <div>
            <label class="block text-[11px] font-extrabold text-slate-300 uppercase tracking-wider mb-2">Type de Client</label>
            <select [(ngModel)]="clientType" class="w-full px-4 py-3 rounded-xl bg-[#090D28] border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-[#E85D04] transition-all">
              <option value="individual">Personne Physique</option>
              <option value="corporate">Personne Morale</option>
            </select>
          </div>

          <div>
            <label class="block text-[11px] font-extrabold text-slate-300 uppercase tracking-wider mb-2">Fichiers du Dossier (Liste séparée par des virgules)</label>
            <input type="text" [(ngModel)]="dossierFilesText" placeholder="ex: rne_extrait.pdf, cin_gerant.pdf"
              class="w-full px-4 py-3 rounded-xl bg-[#090D28] border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-[#E85D04] transition-all" />
          </div>

          <button (click)="runCheck()" [disabled]="loading() || !clientName"
            class="w-full py-3.5 rounded-xl font-bold text-white bg-gradient-to-r from-[#FAA307] via-[#E85D04] to-[#DC2F02] hover:from-[#E85D04] hover:to-[#9D0208] disabled:opacity-50 shadow-xl shadow-[#E85D04]/30 transition-all text-sm">
            {{ loading() ? 'Vérification en cours...' : 'Exécuter l\'analyse KYC' }}
          </button>
        </div>

        <!-- Output Report -->
        <div class="lg:col-span-2 glass-card p-8 space-y-6">
          @if (!report()) {
            <div class="flex flex-col items-center justify-center h-64 text-slate-500 italic font-medium">
              Remplissez les détails du dossier et lancez la vérification.
            </div>
          } @else {
            <div class="flex items-center justify-between border-b border-slate-800 pb-5">
              <div>
                <h2 class="text-xl font-black text-white">{{ report().client_name }}</h2>
                <div class="text-xs text-slate-400 font-medium mt-0.5">ID Dossier: {{ report().dossier_id }}</div>
              </div>
              <app-severity-badge [severity]="report().overall_risk"></app-severity-badge>
            </div>

            <div class="grid grid-cols-2 gap-6">
              <div class="p-5 rounded-2xl bg-[#090D28] border border-slate-800/80 text-center space-y-1">
                <div class="text-[10px] text-slate-400 uppercase font-black tracking-wider">Score de Complétude</div>
                <div class="text-3xl font-black text-[#E85D04]">{{ (report().completeness_score * 100).toFixed(0) }}%</div>
              </div>

              <div class="p-5 rounded-2xl bg-[#090D28] border border-slate-800/80 text-center space-y-1">
                <div class="text-[10px] text-slate-400 uppercase font-black tracking-wider">Filtrage Sanctions</div>
                <div [class]="report().sanctions_hit ? 'text-rose-400 text-xl font-black' : 'text-emerald-400 text-xl font-black'">
                  {{ report().sanctions_hit ? '⚠️ MATCH DETECTÉ' : '✅ CONFORME' }}
                </div>
              </div>
            </div>

            <div class="space-y-3">
              <h3 class="text-xs font-black text-slate-300 uppercase tracking-wider">Recommandations & Actions</h3>
              @for (rec of report().recommendations; track $index) {
                <div class="p-4 rounded-xl bg-[#E85D04]/10 border border-[#E85D04]/20 text-[#E85D04] text-xs font-semibold">
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
