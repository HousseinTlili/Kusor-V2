import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { SeverityBadgeComponent } from '../../shared/components/severity-badge/severity-badge.component';

interface DocSlot {
  code: string;
  name: string;
  category: string;
  required: boolean;
  file: File | null;
  fileName: string;
  fileSize: number;
}

@Component({
  selector: 'app-kyc',
  standalone: true,
  imports: [CommonModule, FormsModule, SeverityBadgeComponent],
  template: `
    <div class="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
      
      <!-- Header Banner -->
      <div class="glass-card p-6 md:p-8 relative overflow-hidden">
        <div class="space-y-1 z-10 relative">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#E85D04]/10 text-[#E85D04] text-xs font-bold uppercase tracking-wider">
            <span>🛡️ Conformité & Sécurité Financière</span>
          </div>
          <h1 class="text-2xl md:text-3xl font-black text-[var(--text-primary)]">Contrôle de Conformité AML / KYC</h1>
          <p class="text-sm text-[var(--text-muted)] max-w-3xl">
            Emplacements précis par pièce justificative avec vérification automatique de complétude et filtrage sanctions BCT / CTAF / OFAC.
          </p>
        </div>
      </div>

      <!-- Quick Demo Presets Bar -->
      <div class="glass-card p-4 flex flex-wrap items-center justify-between gap-3 text-xs shadow-sm">
        <div class="flex items-center flex-wrap gap-2">
          <span class="font-bold text-[var(--text-muted)] uppercase tracking-wider text-[10px]">Cas Types Démonstration :</span>
          <button (click)="loadDemoPreset('individual_clean')" class="px-3 py-1.5 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-500 border border-emerald-500/20 font-semibold transition-all shadow-sm">
            ✓ Individuel Conforme (Tous Slots)
          </button>
          <button (click)="loadDemoPreset('sanctions_hit')" class="px-3 py-1.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 border border-rose-500/20 font-semibold transition-all shadow-sm">
            ⚠️ Match Sanction (Ali Trabelsi)
          </button>
          <button (click)="loadDemoPreset('corporate_clean')" class="px-3 py-1.5 rounded-xl bg-blue-500/10 hover:bg-blue-500/20 text-blue-500 border border-blue-500/20 font-semibold transition-all shadow-sm">
            🏢 Personne Morale (RNE + Statuts)
          </button>
        </div>
        <div class="text-[11px] text-[var(--text-muted)] font-medium">
          Slots complétés : <strong class="text-emerald-500">{{ getFilledSlotsCount() }}</strong> / {{ getActiveSlots().length }}
        </div>
      </div>

      <!-- TOP SECTION: Horizontal Inputs & Document Slots -->
      <div class="glass-card p-6 space-y-6 shadow-sm">
        
        <!-- Top Parameter Controls Row -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label class="block text-[11px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1.5">Type de Client</label>
            <select [(ngModel)]="clientType" (change)="onClientTypeChange()"
              class="w-full px-3.5 py-2.5 rounded-xl bg-[var(--bg-input)] border border-[var(--border-input)] text-[var(--text-primary)] text-xs font-semibold focus:outline-none focus:border-[#E85D04] transition-all">
              <option value="individuel">Personne Physique</option>
              <option value="corporate">Personne Morale (Corporate)</option>
              <option value="ppe">Personne PPE</option>
            </select>
          </div>

          <div>
            <label class="block text-[11px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1.5">Nom du Client</label>
            <input type="text" [(ngModel)]="clientName" placeholder="Auto-extrait du document si vide"
              class="w-full px-3.5 py-2.5 rounded-xl bg-[var(--bg-input)] border border-[var(--border-input)] text-[var(--text-primary)] text-xs focus:outline-none focus:border-[#E85D04] transition-all" />
          </div>

          <div>
            <label class="block text-[11px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1.5">Montant du Dépôt Initial (TND)</label>
            <input type="number" [(ngModel)]="depositAmount" placeholder="0"
              class="w-full px-3.5 py-2.5 rounded-xl bg-[var(--bg-input)] border border-[var(--border-input)] text-[var(--text-primary)] text-xs focus:outline-none focus:border-[#E85D04] transition-all" />
          </div>
        </div>

        <!-- Horizontal Document Slots Grid (2, 3, or 4 cols) -->
        <div class="space-y-3 pt-2">
          <div class="text-[11px] font-bold text-[var(--text-secondary)] uppercase tracking-wider flex items-center justify-between">
            <span>Emplacements des Pièces Justificatives (Circulaire BCT 2018-09) :</span>
            <span class="text-[10px] text-[var(--text-muted)]">Glissez ou déposez vos fichiers PDF</span>
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
                    <span class="text-[9px] font-bold px-2 py-0.5 rounded-full uppercase"
                      [ngClass]="slot.required ? 'bg-amber-500/10 text-amber-500 border border-amber-500/20' : 'bg-[var(--bg-input)] text-[var(--text-muted)]'">
                      {{ slot.required ? 'Obligatoire' : 'Conditionnel' }}
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
          <button (click)="submitKycCheck()" [disabled]="isLoading()"
            class="py-3.5 px-8 rounded-xl bg-gradient-to-r from-[#E85D04] to-[#F48C06] hover:from-[#DC2F02] hover:to-[#E85D04] text-white font-bold text-sm shadow-lg shadow-[#E85D04]/25 transition-all flex items-center justify-center gap-2 disabled:opacity-50 min-w-[260px]">
            @if (isLoading()) {
              <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              <span>Extraction & Contrôle en cours...</span>
            } @else {
              <span>🛡️ Lancer le Contrôle KYC</span>
            }
          </button>
        </div>

      </div>

      <!-- BOTTOM SECTION: Full-Width Results Display -->
      @if (report(); as r) {
        <div class="glass-card p-6 md:p-8 border-l-4 space-y-6 shadow-sm"
          [ngClass]="{
            'border-l-emerald-500': r.verdict === 'Conforme',
            'border-l-amber-500': r.verdict === 'Non conforme',
            'border-l-rose-500': r.verdict === 'Escaladé'
          }">
          
          <!-- Executive Verdict Header -->
          <div class="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[var(--border-card)]">
            <div>
              <div class="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Résultat d'Analyse Dossier Client</div>
              <h2 class="text-2xl md:text-3xl font-black text-[var(--text-primary)] mt-0.5">{{ r.client_name }}</h2>
              <div class="text-xs text-[var(--text-secondary)] mt-0.5">Dossier ID : <span class="font-mono text-[var(--text-muted)]">{{ r.dossier_id }}</span> | Type : <span class="uppercase font-bold text-[var(--text-primary)]">{{ r.client_type }}</span></div>
            </div>
            <div class="flex items-center gap-4">
              <div class="text-right">
                <div class="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider mb-1">Niveau de Risque</div>
                <app-severity-badge [severity]="r.overall_risk"></app-severity-badge>
              </div>
              <div class="px-6 py-3 rounded-2xl text-base font-black tracking-wider uppercase border shadow-sm"
                [ngClass]="{
                  'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20': r.verdict === 'Conforme',
                  'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20': r.verdict === 'Non conforme',
                  'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20': r.verdict === 'Escaladé'
                }">
                {{ r.verdict }}
              </div>
            </div>
          </div>

          <!-- Key Metrics Row (4 Columns) -->
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="p-4 rounded-xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)]">
              <div class="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Complétude Pièces</div>
              <div class="text-2xl font-black text-[var(--text-primary)] mt-1">{{ (r.completeness_score * 100) | number:'1.0-0' }}%</div>
            </div>
            <div class="p-4 rounded-xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)]">
              <div class="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Qualité Extraction</div>
              <div class="text-2xl font-black text-emerald-500 mt-1">{{ (r.extraction_quality_score * 100) | number:'1.0-0' }}%</div>
            </div>
            <div class="p-4 rounded-xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)]">
              <div class="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Filtrage Sanctions</div>
              <div class="text-base font-black mt-1.5" [ngClass]="r.sanctions_hit ? 'text-rose-500' : 'text-emerald-500'">
                {{ r.sanctions_hit ? '⚠️ MATCH IDENTIFIÉ' : '✓ AUCUN MATCH' }}
              </div>
            </div>
            <div class="p-4 rounded-xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)]">
              <div class="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Confiance Agent</div>
              <div class="text-2xl font-black text-[#E85D04] mt-1">{{ (r.agent_confidence * 100) | number:'1.0-0' }}%</div>
            </div>
          </div>

          <!-- Sanctions Hit Alert Box -->
          @if (r.sanctions_hit) {
            <div class="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-600 dark:text-rose-400 space-y-2">
              <div class="flex items-center gap-2 font-black text-sm">
                <span>🚨 ALERTE SANCTIONS FINANCIÈRES (CTAF / OFAC / ONU)</span>
              </div>
              @for (s of r.sanctions_results; track s.list_name) {
                @if (s.match_found) {
                  <div class="text-xs space-y-1 bg-rose-500/5 p-3 rounded-xl border border-rose-500/20">
                    <div>Liste : <strong class="font-mono">{{ s.list_name }}</strong></div>
                    <div>Cible identifiée : <strong>{{ s.matched_name }}</strong> (Similarité : {{ (s.match_score * 100) | number:'1.0-0' }}%)</div>
                  </div>
                }
              }
            </div>
          }

          <!-- Two Column Details Row: Extracted Entities & Checklist -->
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            <!-- Left: Extracted Entities Details -->
            @if (r.extracted_entities) {
              <div class="p-5 rounded-2xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)] space-y-3">
                <div class="font-bold text-xs text-[var(--text-primary)] uppercase tracking-wider flex items-center gap-2">
                  <span>🔍 Données Extraites des Pièces :</span>
                </div>
                <div class="space-y-2 text-xs text-[var(--text-secondary)]">
                  @if (r.extracted_entities.cin) {
                    <div class="flex items-center justify-between border-b border-[var(--border-card)] pb-1.5">
                      <span>Numéro CIN :</span>
                      <strong class="font-mono text-[var(--text-primary)]">{{ r.extracted_entities.cin.cin_number || 'N/A' }}</strong>
                    </div>
                    <div class="flex items-center justify-between border-b border-[var(--border-card)] pb-1.5">
                      <span>Date de Naissance :</span>
                      <strong class="text-[var(--text-primary)]">{{ r.extracted_entities.cin.date_of_birth || 'N/A' }}</strong>
                    </div>
                    <div class="flex items-center justify-between border-b border-[var(--border-card)] pb-1.5">
                      <span>Adresse :</span>
                      <strong class="text-[var(--text-primary)]">{{ r.extracted_entities.cin.address || 'N/A' }}</strong>
                    </div>
                  }
                  @if (r.extracted_entities.salary) {
                    <div class="flex items-center justify-between border-b border-[var(--border-card)] pb-1.5">
                      <span>Employeur :</span>
                      <strong class="text-[var(--text-primary)]">{{ r.extracted_entities.salary.employer_name || 'N/A' }}</strong>
                    </div>
                    <div class="flex items-center justify-between border-b border-[var(--border-card)] pb-1.5">
                      <span>Salaire Net Vérifié :</span>
                      <strong class="text-emerald-500 font-bold">{{ r.extracted_entities.salary.net_monthly_salary | number:'1.2-2' }} TND</strong>
                    </div>
                  }
                  @if (r.extracted_entities.corporate) {
                    <div class="flex items-center justify-between border-b border-[var(--border-card)] pb-1.5">
                      <span>Raison Sociale :</span>
                      <strong class="text-[var(--text-primary)]">{{ r.extracted_entities.corporate.company_name || 'N/A' }}</strong>
                    </div>
                    <div class="flex items-center justify-between border-b border-[var(--border-card)] pb-1.5">
                      <span>Matricule RNE :</span>
                      <strong class="font-mono text-[var(--text-primary)]">{{ r.extracted_entities.corporate.registration_number || 'N/A' }}</strong>
                    </div>
                  }
                </div>
              </div>
            }

            <!-- Right: Document Checklist Audit -->
            <div class="p-5 rounded-2xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)] space-y-3">
              <div class="font-bold text-xs text-[var(--text-primary)] uppercase tracking-wider">
                Contrôle des Pièces Obligatoires (BCT) :
              </div>
              <div class="space-y-2">
                @for (doc of r.document_checks; track doc.document_name) {
                  <div class="p-2.5 rounded-xl bg-[var(--bg-card)] border border-[var(--border-card)] flex items-center justify-between gap-3 text-xs">
                    <div class="flex items-center gap-2.5">
                      <span class="w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold"
                        [ngClass]="doc.is_valid ? 'bg-emerald-500/20 text-emerald-500' : 'bg-rose-500/20 text-rose-500'">
                        {{ doc.is_valid ? '✓' : '✕' }}
                      </span>
                      <span class="font-medium text-[var(--text-primary)] text-[11px]">{{ doc.document_name }}</span>
                    </div>
                    <span class="text-[10px] font-semibold" [ngClass]="doc.is_valid ? 'text-emerald-500' : 'text-rose-500'">
                      {{ doc.notes }}
                    </span>
                  </div>
                }
              </div>
            </div>

          </div>

          <!-- Recommendations Section -->
          @if (r.recommendations.length > 0) {
            <div class="space-y-2 pt-2 border-t border-[var(--border-card)]">
              <h3 class="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider">Actions & Mesures Recommandées</h3>
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
export class KycComponent {
  private api = inject(ApiService);

  clientName = '';
  clientType = 'individuel';
  depositAmount = 0;

  individualSlots: DocSlot[] = [
    { code: 'cin', name: "Carte d'Identité Nationale (CIN / Passeport)", category: 'IDENTITE', required: true, file: null, fileName: '', fileSize: 0 },
    { code: 'domicile', name: "Justificatif Domicile (< 3 mois, STEG / SONEDE)", category: 'DOMICILE', required: true, file: null, fileName: '', fileSize: 0 },
    { code: 'salaire', name: "Justificatif Revenus (Bulletin de paie)", category: 'REVENUS', required: true, file: null, fileName: '', fileSize: 0 },
    { code: 'signature', name: "Spécimen de Signature & Formulaire KYC", category: 'SIGNATURE', required: true, file: null, fileName: '', fileSize: 0 },
  ];

  corporateSlots: DocSlot[] = [
    { code: 'rne', name: "Registre National des Entreprises (RNE)", category: 'LEGAL', required: true, file: null, fileName: '', fileSize: 0 },
    { code: 'statuts', name: "Statuts de la Société à jour", category: 'LEGAL', required: true, file: null, fileName: '', fileSize: 0 },
    { code: 'be', name: "Déclaration des Bénéficiaires Effectifs (> 25%)", category: 'AML', required: true, file: null, fileName: '', fileSize: 0 },
    { code: 'pv', name: "Procès-Verbal Nomination Signataires", category: 'GOUVERNANCE', required: true, file: null, fileName: '', fileSize: 0 },
  ];

  ppeSlots: DocSlot[] = [
    { code: 'cin', name: "Pièce d'Identité de la PPE (CIN / Passeport)", category: 'IDENTITE', required: true, file: null, fileName: '', fileSize: 0 },
    { code: 'fonction', name: "Justificatif du Mandat ou de la Fonction", category: 'PPE', required: true, file: null, fileName: '', fileSize: 0 },
    { code: 'fonds', name: "Déclaration Détaillée Origine des Fonds", category: 'AML', required: true, file: null, fileName: '', fileSize: 0 },
  ];

  report = signal<any | null>(null);
  isLoading = signal(false);

  getActiveSlots(): DocSlot[] {
    if (this.clientType === 'corporate') return this.corporateSlots;
    if (this.clientType === 'ppe') return this.ppeSlots;
    return this.individualSlots;
  }

  getFilledSlotsCount(): number {
    return this.getActiveSlots().filter(s => s.file !== null).length;
  }

  getSlotIcon(code: string): string {
    switch (code) {
      case 'cin': return '🪪';
      case 'domicile': return '🏠';
      case 'salaire': return '💼';
      case 'signature': return '✍️';
      case 'rne': return '🏢';
      case 'statuts': return '📜';
      case 'be': return '👥';
      case 'pv': return '📑';
      case 'fonction': return '👔';
      case 'fonds': return '💰';
      default: return '📄';
    }
  }

  onClientTypeChange() {
    this.report.set(null);
  }

  onSlotFileSelected(event: any, slot: DocSlot) {
    const file = event.target.files[0];
    if (file) {
      slot.file = file;
      slot.fileName = file.name;
      slot.fileSize = file.size;
    }
  }

  clearSlot(slot: DocSlot) {
    slot.file = null;
    slot.fileName = '';
    slot.fileSize = 0;
  }

  loadDemoPreset(preset: string) {
    this.isLoading.set(true);
    let payload: any = {};

    if (preset === 'individual_clean') {
      this.clientType = 'individuel';
      this.clientName = 'Mohamed Ben Salem';
      this.individualSlots[0].fileName = 'fake_cin.pdf';
      this.individualSlots[0].fileSize = 58900;
      this.individualSlots[1].fileName = 'fake_proof_of_address.pdf';
      this.individualSlots[1].fileSize = 64200;
      this.individualSlots[2].fileName = 'fake_salary_slip.pdf';
      this.individualSlots[2].fileSize = 67100;
      this.individualSlots[3].fileName = 'specimen_signature.pdf';
      this.individualSlots[3].fileSize = 42000;

      payload = {
        client_name: 'Mohamed Ben Salem',
        client_type: 'individuel',
        dossier_files: [
          { code: 'cin_valide', name: "Carte d'identité nationale (CIN)", present: true, expired: false },
          { code: 'justificatif_domicile', name: "Justificatif de domicile de moins de 3 mois", present: true, expired: false },
          { code: 'bulletin_salaire', name: "Justificatif de revenus / bulletin de salaire", present: true, expired: false },
          { code: 'specimen_signature', name: "Spécimen de signature", present: true, expired: false }
        ]
      };
    } else if (preset === 'sanctions_hit') {
      this.clientType = 'individuel';
      this.clientName = 'Ali Trabelsi';
      this.individualSlots[0].fileName = 'cin_ali_trabelsi.pdf';
      this.individualSlots[0].fileSize = 51200;
      this.individualSlots[1].fileName = 'domicile_gamart.pdf';
      this.individualSlots[1].fileSize = 48000;
      this.individualSlots[2].fileName = '';
      this.individualSlots[3].fileName = '';

      payload = {
        client_name: 'Ali Trabelsi',
        client_type: 'individuel',
        dossier_files: [
          { code: 'cin_valide', name: "Carte d'identité nationale (CIN)", present: true, expired: false },
          { code: 'justificatif_domicile', name: "Justificatif de domicile", present: true, expired: false }
        ]
      };
    } else if (preset === 'corporate_clean') {
      this.clientType = 'corporate';
      this.clientName = 'Société Tunisienne de Services SARL';
      this.corporateSlots[0].fileName = 'extrait_rne_2026.pdf';
      this.corporateSlots[0].fileSize = 88400;
      this.corporateSlots[1].fileName = 'statuts_societe_sarl.pdf';
      this.corporateSlots[1].fileSize = 142000;
      this.corporateSlots[2].fileName = 'liste_beneficiaires_effectifs.pdf';
      this.corporateSlots[2].fileSize = 53000;
      this.corporateSlots[3].fileName = 'pv_nomination_gerance.pdf';
      this.corporateSlots[3].fileSize = 61000;

      payload = {
        client_name: 'Société Tunisienne de Services SARL',
        client_type: 'corporate',
        dossier_files: [
          { code: 'rne', name: "Registre de commerce (RNE)", present: true, expired: false },
          { code: 'statuts_societe', name: "Statuts de la société", present: true, expired: false },
          { code: 'liste_beneficiaires_effectifs', name: "Liste des bénéficiaires effectifs", present: true, expired: false },
          { code: 'pv_nomination_signataires', name: "Procès-verbal de nomination des signataires", present: true, expired: false }
        ]
      };
    }

    this.api.runKycCheck(payload).subscribe({
      next: (res) => {
        this.report.set(res);
        this.isLoading.set(false);
      },
      error: () => this.isLoading.set(false)
    });
  }

  submitKycCheck() {
    this.isLoading.set(true);
    const formData = new FormData();
    if (this.clientName) formData.append('client_name', this.clientName);
    formData.append('client_type', this.clientType);
    if (this.depositAmount) formData.append('deposit_amount_tnd', this.depositAmount.toString());

    const slots = this.getActiveSlots();
    slots.forEach(slot => {
      if (slot.file) {
        formData.append('files', slot.file, slot.fileName);
      }
    });

    this.api.runKycCheck(formData).subscribe({
      next: (res) => {
        this.report.set(res);
        this.isLoading.set(false);
      },
      error: () => this.isLoading.set(false)
    });
  }
}
