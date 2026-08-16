import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <div class="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      
      <!-- Top Welcome Banner -->
      <div class="glass-card p-6 md:p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 relative overflow-hidden">
        <div class="space-y-1.5 z-10">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#E85D04]/10 text-[#E85D04] text-xs font-bold uppercase tracking-wider">
            <span class="w-2 h-2 rounded-full bg-[#E85D04] animate-pulse"></span>
            Supervision Réglementaire BCT
          </div>
          <h1 class="text-2xl md:text-3xl font-black tracking-tight text-[var(--text-primary)]">
            Tableau de Bord de Conformité
          </h1>
          <p class="text-[var(--text-muted)] text-sm max-w-2xl">
            Surveillance continue des obligations BCT, cartographie d'impacts et filtrage des opérations pour Attijari Bank.
          </p>
        </div>

        <div class="flex items-center gap-3 z-10">
          <button (click)="loadStats()" [disabled]="loading()"
            class="px-4 py-2.5 rounded-xl bg-[var(--bg-page-subtle)] hover:bg-[#E85D04]/10 text-[var(--text-secondary)] hover:text-[#E85D04] border border-[var(--border-card)] text-xs font-bold transition-all shadow-sm flex items-center gap-2">
            @if (loading()) {
              <svg class="animate-spin h-4 w-4 text-[#E85D04]" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>Actualisation...</span>
            } @else {
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
              </svg>
              <span>Actualiser les Données</span>
            }
          </button>

          <a routerLink="/chat" class="px-5 py-2.5 rounded-xl font-bold brand-btn-primary text-xs flex items-center gap-2 shadow-sm">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
            </svg>
            <span>Poser une Question</span>
          </a>
        </div>
      </div>

      <!-- Stats Metric Grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        
        <!-- Circulaires Card -->
        <div class="glass-card-interactive p-6 space-y-3">
          <div class="flex items-center justify-between">
            <div class="text-[11px] uppercase font-bold text-[var(--text-muted)] tracking-wider">Circulaires & Textes BCT</div>
            <div class="p-2.5 rounded-xl bg-orange-50 dark:bg-orange-950/30 text-[#E85D04] border border-orange-100 dark:border-orange-900/40">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
              </svg>
            </div>
          </div>
          <div class="text-3xl font-black text-[var(--text-primary)]">{{ stats()?.documents_total || 0 }}</div>
          <div class="text-xs text-[var(--text-muted)] font-medium">Textes indexés & vectorisés</div>
        </div>

        <!-- Vecteurs Embeddings -->
        <div class="glass-card-interactive p-6 space-y-3">
          <div class="flex items-center justify-between">
            <div class="text-[11px] uppercase font-bold text-[var(--text-muted)] tracking-wider">Vecteurs Embeddings</div>
            <div class="p-2.5 rounded-xl bg-amber-50 dark:bg-amber-950/30 text-amber-600 dark:text-amber-400 border border-amber-100 dark:border-amber-900/40">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/>
              </svg>
            </div>
          </div>
          <div class="text-3xl font-black text-amber-600 dark:text-amber-400">{{ stats()?.chromadb_vectors || 0 }}</div>
          <div class="text-xs text-[var(--text-muted)] font-medium">Embeddings nomic-embed-text</div>
        </div>

        <!-- Nœuds Graph Neo4j -->
        <div class="glass-card-interactive p-6 space-y-3">
          <div class="flex items-center justify-between">
            <div class="text-[11px] uppercase font-bold text-[var(--text-muted)] tracking-wider">Nœuds & Obligations</div>
            <div class="p-2.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 text-emerald-600 dark:text-emerald-400 border border-emerald-100 dark:border-emerald-900/40">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
              </svg>
            </div>
          </div>
          <div class="text-3xl font-black text-emerald-600 dark:text-emerald-400">{{ stats()?.neo4j_nodes || 0 }}</div>
          <div class="text-xs text-[var(--text-muted)] font-medium">{{ stats()?.neo4j_relationships || 0 }} relations temporelles</div>
        </div>

        <!-- Logs d'Audit -->
        <div class="glass-card-interactive p-6 space-y-3">
          <div class="flex items-center justify-between">
            <div class="text-[11px] uppercase font-bold text-[var(--text-muted)] tracking-wider">Audit & Traçabilité</div>
            <div class="p-2.5 rounded-xl bg-blue-50 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400 border border-blue-100 dark:border-blue-900/40">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
              </svg>
            </div>
          </div>
          <div class="text-3xl font-black text-blue-600 dark:text-blue-400">{{ stats()?.audit_logs_total || 0 }}</div>
          <div class="text-xs text-[var(--text-muted)] font-medium">Scellés cryptographiques SHA-256</div>
        </div>
      </div>

      <!-- Quick Action Modules Grid -->
      <div class="space-y-4">
        <h2 class="text-lg font-bold text-[var(--text-primary)]">Modules d'Évaluation Métier</h2>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
          
          <!-- KYC Card -->
          <a routerLink="/kyc" class="glass-card-interactive p-6 space-y-3 group block">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-[#E85D04] uppercase tracking-wider">Conformité Client</span>
              <span class="p-2 rounded-xl bg-[var(--bg-page-subtle)] text-[var(--text-muted)] group-hover:text-[#E85D04] transition-colors">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                </svg>
              </span>
            </div>
            <h3 class="text-base font-bold text-[var(--text-primary)] group-hover:text-[#E85D04] transition-colors">Vérification KYC & Sanctions</h3>
            <p class="text-xs text-[var(--text-muted)] leading-relaxed">
              Filtrage des personnes physiques et morales contre les listes de sanctions internationales (ONU, UE, OFAC) et normes GAFI.
            </p>
          </a>

          <!-- Credit Card -->
          <a routerLink="/credit" class="glass-card-interactive p-6 space-y-3 group block">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-emerald-600 uppercase tracking-wider">Engagement & Risque</span>
              <span class="p-2 rounded-xl bg-[var(--bg-page-subtle)] text-[var(--text-muted)] group-hover:text-emerald-600 transition-colors">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                </svg>
              </span>
            </div>
            <h3 class="text-base font-bold text-[var(--text-primary)] group-hover:text-emerald-600 transition-colors">Pré-filtrage Crédit & Ratios</h3>
            <p class="text-xs text-[var(--text-muted)] leading-relaxed">
              Contrôle automatique du ratio d'endettement maximal (40% BCT), garanties requises et solvabilité de l'emprunteur.
            </p>
          </a>

          <!-- Contract Card -->
          <a routerLink="/contract" class="glass-card-interactive p-6 space-y-3 group block">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-indigo-600 uppercase tracking-wider">Affaires Juridiques</span>
              <span class="p-2 rounded-xl bg-[var(--bg-page-subtle)] text-[var(--text-muted)] group-hover:text-indigo-600 transition-colors">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                </svg>
              </span>
            </div>
            <h3 class="text-base font-bold text-[var(--text-primary)] group-hover:text-indigo-600 transition-colors">Audit Contrats & Clauses</h3>
            <p class="text-xs text-[var(--text-muted)] leading-relaxed">
              Détection des clauses abusives, obsolètes ou non conformes aux dernières circulaires de la Banque Centrale de Tunisie.
            </p>
          </a>

        </div>
      </div>

    </div>
  `
})
export class DashboardComponent implements OnInit {
  api = inject(ApiService);
  auth = inject(AuthService);
  stats = signal<any>(null);
  loading = signal(false);

  ngOnInit() {
    this.loadStats();
  }

  loadStats() {
    this.loading.set(true);
    this.api.getStats().subscribe({
      next: (res: any) => {
        this.stats.set(res);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
      }
    });
  }
}
