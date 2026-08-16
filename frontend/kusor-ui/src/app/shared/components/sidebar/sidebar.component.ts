import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { ThemeService } from '../../../core/services/theme.service';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive],
  template: `
    <aside class="fixed top-0 left-0 bottom-0 w-64 bg-[var(--bg-sidebar)] border-r border-[var(--border-sidebar)] flex flex-col z-50 shadow-sm transition-colors duration-200">
      
      <!-- Attijari Bank Brand Header -->
      <div class="p-5 border-b border-[var(--border-sidebar)] flex items-center justify-between">
        <div class="flex items-center gap-3">
          <img src="assets/attijari_logo.png" alt="Attijari Bank Logo" class="h-9 w-9 object-contain rounded-lg shadow-sm border border-[var(--border-card)]" />
          <div>
            <div class="text-lg font-black tracking-tight brand-gradient-text leading-none">KUSOR v3</div>
            <div class="text-[10px] font-bold tracking-wider text-[#E85D04] uppercase mt-1">Attijari Bank</div>
          </div>
        </div>

        <!-- Theme Toggle Button -->
        <button (click)="theme.toggleTheme()" [title]="theme.isDark() ? 'Activer le mode clair' : 'Activer le mode sombre'"
          class="p-2 rounded-xl text-[var(--text-muted)] hover:text-[#E85D04] hover:bg-[var(--accent-orange-light)] border border-[var(--border-card)] transition-all">
          @if (theme.isDark()) {
            <!-- Sun Icon for Light Mode -->
            <svg class="w-4 h-4 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          } @else {
            <!-- Moon Icon for Dark Mode -->
            <svg class="w-4 h-4 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          }
        </button>
      </div>

      <!-- Navigation Section -->
      <div class="flex-1 overflow-y-auto px-3.5 py-5 space-y-5">
        
        <!-- Main Navigation -->
        <div>
          <div class="px-3 mb-2 text-[10px] font-extrabold tracking-widest text-[var(--text-faint)] uppercase">Vue d'Ensemble</div>
          <div class="space-y-1">
            <a routerLink="/dashboard" routerLinkActive="bg-[#E85D04]/10 border-l-4 border-[#E85D04] text-[#E85D04] font-bold"
              class="flex items-center gap-3 px-3 py-2 rounded-xl text-xs text-[var(--text-secondary)] hover:text-[#E85D04] hover:bg-[var(--bg-page-subtle)] transition-all group">
              <svg class="w-4 h-4 text-[var(--text-muted)] group-hover:text-[#E85D04]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
              </svg>
              <span>Tableau de Bord</span>
            </a>

            <a routerLink="/chat" routerLinkActive="bg-[#E85D04]/10 border-l-4 border-[#E85D04] text-[#E85D04] font-bold"
              class="flex items-center gap-3 px-3 py-2 rounded-xl text-xs text-[var(--text-secondary)] hover:text-[#E85D04] hover:bg-[var(--bg-page-subtle)] transition-all group">
              <svg class="w-4 h-4 text-[var(--text-muted)] group-hover:text-[#E85D04]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
              </svg>
              <span>Assistant RAG BCT</span>
            </a>

            <a routerLink="/graph" routerLinkActive="bg-[#E85D04]/10 border-l-4 border-[#E85D04] text-[#E85D04] font-bold"
              class="flex items-center gap-3 px-3 py-2 rounded-xl text-xs text-[var(--text-secondary)] hover:text-[#E85D04] hover:bg-[var(--bg-page-subtle)] transition-all group">
              <svg class="w-4 h-4 text-[var(--text-muted)] group-hover:text-[#E85D04]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
              </svg>
              <span>Graphe Neo4j</span>
            </a>

            <a routerLink="/temporal-explorer" routerLinkActive="bg-[#E85D04]/10 border-l-4 border-[#E85D04] text-[#E85D04] font-bold"
              class="flex items-center gap-3 px-3 py-2 rounded-xl text-xs text-[var(--text-secondary)] hover:text-[#E85D04] hover:bg-[var(--bg-page-subtle)] transition-all group">
              <svg class="w-4 h-4 text-[var(--text-muted)] group-hover:text-[#E85D04]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              <span>Explorateur Temporel</span>
            </a>

            <a routerLink="/impact-viewer" routerLinkActive="bg-[#E85D04]/10 border-l-4 border-[#E85D04] text-[#E85D04] font-bold"
              class="flex items-center gap-3 px-3 py-2 rounded-xl text-xs text-[var(--text-secondary)] hover:text-[#E85D04] hover:bg-[var(--bg-page-subtle)] transition-all group">
              <svg class="w-4 h-4 text-[var(--text-muted)] group-hover:text-[#E85D04]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
              </svg>
              <span>Impact Réglementaire</span>
            </a>
          </div>
        </div>

        <!-- Compliance Modules -->
        <div>
          <div class="px-3 mb-2 text-[10px] font-extrabold tracking-widest text-[var(--text-faint)] uppercase">Modules Métiers</div>
          <div class="space-y-1">
            <a routerLink="/kyc" routerLinkActive="bg-[#E85D04]/10 border-l-4 border-[#E85D04] text-[#E85D04] font-bold"
              class="flex items-center gap-3 px-3 py-2 rounded-xl text-xs text-[var(--text-secondary)] hover:text-[#E85D04] hover:bg-[var(--bg-page-subtle)] transition-all group">
              <svg class="w-4 h-4 text-[var(--text-muted)] group-hover:text-[#E85D04]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              <span>Conformité KYC / AML</span>
            </a>

            <a routerLink="/contract" routerLinkActive="bg-[#E85D04]/10 border-l-4 border-[#E85D04] text-[#E85D04] font-bold"
              class="flex items-center gap-3 px-3 py-2 rounded-xl text-xs text-[var(--text-secondary)] hover:text-[#E85D04] hover:bg-[var(--bg-page-subtle)] transition-all group">
              <svg class="w-4 h-4 text-[var(--text-muted)] group-hover:text-[#E85D04]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
              </svg>
              <span>Analyse Contrats BCT</span>
            </a>

            <a routerLink="/credit" routerLinkActive="bg-[#E85D04]/10 border-l-4 border-[#E85D04] text-[#E85D04] font-bold"
              class="flex items-center gap-3 px-3 py-2 rounded-xl text-xs text-[var(--text-secondary)] hover:text-[#E85D04] hover:bg-[var(--bg-page-subtle)] transition-all group">
              <svg class="w-4 h-4 text-[var(--text-muted)] group-hover:text-[#E85D04]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              <span>Pré-filtrage Crédit</span>
            </a>
          </div>
        </div>

        <!-- Admin Section -->
        <div>
          <div class="px-3 mb-2 text-[10px] font-extrabold tracking-widest text-[var(--text-faint)] uppercase">Administration</div>
          <div class="space-y-1">
            <a routerLink="/admin/documents" routerLinkActive="bg-[#E85D04]/10 border-l-4 border-[#E85D04] text-[#E85D04] font-bold"
              class="flex items-center gap-3 px-3 py-2 rounded-xl text-xs text-[var(--text-secondary)] hover:text-[#E85D04] hover:bg-[var(--bg-page-subtle)] transition-all group">
              <svg class="w-4 h-4 text-[var(--text-muted)] group-hover:text-[#E85D04]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
              </svg>
              <span>Gestion Documentaire</span>
            </a>
          </div>
        </div>
      </div>

      <!-- User Profile Drawer & Logout -->
      <div class="p-3.5 border-t border-[var(--border-sidebar)] bg-[var(--bg-sidebar)] flex items-center justify-between">
        <div class="truncate mr-2">
          <div class="text-xs font-bold text-[var(--text-primary)] truncate">{{ auth.currentUser()?.full_name || auth.currentUser()?.username }}</div>
          <div class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-[#E85D04]/10 text-[#E85D04] text-[10px] font-bold tracking-wider uppercase mt-0.5">
            <span class="w-1.5 h-1.5 rounded-full bg-[#E85D04]"></span>
            {{ auth.userRole() }}
          </div>
        </div>
        <button (click)="auth.logout()" title="Déconnexion"
          class="p-2 rounded-xl text-[var(--text-muted)] hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-all">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
          </svg>
        </button>
      </div>
    </aside>
  `
})
export class SidebarComponent {
  auth = inject(AuthService);
  theme = inject(ThemeService);

  hasRole(roles: string[]): boolean {
    const userRole = this.auth.userRole();
    if (userRole === 'admin') return true;
    return roles.includes(userRole);
  }
}
