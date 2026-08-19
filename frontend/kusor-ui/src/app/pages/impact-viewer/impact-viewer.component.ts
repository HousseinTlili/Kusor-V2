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
    <div class="impact-page-container">
      
      <!-- 1. Executive Attijari Header Banner -->
      <div class="glass-card header-banner">
        <div class="banner-left">
          <div class="badge-row">
            <span class="bank-badge">Attijari Bank • Direction de la Stratégie & Veille</span>
            <span class="norm-badge">Propagation & Effet Domino BCT</span>
          </div>
          <h1 class="page-title">Cartographie d'Impact & Dépendances Réglementaires</h1>
          <p class="page-subtitle">
            Surveillance et analyse de propagation automatique des circulaires BCT sur les processus métiers, la gouvernance des risques et les modèles contractuels d'Attijari Bank.
          </p>
        </div>
        <div class="banner-right">
          <div class="stat-card">
            <span class="stat-label">Moteur de Graphe</span>
            <span class="stat-value">Neo4j</span>
            <span class="stat-desc">Analyse causale & temporelle</span>
          </div>
        </div>
      </div>

      <!-- 2. Circular Selector & Search Toolbar -->
      <div class="glass-card toolbar-card">
        <div class="search-row">
          <div class="search-input-wrapper">
            <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
            </svg>
            <input 
              type="text" 
              [(ngModel)]="searchQuery" 
              (keyup.enter)="onSearch()"
              placeholder="Entrez une référence de circulaire BCT (ex: 2024-88, 2016-01, 2017-02)..."
              class="search-input"
            />
          </div>

          <button 
            (click)="onSearch()"
            [disabled]="loading() || !searchQuery.trim()"
            class="btn-search-impact"
          >
            @if (loading()) {
              <svg class="spinner-icon animate-spin" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>Calcul de propagation...</span>
            } @else {
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="action-icon">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
              </svg>
              <span>Analyser l'Impact</span>
            }
          </button>
        </div>

        <!-- Quick Presets -->
        <div class="presets-row">
          <span class="presets-label">Circulaires BCT Clés :</span>
          @for (preset of presets; track preset.id) {
            <button 
              (click)="selectPreset(preset.id)"
              [class.active]="circularId() === preset.id"
              class="preset-chip"
            >
              {{ preset.label }}
            </button>
          }
        </div>
      </div>

      <!-- 3. Results Container -->
      <div class="results-container">
        @if (loading()) {
          <div class="glass-card loading-card">
            <svg class="loading-spinner animate-spin" viewBox="0 0 24 24" fill="none">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <div class="loading-text">
              <div class="loading-title">Parcours du Graphe Temporel Neo4j en cours...</div>
              <div class="loading-desc">Calcul de la chaîne d'impact et propagation sur la Circulaire N° {{ circularId() }}</div>
            </div>
          </div>
        } @else if (report()) {
          <!-- KPI Metrics Grid -->
          <div class="kpi-grid">
            <div class="glass-card kpi-box">
              <span class="kpi-title">Total Éléments Impactés</span>
              <span class="kpi-value text-blue">{{ report().total_affected }}</span>
            </div>
            <div class="glass-card kpi-box">
              <span class="kpi-title">Criticité Majeure / Bloquante</span>
              <span class="kpi-value text-danger">{{ report().critical_count }}</span>
            </div>
            <div class="glass-card kpi-box">
              <span class="kpi-title">Vigilance Réglementaire</span>
              <span class="kpi-value text-amber">{{ report().high_count }}</span>
            </div>
            <div class="glass-card kpi-box">
              <span class="kpi-title">Impacts Modérés / Métiers</span>
              <span class="kpi-value text-indigo">{{ (report().medium_count || 0) + (report().low_count || 0) }}</span>
            </div>
          </div>

          <!-- Filters Toolbar -->
          <div class="glass-card filter-toolbar">
            <div class="filter-group">
              <span class="filter-label">Niveau de Sévérité :</span>
              <button (click)="severityFilter.set('ALL')" [class.active]="severityFilter() === 'ALL'" class="filter-btn">Tous</button>
              <button (click)="severityFilter.set('CRITICAL')" [class.active]="severityFilter() === 'CRITICAL'" class="filter-btn btn-crit">Critique</button>
              <button (click)="severityFilter.set('HIGH')" [class.active]="severityFilter() === 'HIGH'" class="filter-btn btn-high">Élevé</button>
              <button (click)="severityFilter.set('MEDIUM')" [class.active]="severityFilter() === 'MEDIUM'" class="filter-btn btn-med">Modéré</button>
            </div>

            <div class="filter-count">
              Affichage de <strong>{{ filteredItems().length }}</strong> élément(s)
            </div>
          </div>

          <!-- Impact Items List -->
          <div class="glass-card impact-items-card">
            <div class="card-header-row">
              <h2 class="card-title">Chaîne de Propagation Détailée</h2>
              <span class="card-subtitle">Circulaire BCT N° {{ circularId() }}</span>
            </div>

            @if (filteredItems().length === 0) {
              <div class="empty-filter-state">
                Aucun élément correspondant aux filtres sélectionnés.
              </div>
            } @else {
              <div class="impact-list">
                @for (item of filteredItems(); track item.entity_id) {
                  <div class="impact-item-row">
                    <div class="item-main">
                      <div class="item-badge-row">
                        <span class="entity-type-badge">{{ item.entity_type }}</span>
                        <span class="entity-name">{{ item.entity_name }}</span>
                      </div>
                      <p class="item-description">{{ item.impact_description }}</p>
                    </div>
                    <app-severity-badge [severity]="item.severity"></app-severity-badge>

                    @if (item.relationship_path && item.relationship_path.length > 0) {
                      <div class="chain-box">
                        <span class="chain-title">Chaîne de transmission :</span>
                        <span class="chain-nodes">Circulaire {{ circularId() }} ➔ {{ item.relationship_path.join(' ➔ ') }} ➔ {{ item.entity_type }}</span>
                      </div>
                    }
                  </div>
                }
              </div>
            }
          </div>
        } @else {
          <div class="glass-card empty-card">
            <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
            </svg>
            <h3 class="empty-title">Aucune analyse sélectionnée</h3>
            <p class="empty-desc">Sélectionnez une circulaire ci-dessus pour cartographier les répercussions réglementaires et contractuelles.</p>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    .impact-page-container {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
      max-width: 1300px;
      margin: 0 auto;
      animation: fadeIn 0.3s ease-out;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }

    /* 1. Header Banner */
    .header-banner {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1.75rem 2rem;
      border-radius: 16px;
      background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.7) 100%);
      border: 1px solid rgba(59, 130, 246, 0.2);
      gap: 1.5rem;

      @media (max-width: 900px) {
        flex-direction: column;
        align-items: flex-start;
      }
    }

    .badge-row {
      display: flex;
      gap: 0.6rem;
      margin-bottom: 0.4rem;
      flex-wrap: wrap;
    }

    .bank-badge {
      background: rgba(37, 99, 235, 0.15);
      border: 1px solid rgba(59, 130, 246, 0.3);
      color: #60a5fa;
      font-size: 0.72rem;
      font-weight: 700;
      padding: 0.2rem 0.65rem;
      border-radius: 20px;
    }

    .norm-badge {
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid rgba(16, 185, 129, 0.3);
      color: #34d399;
      font-size: 0.72rem;
      font-weight: 700;
      padding: 0.2rem 0.65rem;
      border-radius: 20px;
    }

    .page-title {
      font-size: 1.6rem;
      font-weight: 800;
      color: var(--text-primary);
      margin-bottom: 0.35rem;
      letter-spacing: -0.01em;
    }

    .page-subtitle {
      font-size: 0.85rem;
      color: var(--text-secondary);
      max-width: 720px;
      line-height: 1.45;
    }

    .stat-card {
      background: rgba(0, 0, 0, 0.3);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 12px;
      padding: 0.85rem 1.25rem;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      flex-shrink: 0;

      .stat-label { font-size: 0.68rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; }
      .stat-value { font-size: 1.6rem; font-weight: 900; color: #38bdf8; }
      .stat-desc { font-size: 0.65rem; color: var(--text-muted); }
    }

    /* 2. Toolbar & Presets */
    .toolbar-card {
      padding: 1.5rem;
      border-radius: 16px;
      display: flex;
      flex-direction: column;
      gap: 1.15rem;
    }

    .search-row {
      display: flex;
      gap: 0.75rem;

      @media (max-width: 768px) {
        flex-direction: column;
      }
    }

    .search-input-wrapper {
      flex: 1;
      position: relative;
      display: flex;
      align-items: center;

      .search-icon {
        position: absolute;
        left: 0.85rem;
        width: 1.15rem;
        height: 1.15rem;
        color: var(--text-muted);
      }

      .search-input {
        width: 100%;
        padding: 0.75rem 1rem 0.75rem 2.5rem;
        background: var(--bg-input);
        border: 1px solid var(--border-input);
        color: var(--text-primary);
        border-radius: 10px;
        font-size: 0.85rem;
        outline: none;
        transition: all 0.15s ease;

        &:focus {
          border-color: #3b82f6;
          box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
        }
      }
    }

    .btn-search-impact {
      background: linear-gradient(135deg, #1e40af 0%, #1e3a8a 100%);
      border: 1px solid rgba(59, 130, 246, 0.4);
      color: white;
      padding: 0 1.5rem;
      border-radius: 10px;
      font-size: 0.85rem;
      font-weight: 800;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      box-shadow: 0 4px 12px rgba(30, 58, 138, 0.3);
      transition: all 0.2s ease;
      min-height: 42px;

      &:hover:not(:disabled) {
        background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
        border-color: #60a5fa;
        transform: translateY(-1px);
      }

      &:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

      .action-icon {
        width: 1.1rem;
        height: 1.1rem;
      }
    }

    .presets-row {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      flex-wrap: wrap;

      .presets-label {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        color: var(--text-muted);
        margin-right: 0.25rem;
      }
    }

    .preset-chip {
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border-color);
      color: var(--text-secondary);
      padding: 0.35rem 0.75rem;
      border-radius: 8px;
      font-size: 0.76rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;

      &:hover {
        background: rgba(255, 255, 255, 0.08);
        color: var(--text-primary);
        border-color: rgba(59, 130, 246, 0.3);
      }

      &.active {
        background: rgba(37, 99, 235, 0.2);
        border-color: #3b82f6;
        color: #93c5fd;
        font-weight: 700;
      }
    }

    /* 3. Results Container */
    .results-container {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .loading-card {
      padding: 4rem 2rem;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 1rem;
      border-radius: 16px;

      .loading-spinner {
        width: 2.5rem;
        height: 2.5rem;
        color: #3b82f6;
      }

      .loading-text {
        text-align: center;

        .loading-title {
          font-size: 1rem;
          font-weight: 800;
          color: var(--text-primary);
        }

        .loading-desc {
          font-size: 0.78rem;
          color: var(--text-muted);
          margin-top: 0.25rem;
        }
      }
    }

    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 1rem;

      @media (max-width: 800px) {
        grid-template-columns: repeat(2, 1fr);
      }
    }

    .kpi-box {
      padding: 1.25rem;
      border-radius: 14px;
      text-align: center;
      display: flex;
      flex-direction: column;
      gap: 0.35rem;

      .kpi-title {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        color: var(--text-muted);
      }

      .kpi-value {
        font-size: 1.8rem;
        font-weight: 900;

        &.text-blue { color: #38bdf8; }
        &.text-danger { color: #ef4444; }
        &.text-amber { color: #f59e0b; }
        &.text-indigo { color: #818cf8; }
      }
    }

    .filter-toolbar {
      padding: 0.85rem 1.25rem;
      border-radius: 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.75rem;

      .filter-group {
        display: flex;
        align-items: center;
        gap: 0.45rem;
      }

      .filter-label {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        color: var(--text-muted);
        margin-right: 0.25rem;
      }

      .filter-btn {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid var(--border-color);
        color: var(--text-secondary);
        padding: 0.25rem 0.65rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.15s ease;

        &.active {
          background: #1e40af;
          border-color: #3b82f6;
          color: white;
        }

        &.btn-crit.active { background: #dc2626; border-color: #ef4444; }
        &.btn-high.active { background: #d97706; border-color: #f59e0b; }
        &.btn-med.active { background: #4f46e5; border-color: #6366f1; }
      }

      .filter-count {
        font-size: 0.78rem;
        color: var(--text-muted);

        strong { color: var(--text-primary); }
      }
    }

    .impact-items-card {
      padding: 1.75rem;
      border-radius: 16px;
      display: flex;
      flex-direction: column;
      gap: 1.25rem;

      .card-header-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 0.85rem;
        border-bottom: 1px solid var(--border-color);

        .card-title {
          font-size: 1.05rem;
          font-weight: 800;
          color: var(--text-primary);
        }

        .card-subtitle {
          font-size: 0.78rem;
          color: var(--text-muted);
        }
      }
    }

    .impact-list {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .impact-item-row {
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      transition: all 0.15s ease;

      &:hover {
        border-color: rgba(59, 130, 246, 0.35);
        background: rgba(255, 255, 255, 0.04);
      }

      .item-badge-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.35rem;

        .entity-type-badge {
          background: rgba(56, 189, 248, 0.12);
          border: 1px solid rgba(56, 189, 248, 0.25);
          color: #38bdf8;
          font-size: 0.68rem;
          font-weight: 800;
          text-transform: uppercase;
          padding: 0.15rem 0.5rem;
          border-radius: 4px;
        }

        .entity-name {
          font-size: 0.92rem;
          font-weight: 800;
          color: var(--text-primary);
        }
      }

      .item-description {
        font-size: 0.82rem;
        color: var(--text-secondary);
        line-height: 1.5;
      }

      .chain-box {
        padding-top: 0.65rem;
        border-top: 1px solid rgba(255, 255, 255, 0.04);
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.74rem;
        color: var(--text-muted);

        .chain-title {
          font-weight: 700;
          color: #60a5fa;
        }
      }
    }

    .empty-card {
      padding: 4rem 2rem;
      border-radius: 16px;
      text-align: center;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.5rem;

      .empty-icon {
        width: 3rem;
        height: 3rem;
        color: var(--text-muted);
        opacity: 0.4;
        margin-bottom: 0.5rem;
      }

      .empty-title {
        font-size: 1.1rem;
        font-weight: 800;
        color: var(--text-primary);
      }

      .empty-desc {
        font-size: 0.82rem;
        color: var(--text-muted);
        max-width: 420px;
      }
    }

    .empty-filter-state {
      text-align: center;
      padding: 2.5rem 1rem;
      font-size: 0.82rem;
      color: var(--text-muted);
    }
  `]
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
      next: (res: any) => {
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

