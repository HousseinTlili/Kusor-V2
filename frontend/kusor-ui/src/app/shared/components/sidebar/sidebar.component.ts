import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive],
  template: `
    <aside class="fixed top-0 left-0 bottom-0 w-64 bg-[#03071E] border-r border-[#E85D04]/30 flex flex-col z-50 shadow-2xl">
      <!-- Attijari Bank Brand Header -->
      <div class="p-5 border-b border-[#E85D04]/30 flex items-center gap-3 bg-[#03071E]">
        <img src="assets/attijari_logo.png" alt="Attijari Bank Logo" class="h-10 w-10 object-cover rounded-lg shadow-md border border-[#E85D04]/30" />
        <div>
          <span class="text-xl font-black tracking-wider brand-gradient-text">KUSOR v3</span>
          <div class="text-[10px] font-extrabold tracking-widest text-[#E85D04] uppercase">Attijari Bank</div>
        </div>
      </div>

      <!-- Navigation Section -->
      <div class="flex-1 overflow-y-auto px-4 py-6 space-y-6 bg-[#03071E]">
        <!-- Main Navigation -->
        <div>
          <div class="px-3 mb-2 text-[10px] font-extrabold tracking-widest text-slate-400 uppercase">Vue d'Ensemble</div>
          <div class="space-y-1">
            <a routerLink="/dashboard" routerLinkActive="bg-[#E85D04]/20 border-l-4 border-[#E85D04] text-[#E85D04] font-bold"
              class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs text-slate-200 hover:text-white hover:bg-[#070A18] transition-all group">
              <svg class="w-4 h-4 text-slate-400 group-hover:text-[#E85D04]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
              </svg>
              Tableau de Bord
            </a>

            <a routerLink="/chat" routerLinkActive="bg-[#E85D04]/20 border-l-4 border-[#E85D04] text-[#E85D04] font-bold"
              class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs text-slate-200 hover:text-white hover:bg-[#070A18] transition-all group">
              <svg class="w-4 h-4 text-slate-400 group-hover:text-[#E85D04]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
              </svg>
              Assistant RAG
            </a>

            <a routerLink="/graph" routerLinkActive="bg-[#E85D04]/20 border-l-4 border-[#E85D04] text-[#E85D04] font-bold"
              class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs text-slate-200 hover:text-white hover:bg-[#070A18] transition-all group">
              <svg class="w-4 h-4 text-slate-400 group-hover:text-[#E85D04]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
              </svg>
              Graphe Neo4j
            </a>

            <a routerLink="/temporal-explorer" routerLinkActive="bg-[#E85D04]/20 border-l-4 border-[#E85D04] text-[#E85D04] font-bold"
              class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs text-slate-200 hover:text-white hover:bg-[#070A18] transition-all group">
              <svg class="w-4 h-4 text-slate-400 group-hover:text-[#E85D04]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              Explorateur Temporel
            </a>
          </div>
        </div>

        <!-- Compliance Modules -->
        <div>
          <div class="px-3 mb-2 text-[10px] font-extrabold tracking-widest text-slate-400 uppercase">Modules Métiers</div>
          <div class="space-y-1">
            @if (hasRole(['compliance'])) {
              <a routerLink="/kyc" routerLinkActive="bg-[#E85D04]/20 border-l-4 border-[#E85D04] text-[#E85D04] font-bold"
                class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs text-slate-200 hover:text-white hover:bg-[#070A18] transition-all group">
                <svg class="w-4 h-4 text-slate-400 group-hover:text-[#E85D04]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                Conformité KYC
              </a>
            }

            @if (hasRole(['legal'])) {
              <a routerLink="/contract" routerLinkActive="bg-[#E85D04]/20 border-l-4 border-[#E85D04] text-[#E85D04] font-bold"
                class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs text-slate-200 hover:text-white hover:bg-[#070A18] transition-all group">
                <svg class="w-4 h-4 text-slate-400 group-hover:text-[#E85D04]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                </svg>
                Analyse Contrats
              </a>
            }

            @if (hasRole(['credit'])) {
              <a routerLink="/credit" routerLinkActive="bg-[#E85D04]/20 border-l-4 border-[#E85D04] text-[#E85D04] font-bold"
                class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs text-slate-200 hover:text-white hover:bg-[#070A18] transition-all group">
                <svg class="w-4 h-4 text-slate-400 group-hover:text-[#E85D04]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                Pré-filtrage Crédit
              </a>
            }
          </div>
        </div>

        <!-- Admin Section -->
        @if (hasRole(['admin'])) {
          <div>
            <div class="px-3 mb-2 text-[10px] font-extrabold tracking-widest text-slate-400 uppercase">Administration</div>
            <div class="space-y-1">
              <a routerLink="/admin/documents" routerLinkActive="bg-[#E85D04]/20 border-l-4 border-[#E85D04] text-[#E85D04] font-bold"
                class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs text-slate-200 hover:text-white hover:bg-[#070A18] transition-all group">
                <svg class="w-4 h-4 text-slate-400 group-hover:text-[#E85D04]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                </svg>
                Admin Documents
              </a>
            </div>
          </div>
        }
      </div>

      <!-- User Profile Drawer -->
      <div class="p-4 border-t border-[#E85D04]/30 flex items-center justify-between bg-[#03071E]">
        <div class="truncate">
          <div class="text-xs font-bold text-slate-100 truncate">{{ auth.currentUser()?.full_name || auth.currentUser()?.username }}</div>
          <div class="text-[10px] font-semibold text-[#E85D04] uppercase tracking-wider">{{ auth.userRole() }}</div>
        </div>

        <button (click)="auth.logout()" class="p-2 rounded-xl bg-[#070A18] hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 border border-slate-800 transition-all">
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

  hasRole(roles: string[]): boolean {
    const r = this.auth.userRole();
    return r === 'admin' || roles.includes(r);
  }
}
