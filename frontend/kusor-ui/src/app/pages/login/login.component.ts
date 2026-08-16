import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="min-h-screen w-full bg-[#000000] text-slate-100 flex flex-col justify-between relative overflow-hidden font-sans">
      
      <!-- Background Ambient Light Spots & Tech Grid -->
      <div class="absolute inset-0 bg-[radial-gradient(#262626_1px,transparent_1px)] [background-size:32px_32px] opacity-20 pointer-events-none"></div>
      <div class="absolute -top-40 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-[#E85D04]/15 rounded-full blur-[150px] pointer-events-none"></div>
      <div class="absolute -bottom-40 -left-40 w-[600px] h-[600px] bg-[#DC2F02]/10 rounded-full blur-[180px] pointer-events-none"></div>

      <!-- Top Header Bar -->
      <header class="w-full max-w-7xl mx-auto px-6 py-6 flex items-center justify-between relative z-20">
        <div class="flex items-center space-x-4">
          <img src="assets/attijari_logo.png" alt="Attijari Bank Logo" class="h-12 w-auto object-contain" />
          <div class="h-8 w-px bg-slate-800"></div>
          <div>
            <span class="text-xs font-black uppercase tracking-widest text-[#E85D04]">KUSOR v3</span>
            <p class="text-[11px] text-slate-400 font-medium">Compliance & Regulatory Intelligence</p>
          </div>
        </div>
        <div class="hidden sm:flex items-center space-x-2 text-xs font-semibold">
          <span class="inline-flex items-center px-3 py-1.5 rounded-full bg-[#E85D04]/10 border border-[#E85D04]/30 text-[#E85D04]">
            <span class="w-2 h-2 rounded-full bg-[#E85D04] animate-pulse mr-2"></span>
            BCT Regulatory Node Active
          </span>
        </div>
      </header>

      <!-- Center Content Area -->
      <div class="w-full max-w-lg mx-auto px-6 py-8 relative z-20 flex-1 flex flex-col justify-center">
        <div class="p-8 rounded-3xl bg-[#0A0A0A] border border-[#E85D04]/30 shadow-[0_0_50px_rgba(0,0,0,0.9)] backdrop-blur-2xl space-y-6">
          
          <!-- Logo & Title -->
          <div class="text-center space-y-2">
            <div class="inline-flex p-4 rounded-2xl bg-[#03071E] border border-[#E85D04]/30 shadow-inner justify-center items-center mb-1">
              <img src="assets/attijari_logo.png" alt="Attijari Bank" class="h-10 w-auto object-contain max-w-[180px]" />
            </div>
            <h1 class="text-2xl font-extrabold tracking-tight text-white">Connexion au Portail</h1>
            <p class="text-xs text-slate-400 font-medium">Plateforme IA d'Intelligence Réglementaire BCT</p>
          </div>

          <!-- Error Message Banner -->
          @if (errorMessage()) {
            <div class="p-4 rounded-xl bg-rose-950/50 border border-rose-500/40 text-rose-300 text-xs font-semibold flex items-center space-x-3">
              <svg class="w-5 h-5 text-rose-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span>{{ errorMessage() }}</span>
            </div>
          }

          <!-- Form Fields -->
          <form (ngSubmit)="onSubmit()" class="space-y-4">
            <div>
              <label class="block text-[11px] font-bold text-slate-300 uppercase tracking-wider mb-1.5">Identifiant Utilisateur</label>
              <div class="relative">
                <input type="text" [(ngModel)]="username" name="username" required placeholder="Ex: admin"
                  class="w-full pl-11 pr-4 py-3 rounded-xl bg-[#03071E] border border-slate-800 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-[#E85D04] focus:ring-1 focus:ring-[#E85D04] transition-all text-xs font-medium" />
                <svg class="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
            </div>

            <div>
              <label class="block text-[11px] font-bold text-slate-300 uppercase tracking-wider mb-1.5">Mot de passe</label>
              <div class="relative">
                <input type="password" [(ngModel)]="password" name="password" required placeholder="••••••••"
                  class="w-full pl-11 pr-4 py-3 rounded-xl bg-[#03071E] border border-slate-800 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-[#E85D04] focus:ring-1 focus:ring-[#E85D04] transition-all text-xs font-medium" />
                <svg class="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
            </div>

            <button type="submit" [disabled]="loading()"
              class="w-full py-3.5 px-4 rounded-xl font-bold text-white bg-gradient-to-r from-[#E85D04] via-[#F48C06] to-[#DC2F02] hover:opacity-95 active:scale-[0.99] shadow-lg shadow-[#E85D04]/30 transition-all disabled:opacity-50 text-xs flex items-center justify-center space-x-2">
              @if (loading()) {
                <svg class="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Connexion en cours...</span>
              } @else {
                <span>Se Connecter</span>
                <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              }
            </button>
          </form>

          <!-- 5 Demo Role Presets -->
          <div class="pt-4 border-t border-slate-800/80 space-y-2">
            <p class="text-[11px] font-bold text-slate-400 uppercase tracking-wider text-center mb-2">Les 5 Rôles de Démonstration (Accès Rapide)</p>
            <div class="grid grid-cols-2 gap-2">
              <button (click)="fillPreset('admin', 'Password123!')" type="button"
                class="px-3 py-2 rounded-xl bg-[#03071E] border border-slate-800 hover:border-[#E85D04]/60 text-xs font-semibold text-slate-300 hover:text-white transition-all flex items-center justify-between">
                <span>Administrateur</span>
                <span class="text-[10px] px-1.5 py-0.5 rounded-md bg-[#E85D04]/20 text-[#E85D04] font-bold">Admin</span>
              </button>

              <button (click)="fillPreset('compliance', 'Password123!')" type="button"
                class="px-3 py-2 rounded-xl bg-[#03071E] border border-slate-800 hover:border-[#E85D04]/60 text-xs font-semibold text-slate-300 hover:text-white transition-all flex items-center justify-between">
                <span>Conformité</span>
                <span class="text-[10px] px-1.5 py-0.5 rounded-md bg-emerald-500/20 text-emerald-400 font-bold">Compliance</span>
              </button>

              <button (click)="fillPreset('legal', 'Password123!')" type="button"
                class="px-3 py-2 rounded-xl bg-[#03071E] border border-slate-800 hover:border-[#E85D04]/60 text-xs font-semibold text-slate-300 hover:text-white transition-all flex items-center justify-between">
                <span>Juridique</span>
                <span class="text-[10px] px-1.5 py-0.5 rounded-md bg-indigo-500/20 text-indigo-400 font-bold">Legal</span>
              </button>

              <button (click)="fillPreset('credit', 'Password123!')" type="button"
                class="px-3 py-2 rounded-xl bg-[#03071E] border border-slate-800 hover:border-[#E85D04]/60 text-xs font-semibold text-slate-300 hover:text-white transition-all flex items-center justify-between">
                <span>Risques Crédit</span>
                <span class="text-[10px] px-1.5 py-0.5 rounded-md bg-amber-500/20 text-amber-400 font-bold">Credit</span>
              </button>

              <button (click)="fillPreset('user', 'Password123!')" type="button"
                class="px-3 py-2 rounded-xl bg-[#03071E] border border-slate-800 hover:border-[#E85D04]/60 text-xs font-semibold text-slate-300 hover:text-white transition-all flex items-center justify-between col-span-2">
                <span>Utilisateur Consultatif</span>
                <span class="text-[10px] px-1.5 py-0.5 rounded-md bg-slate-700 text-slate-300 font-bold">User</span>
              </button>
            </div>
          </div>

        </div>
      </div>

      <!-- Footer Bar -->
      <footer class="w-full max-w-7xl mx-auto px-6 py-4 flex flex-col sm:flex-row items-center justify-between text-[11px] text-slate-500 border-t border-slate-900/80 relative z-20 gap-2">
        <p>© 2026 Attijari Bank Tunisia. Tous droits réservés.</p>
        <p>KUSOR v3 — Intelligence Artificielle & Graphe de Connaissances Temporel</p>
      </footer>

    </div>
  `
})
export class LoginComponent {
  auth = inject(AuthService);
  router = inject(Router);

  username = 'admin';
  password = 'Password123!';
  loading = signal(false);
  errorMessage = signal('');

  fillPreset(user: string, pass: string) {
    this.username = user;
    this.password = pass;
  }

  onSubmit() {
    if (!this.username || !this.password) return;
    this.loading.set(true);
    this.errorMessage.set('');

    this.auth.login({ username: this.username, password: this.password }).subscribe({
      next: () => {
        this.loading.set(false);
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.loading.set(false);
        this.errorMessage.set(err.error?.error || 'Identifiants invalides');
      }
    });
  }
}
