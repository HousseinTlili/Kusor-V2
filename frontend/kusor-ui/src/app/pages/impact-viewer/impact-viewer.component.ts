import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { SeverityBadgeComponent } from '../../shared/components/severity-badge/severity-badge.component';

@Component({
  selector: 'app-impact-viewer',
  standalone: true,
  imports: [CommonModule, FormsModule, SeverityBadgeComponent],
  template: `
    <div class="p-6 md:p-8 max-w-7xl mx-auto space-y-8">
      
      <!-- Header Banner -->
      <div class="glass-card p-6 md:p-8 border-l-4 border-[#E85D04] relative overflow-hidden shadow-sm">
        <div class="space-y-2 z-10 relative">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#E85D04]/10 text-[#E85D04] text-xs font-bold uppercase tracking-wider">
            <span>⚡ Propagation Réglementaire</span>
          </div>
          <h1 class="text-2xl md:text-3xl font-black text-[var(--text-primary)]">Cartographie d'Impact Réglementaire</h1>
          <p class="text-sm text-[var(--text-muted)] max-w-3xl">
            Surveillance et analyse de propagation automatique des circulaires BCT sur les obligations de conformité, processus opérationnels et modèles contractuels d'Attijari Bank.
          </p>
        </div>
      </div>

      <!-- Circular Selector & Search Toolbar -->
      <div class="glass-card p-6 shadow-sm space-y-4">
        <div class="flex flex-col md:flex-row items-stretch md:items-center gap-3">
          <div class="relative flex-1">
            <input 
              type="text" 
              [(ngModel)]="searchQuery" 
              (keyup.enter)="onSearch()"
              placeholder="Entrez une référence de circulaire BCT (ex: 2024-88, 2016-01, 2017-02)..."
              class="w-full pl-10 pr-4 py-3 bg-[var(--bg-page)] border border-[var(--border-card)] rounded-xl text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[#E85D04] transition-all"
            />
            <svg class="w-5 h-5 text-[var(--text-muted)] absolute left-3 top-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>

          <button 
            (click)="onSearch()"
            [disabled]="loading() || !searchQuery.trim()"
            class="px-6 py-3 rounded-xl bg-gradient-to-r from-[#E85D04] to-[#D95000] text-white font-bold text-sm shadow-md hover:shadow-lg disabled:opacity-50 transition-all flex items-center justify-center gap-2 cursor-pointer"
          >
            @if (loading()) {
              <svg class="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>Analyse...</span>
            } @else {
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span>Analyser l'Impact</span>
            }
          </button>
        </div>

        <!-- Quick Presets -->
        <div class="flex flex-wrap items-center gap-2 pt-1">
          <span class="text-xs font-semibold text-[var(--text-muted)]">Circulaires Prédéfinies :</span>
          @for (preset of presets; track preset.id) {
            <button 
              (click)="selectPreset(preset.id)"
              [class.bg-[#E85D04]]="circularId() === preset.id"
              [class.text-white]="circularId() === preset.id"
              [class.bg-[var(--bg-page-subtle)]]="circularId() !== preset.id"
              [class.text-[var(--text-secondary)]]="circularId() !== preset.id"
              class="px-3 py-1.5 rounded-lg text-xs font-semibold border border-[var(--border-card)] hover:border-[#E85D04] transition-all cursor-pointer"
            >
              {{ preset.label }}
            </button>
          }
        </div>
      </div>

      <!-- Main Results Container -->
      <div class="space-y-6">
        @if (loading()) {
          <div class="glass-card p-12 flex flex-col justify-center items-center h-64 text-[var(--text-muted)] font-medium gap-4">
            <svg class="animate-spin h-8 w-8 text-[#E85D04]" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <div class="text-center">
              <div class="text-base font-bold text-[var(--text-primary)]">Parcours du Graphe Temporel Neo4j...</div>
              <div class="text-xs text-[var(--text-muted)] mt-1">Calcul des dépendances et propagation sur la Circulaire N° {{ circularId() }}</div>
            </div>
          </div>
        } @else if (report()) {
          <!-- Metric KPI Grid -->
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div class="glass-card p-5 rounded-2xl border border-[var(--border-card)] shadow-sm">
              <div class="text-[10px] text-[var(--text-muted)] uppercase font-bold tracking-wider">Total Éléments Impactés</div>
              <div class="text-3xl font-black text-[#E85D04] mt-1">{{ report().total_affected }}</div>
            </div>
            <div class="glass-card p-5 rounded-2xl border border-[var(--border-card)] shadow-sm">
              <div class="text-[10px] text-[var(--text-muted)] uppercase font-bold tracking-wider">Impact Critique</div>
              <div class="text-3xl font-black text-rose-600 dark:text-rose-400 mt-1">{{ report().critical_count }}</div>
            </div>
            <div class="glass-card p-5 rounded-2xl border border-[var(--border-card)] shadow-sm">
              <div class="text-[10px] text-[var(--text-muted)] uppercase font-bold tracking-wider">Impact Élevé</div>
              <div class="text-3xl font-black text-amber-600 dark:text-amber-400 mt-1">{{ report().high_count }}</div>
            </div>
            <div class="glass-card p-5 rounded-2xl border border-[var(--border-card)] shadow-sm">
              <div class="text-[10px] text-[var(--text-muted)] uppercase font-bold tracking-wider">Impact Modéré / Faible</div>
              <div class="text-3xl font-black text-indigo-600 dark:text-indigo-400 mt-1">{{ (report().medium_count || 0) + (report().low_count || 0) }}</div>
            </div>
          </div>

          <!-- Filters Toolbar -->
          <div class="glass-card p-4 shadow-sm flex flex-wrap items-center justify-between gap-4">
            <div class="flex items-center gap-2">
              <span class="text-xs font-bold text-[var(--text-muted)] uppercase mr-1">Sévérité :</span>
              <button (click)="severityFilter.set('ALL')" [class.bg-[#E85D04]]="severityFilter() === 'ALL'" [class.text-white]="severityFilter() === 'ALL'" class="px-3 py-1 rounded-lg text-xs font-semibold border border-[var(--border-card)] transition-all cursor-pointer">Tous</button>
              <button (click)="severityFilter.set('CRITICAL')" [class.bg-rose-600]="severityFilter() === 'CRITICAL'" [class.text-white]="severityFilter() === 'CRITICAL'" class="px-3 py-1 rounded-lg text-xs font-semibold border border-[var(--border-card)] transition-all cursor-pointer">Critique</button>
              <button (click)="severityFilter.set('HIGH')" [class.bg-amber-500]="severityFilter() === 'HIGH'" [class.text-white]="severityFilter() === 'HIGH'" class="px-3 py-1 rounded-lg text-xs font-semibold border border-[var(--border-card)] transition-all cursor-pointer">Élevé</button>
              <button (click)="severityFilter.set('MEDIUM')" [class.bg-indigo-600]="severityFilter() === 'MEDIUM'" [class.text-white]="severityFilter() === 'MEDIUM'" class="px-3 py-1 rounded-lg text-xs font-semibold border border-[var(--border-card)] transition-all cursor-pointer">Modéré</button>
            </div>

            <div class="text-xs text-[var(--text-muted)] font-medium">
              Affichage de <span class="font-bold text-[var(--text-primary)]">{{ filteredItems().length }}</span> élément(s)
            </div>
          </div>

          <!-- Impact Cartography List -->
          <div class="glass-card p-6 md:p-8 space-y-4 shadow-sm">
            <h2 class="text-sm font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-center justify-between">
              <span>Cartographie de Propagation Détailée</span>
              <span class="text-xs font-normal text-[var(--text-muted)] normal-case">Circulaire BCT N° {{ circularId() }}</span>
            </h2>

            @if (filteredItems().length === 0) {
              <div class="p-8 text-center text-[var(--text-muted)] text-sm">
                Aucun élément correspondant aux filtres sélectionnés.
              </div>
            } @else {
              <div class="space-y-3">
                @for (item of filteredItems(); track item.entity_id) {
                  <div class="p-5 rounded-2xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)] space-y-3 shadow-sm hover:border-[#E85D04]/40 transition-all">
                    <div class="flex flex-wrap justify-between items-start gap-2">
                      <div class="space-y-1 max-w-3xl">
                        <div class="flex items-center gap-2">
                          <span class="px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider bg-[#E85D04]/10 text-[#E85D04]">
                            {{ item.entity_type }}
                          </span>
                          <span class="font-bold text-[var(--text-primary)] text-sm">
                            {{ item.entity_name }}
                          </span>
                        </div>
                        <p class="text-xs text-[var(--text-secondary)] leading-relaxed">
                          {{ item.impact_description }}
                        </p>
                      </div>
                      <app-severity-badge [severity]="item.severity"></app-severity-badge>
                    </div>

                    @if (item.relationship_path && item.relationship_path.length > 0) {
                      <div class="flex items-center gap-2 pt-2 border-t border-[var(--border-card)]/50 text-[11px] text-[var(--text-muted)]">
                        <span class="font-semibold text-[#E85D04]">Chaîne causale :</span>
                        <span>(Circulaire: {{ circularId() }}) ➔ {{ item.relationship_path.join(' ➔ ') }} ➔ ({{ item.entity_type }})</span>
                      </div>
                    }
                  </div>
                }
              </div>
            }
          </div>
        } @else {
          <div class="glass-card p-12 text-center text-[var(--text-muted)] space-y-3 shadow-sm">
            <svg class="w-12 h-12 text-[var(--text-muted)] mx-auto opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
            </svg>
            <div class="text-base font-bold text-[var(--text-primary)]">Aucune analyse sélectionnée</div>
            <p class="text-xs max-w-md mx-auto">
              Sélectionnez une circulaire BCT ci-dessus ou effectuez une recherche pour cartographier les impacts réglementaires.
            </p>
          </div>
        }
      </div>
    </div>
  `
})
export class ImpactViewerComponent implements OnInit {
  route = inject(ActivatedRoute);
  api = inject(ApiService);

  searchQuery = '2024-88';
  circularId = signal('2024-88');
  report = signal<any>(null);
  loading = signal(false);
  severityFilter = signal<string>('ALL');

  presets = [
    { id: '2024-88', label: '2024-88 (Liquidité & Conformité)' },
    { id: '2016-01', label: '2016-01 (Octroi de Crédit Particuliers)' },
    { id: '2017-02', label: '2017-02 (Prêt PME & Garanties)' },
    { id: '2016-03', label: '2016-03 (Solvabilité & Dividendes)' },
    { id: '2018-09', label: '2018-09 (Gouvernance & Risques)' }
  ];

  filteredItems = computed(() => {
    const rep = this.report();
    if (!rep || !rep.affected_items) return [];
    const sev = this.severityFilter();
    if (sev === 'ALL') return rep.affected_items;
    return rep.affected_items.filter((item: any) => item.severity === sev);
  });

  ngOnInit() {
    const id = this.route.snapshot.paramMap.get('circularId') || '2024-88';
    this.circularId.set(id);
    this.searchQuery = id;
    this.loadImpact(id);
  }

  selectPreset(id: string) {
    this.circularId.set(id);
    this.searchQuery = id;
    this.loadImpact(id);
  }

  onSearch() {
    if (!this.searchQuery.trim()) return;
    const cleanId = this.searchQuery.trim();
    this.circularId.set(cleanId);
    this.loadImpact(cleanId);
  }

  loadImpact(id: string) {
    this.loading.set(true);
    this.api.getImpactReport(id).subscribe({
      next: (res) => {
        this.report.set(res);
        this.loading.set(false);
      },
      error: () => {
        this.report.set(null);
        this.loading.set(false);
      }
    });
  }
}
