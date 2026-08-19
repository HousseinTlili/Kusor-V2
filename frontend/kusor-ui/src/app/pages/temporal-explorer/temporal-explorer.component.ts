import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';

interface TemporalRecord {
  id: string;
  circular_number: string;
  reference: string;
  title: string;
  category: string;
  date_issued: string;
  status_at_date: string;
  status_badge: string;
  current_status: string;
  summary: string;
  relations: Array<{ type: string; target: string; desc: string }>;
}

interface TimelineEvent {
  date: string;
  year: string;
  circular: string;
  title: string;
  category: string;
  status: string;
}

@Component({
  selector: 'app-temporal-explorer',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="p-6 md:p-8 max-w-7xl mx-auto space-y-8 animate-fade-in">
      
      <!-- Executive Header Banner -->
      <div class="glass-card p-6 md:p-8 relative overflow-hidden border border-[var(--border-card)] shadow-lg rounded-2xl">
        <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
          <div class="space-y-2">
            <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-600 dark:text-blue-400 text-xs font-bold uppercase tracking-wider">
              <span>⏱️ Point-in-Time Regulatory Engine</span>
              <span class="w-1.5 h-1.5 rounded-full bg-blue-500 animate-ping"></span>
            </div>
            <h1 class="text-2xl md:text-3xl font-black tracking-tight text-[var(--text-primary)]">
              Explorateur Temporel & Audit Rétrospectif BCT
            </h1>
            <p class="text-sm text-[var(--text-secondary)] max-w-3xl leading-relaxed">
              Reconstitution dynamique de l'état exact des réglementations bancaires et circulaires BCT en vigueur à n'importe quelle date d'évaluation historique.
            </p>
          </div>

          <!-- Date Selector Control Box -->
          <div class="bg-[var(--bg-page-subtle)] p-4 rounded-xl border border-[var(--border-card)] flex flex-col sm:flex-row items-stretch sm:items-center gap-3 shadow-inner">
            <div class="flex flex-col">
              <label class="text-[10px] font-extrabold uppercase tracking-wider text-[var(--text-muted)] mb-1">
                Date d'Évaluation Juridique
              </label>
              <input 
                type="date" 
                [(ngModel)]="asOfDate" 
                (change)="loadTemporalGraph()"
                class="px-3.5 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-card)] text-blue-600 dark:text-blue-400 font-bold text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm transition-all"
              />
            </div>
            <button 
              (click)="loadTemporalGraph()" 
              class="self-end sm:self-auto px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 active:scale-95 text-white font-bold text-xs flex items-center justify-center gap-1.5 shadow-md shadow-blue-500/20 transition-all"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>Actualiser</span>
            </button>
          </div>
        </div>

        <!-- Quick Milestone Chips -->
        <div class="mt-6 pt-5 border-t border-[var(--border-card)] flex flex-wrap items-center gap-2 relative z-10">
          <span class="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mr-2">Jalons Réglementaires :</span>
          @for (preset of presets; track preset.label) {
            <button 
              (click)="selectPreset(preset.date)" 
              [class.bg-blue-600]="asOfDate === preset.date"
              [class.text-white]="asOfDate === preset.date"
              [class.border-blue-500]="asOfDate === preset.date"
              class="px-3 py-1.5 rounded-lg text-xs font-semibold border border-[var(--border-card)] bg-[var(--bg-card)] text-[var(--text-secondary)] hover:border-blue-500/50 hover:text-blue-500 transition-all flex items-center gap-1.5"
            >
              <span>{{ preset.icon }}</span>
              <span>{{ preset.label }}</span>
              <span class="text-[10px] opacity-75">({{ preset.date }})</span>
            </button>
          }
        </div>
      </div>

      <!-- KPI Summary Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- Card 1: Evaluation Date -->
        <div class="glass-card p-5 border border-[var(--border-card)] rounded-xl relative overflow-hidden">
          <div class="text-[11px] font-bold uppercase tracking-wider text-[var(--text-muted)] mb-1">Date Analysée</div>
          <div class="text-xl font-extrabold text-[var(--text-primary)]">{{ asOfDate }}</div>
          <div class="text-xs text-blue-500 font-medium mt-1">Reconstitution temporelle active</div>
        </div>

        <!-- Card 2: En Vigueur -->
        <div class="glass-card p-5 border border-emerald-500/30 rounded-xl bg-emerald-500/5 relative overflow-hidden">
          <div class="text-[11px] font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 mb-1">Circulaires En Vigueur</div>
          <div class="text-2xl font-black text-emerald-600 dark:text-emerald-400">{{ activeCount() }}</div>
          <div class="text-xs text-[var(--text-muted)] font-medium mt-1">Directement applicables au {{ asOfDate }}</div>
        </div>

        <!-- Card 3: Non Publiées (Futures) -->
        <div class="glass-card p-5 border border-amber-500/30 rounded-xl bg-amber-500/5 relative overflow-hidden">
          <div class="text-[11px] font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400 mb-1">Textes Non Encore Parus</div>
          <div class="text-2xl font-black text-amber-600 dark:text-amber-400">{{ futureCount() }}</div>
          <div class="text-xs text-[var(--text-muted)] font-medium mt-1">Inapplicables à cette date historique</div>
        </div>

        <!-- Card 4: Total Knowledge Base -->
        <div class="glass-card p-5 border border-[var(--border-card)] rounded-xl relative overflow-hidden">
          <div class="text-[11px] font-bold uppercase tracking-wider text-[var(--text-muted)] mb-1">Corpus Réglementaire</div>
          <div class="text-2xl font-black text-[var(--text-primary)]">{{ records().length }}</div>
          <div class="text-xs text-[var(--text-muted)] font-medium mt-1">Textes indexés dans le graphe</div>
        </div>
      </div>

      <!-- Historical Timeline Visualizer -->
      <div class="glass-card p-6 md:p-8 border border-[var(--border-card)] rounded-2xl shadow-sm space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="text-sm font-bold uppercase tracking-wider text-[var(--text-primary)] flex items-center gap-2">
            <span>📅</span>
            <span>Frise Chronologique des Réformes Majeures BCT</span>
          </h2>
          <span class="text-xs text-[var(--text-muted)]">Cliquez sur une étape pour vous y téléporter</span>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-5 gap-3 pt-2">
          @for (event of timelineEvents(); track event.circular) {
            <div 
              (click)="selectPreset(event.date)"
              [class.border-blue-500]="asOfDate >= event.date"
              [class.bg-blue-500/5]="asOfDate >= event.date"
              class="p-4 rounded-xl border border-[var(--border-card)] cursor-pointer hover:border-blue-400 transition-all space-y-2 group"
            >
              <div class="flex items-center justify-between">
                <span class="text-xs font-black text-blue-600 dark:text-blue-400 group-hover:underline">
                  {{ event.year }}
                </span>
                <span 
                  [class.bg-emerald-500/10]="asOfDate >= event.date"
                  [class.text-emerald-500]="asOfDate >= event.date"
                  [class.bg-slate-500/10]="asOfDate < event.date"
                  [class.text-slate-500]="asOfDate < event.date"
                  class="px-2 py-0.5 rounded text-[10px] font-bold"
                >
                  {{ asOfDate >= event.date ? 'En vigueur' : 'Futur' }}
                </span>
              </div>
              <div class="font-bold text-xs text-[var(--text-primary)] line-clamp-1">{{ event.circular }}</div>
              <p class="text-[11px] text-[var(--text-secondary)] line-clamp-2 leading-relaxed">{{ event.title }}</p>
            </div>
          }
        </div>
      </div>

      <!-- Point-in-Time Circulars Matrix -->
      <div class="glass-card p-6 md:p-8 border border-[var(--border-card)] rounded-2xl shadow-sm space-y-6">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border-card)] pb-4">
          <div>
            <h2 class="text-base font-extrabold text-[var(--text-primary)]">
              Matrice Réglementaire Applicative au {{ asOfDate }}
            </h2>
            <p class="text-xs text-[var(--text-muted)] mt-0.5">
              Statut juridique certifié pour chaque texte officiel
            </p>
          </div>

          <!-- Category & Status Filter Pills -->
          <div class="flex flex-wrap items-center gap-2">
            <button 
              (click)="selectedFilter = 'ALL'"
              [class.bg-blue-600]="selectedFilter === 'ALL'"
              [class.text-white]="selectedFilter === 'ALL'"
              class="px-3 py-1 rounded-lg text-xs font-bold border border-[var(--border-card)] text-[var(--text-secondary)] transition-all"
            >
              Toutes ({{ records().length }})
            </button>
            <button 
              (click)="selectedFilter = 'EN_VIGUEUR'"
              [class.bg-emerald-600]="selectedFilter === 'EN_VIGUEUR'"
              [class.text-white]="selectedFilter === 'EN_VIGUEUR'"
              class="px-3 py-1 rounded-lg text-xs font-bold border border-[var(--border-card)] text-emerald-600 dark:text-emerald-400 transition-all"
            >
              En Vigueur ({{ activeCount() }})
            </button>
            <button 
              (click)="selectedFilter = 'NON_PUBLIEE'"
              [class.bg-amber-600]="selectedFilter === 'NON_PUBLIEE'"
              [class.text-white]="selectedFilter === 'NON_PUBLIEE'"
              class="px-3 py-1 rounded-lg text-xs font-bold border border-[var(--border-card)] text-amber-600 dark:text-amber-400 transition-all"
            >
              Non Publiées ({{ futureCount() }})
            </button>
          </div>
        </div>

        <!-- Loading State -->
        @if (loading()) {
          <div class="flex justify-center items-center h-48 text-[var(--text-muted)] font-medium gap-3">
            <svg class="animate-spin h-6 w-6 text-blue-500" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span class="text-sm">Reconstitution du graphe réglementaire à la date du {{ asOfDate }}...</span>
          </div>
        } @else {
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            @for (rec of filteredRecords(); track rec.id) {
              <div 
                [class.border-emerald-500/40]="rec.status_at_date === 'EN_VIGUEUR'"
                [class.border-amber-500/30]="rec.status_at_date === 'NON_PUBLIEE'"
                class="p-5 rounded-2xl bg-[var(--bg-card)] border text-xs space-y-3 shadow-sm hover:shadow-md transition-all relative overflow-hidden"
              >
                <!-- Card Top Header -->
                <div class="flex items-start justify-between gap-3">
                  <div>
                    <span class="px-2 py-0.5 rounded text-[10px] font-extrabold uppercase bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
                      {{ rec.category }}
                    </span>
                    <h3 class="font-extrabold text-[var(--text-primary)] text-sm mt-1.5">{{ rec.title }}</h3>
                  </div>

                  <!-- Status Badge -->
                  @if (rec.status_at_date === 'EN_VIGUEUR') {
                    <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-extrabold border border-emerald-500/30 text-[10px] whitespace-nowrap">
                      <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                      <span>En Vigueur</span>
                    </span>
                  } @else {
                    <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-amber-500/10 text-amber-600 dark:text-amber-400 font-extrabold border border-amber-500/30 text-[10px] whitespace-nowrap">
                      <span>⏳</span>
                      <span>Non Publiée (Post {{ asOfDate }})</span>
                    </span>
                  }
                </div>

                <!-- Date Info & Summary -->
                <div class="text-[var(--text-secondary)] leading-relaxed text-xs">
                  {{ rec.summary }}
                </div>

                <div class="flex items-center justify-between text-[11px] text-[var(--text-muted)] pt-2 border-t border-[var(--border-card)]">
                  <div>Date de publication officielle : <span class="font-bold text-[var(--text-primary)]">{{ rec.date_issued }}</span></div>
                </div>

                <!-- Inter-Circular Relations in Graph -->
                @if (rec.relations && rec.relations.length > 0) {
                  <div class="pt-2 flex flex-wrap gap-1.5 items-center">
                    <span class="text-[10px] font-bold text-[var(--text-muted)] uppercase">Liaisons Neo4j :</span>
                    @for (rel of rec.relations; track rel.target) {
                      <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-[var(--bg-page-subtle)] border border-[var(--border-card)] text-[10px] font-medium text-[var(--text-secondary)]">
                        <span class="font-bold text-blue-500">{{ rel.type }}</span>
                        <span>{{ rel.target }}</span>
                      </span>
                    }
                  </div>
                }
              </div>
            }
          </div>
        }
      </div>

    </div>
  `
})
export class TemporalExplorerComponent implements OnInit {
  api = inject(ApiService);
  asOfDate = '2024-02-10';
  selectedFilter: 'ALL' | 'EN_VIGUEUR' | 'NON_PUBLIEE' = 'ALL';

  records = signal<TemporalRecord[]>([]);
  timelineEvents = signal<TimelineEvent[]>([]);
  loading = signal(false);

  presets = [
    { label: 'Aujourd\'hui (2026)', date: '2026-08-19', icon: '🟢' },
    { label: 'Régime NPL (2024)', date: '2024-11-20', icon: '📑' },
    { label: 'Gouvernance & AML (2018)', date: '2018-10-01', icon: '🛡️' },
    { label: 'Réserves Obligatoires (2017)', date: '2017-04-01', icon: '💰' },
    { label: 'Plafond DSTI 40% (2016)', date: '2016-02-01', icon: '💳' },
  ];

  activeCount = computed(() => this.records().filter(r => r.status_at_date === 'EN_VIGUEUR').length);
  futureCount = computed(() => this.records().filter(r => r.status_at_date === 'NON_PUBLIEE').length);

  filteredRecords = computed(() => {
    const list = this.records();
    if (this.selectedFilter === 'EN_VIGUEUR') {
      return list.filter(r => r.status_at_date === 'EN_VIGUEUR');
    }
    if (this.selectedFilter === 'NON_PUBLIEE') {
      return list.filter(r => r.status_at_date === 'NON_PUBLIEE');
    }
    return list;
  });

  ngOnInit() {
    this.loadTemporalGraph();
  }

  selectPreset(date: string) {
    this.asOfDate = date;
    this.loadTemporalGraph();
  }

  loadTemporalGraph() {
    this.loading.set(true);
    this.api.getTemporalGraph(this.asOfDate).subscribe({
      next: (res) => {
        this.records.set(res.records || []);
        this.timelineEvents.set(res.timeline_events || []);
        this.loading.set(false);
      },
      error: () => this.loading.set(false)
    });
  }
}
