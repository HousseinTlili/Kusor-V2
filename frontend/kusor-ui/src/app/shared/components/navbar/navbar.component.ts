import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive],
  template: `
    <header class="sticky top-0 z-50 bg-slate-900/90 backdrop-blur-md border-b border-amber-500/20 px-6 py-3 shadow-xl">
      <div class="max-w-7xl mx-auto flex items-center justify-between">
        <!-- Logo Brand -->
        <div class="flex items-center gap-3">
          <div class="p-2 rounded-xl bg-gradient-to-br from-amber-500 to-amber-600 text-slate-950 font-bold shadow-lg shadow-amber-500/20">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
            </svg>
          </div>
          <div>
            <span class="text-xl font-extrabold tracking-wider gold-gradient-text">KUSOR v3</span>
            <span class="ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30">Attijari Bank</span>
          </div>
        </div>

        <!-- Navigation Links -->
        <nav class="hidden md:flex items-center space-x-1 text-sm font-medium">
          <a routerLink="/dashboard" routerLinkActive="bg-amber-500/15 text-amber-400 border-amber-500/40" class="px-3.5 py-2 rounded-lg text-slate-300 hover:text-amber-400 border border-transparent transition-all">Tableau de bord</a>
          <a routerLink="/chat" routerLinkActive="bg-amber-500/15 text-amber-400 border-amber-500/40" class="px-3.5 py-2 rounded-lg text-slate-300 hover:text-amber-400 border border-transparent transition-all">Assistant RAG</a>
          <a routerLink="/graph" routerLinkActive="bg-amber-500/15 text-amber-400 border-amber-500/40" class="px-3.5 py-2 rounded-lg text-slate-300 hover:text-amber-400 border border-transparent transition-all">Graphe Connaissances</a>
          <a routerLink="/temporal-explorer" routerLinkActive="bg-amber-500/15 text-amber-400 border-amber-500/40" class="px-3.5 py-2 rounded-lg text-slate-300 hover:text-amber-400 border border-transparent transition-all">Explorateur Temporel</a>

          @if (hasRole(['compliance'])) {
            <a routerLink="/kyc" routerLinkActive="bg-amber-500/15 text-amber-400 border-amber-500/40" class="px-3.5 py-2 rounded-lg text-slate-300 hover:text-amber-400 border border-transparent transition-all">Conformité KYC</a>
          }
          @if (hasRole(['legal'])) {
            <a routerLink="/contract" routerLinkActive="bg-amber-500/15 text-amber-400 border-amber-500/40" class="px-3.5 py-2 rounded-lg text-slate-300 hover:text-amber-400 border border-transparent transition-all">Analyse Contrats</a>
          }
          @if (hasRole(['credit'])) {
            <a routerLink="/credit" routerLinkActive="bg-amber-500/15 text-amber-400 border-amber-500/40" class="px-3.5 py-2 rounded-lg text-slate-300 hover:text-amber-400 border border-transparent transition-all">Pré-filtrage Crédit</a>
          }
          @if (hasRole(['admin'])) {
            <a routerLink="/admin/documents" routerLinkActive="bg-amber-500/15 text-amber-400 border-amber-500/40" class="px-3.5 py-2 rounded-lg text-slate-300 hover:text-amber-400 border border-transparent transition-all">Admin Documents</a>
          }
        </nav>

        <!-- User Profile & Logout -->
        <div class="flex items-center gap-4">
          <div class="text-right hidden sm:block">
            <div class="text-sm font-semibold text-slate-200">{{ auth.currentUser()?.full_name || auth.currentUser()?.username }}</div>
            <div class="text-xs uppercase tracking-wider text-amber-400 font-medium">{{ auth.userRole() }}</div>
          </div>
          <button (click)="auth.logout()" class="p-2 rounded-xl bg-slate-800/80 hover:bg-rose-500/20 hover:text-rose-400 text-slate-400 border border-slate-700/60 transition-all">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
            </svg>
          </button>
        </div>
      </div>
    </header>
  `
})
export class NavbarComponent {
  auth = inject(AuthService);

  hasRole(roles: string[]): boolean {
    const r = this.auth.userRole();
    return r === 'admin' || roles.includes(r);
  }
}
