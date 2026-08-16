import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { ThemeService } from '../../core/services/theme.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="min-h-screen w-full bg-[var(--bg-page)] text-[var(--text-primary)] flex flex-col justify-between relative overflow-hidden font-sans transition-colors duration-200">
      
      <!-- Background Ambient Light Spots & Grid -->
      <div class="absolute inset-0 bg-[radial-gradient(#CBD5E1_1px,transparent_1px)] dark:bg-[radial-gradient(#1E293B_1px,transparent_1px)] [background-size:32px_32px] opacity-40 pointer-events-none"></div>
      <div class="absolute -top-40 left-1/2 -translate-x-1/2 w-[700px] h-[350px] bg-[#E85D04]/10 rounded-full blur-[140px] pointer-events-none"></div>

      <!-- Top Header Bar -->
      <header class="w-full max-w-7xl mx-auto px-6 py-6 flex items-center justify-between relative z-20">
        <div class="flex items-center space-x-4">
          <img src="assets/attijari_logo.png" alt="Attijari Bank Logo" class="h-10 w-auto object-contain rounded-lg shadow-sm border border-[var(--border-card)]" />
          <div class="h-8 w-px bg-[var(--border-card)]"></div>
          <div>
            <span class="text-xs font-black uppercase tracking-widest text-[#E85D04]">KUSOR v3</span>
            <p class="text-[11px] text-[var(--text-muted)] font-medium">Compliance & Regulatory Intelligence — Attijari Bank</p>
          </div>
        </div>

        <div class="flex items-center space-x-3 text-xs font-semibold">
          <button (click)="theme.toggleTheme()" [title]="theme.isDark() ? 'Activer le mode clair' : 'Activer le mode sombre'"
            class="p-2.5 rounded-xl text-[var(--text-muted)] hover:text-[#E85D04] hover:bg-[var(--accent-orange-light)] border border-[var(--border-card)] bg-[var(--bg-card)] shadow-sm transition-all">
            @if (theme.isDark()) {
              <svg class="w-4 h-4 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            } @else {
              <svg class="w-4 h-4 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            }
          </button>

          <span class="hidden sm:inline-flex items-center px-3.5 py-1.5 rounded-full bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-400 text-xs font-semibold">
            <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse mr-2"></span>
            Nœud Réglementaire BCT Actif
          </span>
        </div>
      </header>

      <!-- Center Login Card -->
      <div class="w-full max-w-lg mx-auto px-6 py-8 relative z-20 flex-1 flex flex-col justify-center">
        <div class="glass-card p-8 shadow-xl space-y-6">
          
          <!-- Logo & Title -->
          <div class="text-center space-y-2">
            <div class="inline-flex p-3 rounded-2xl bg-[var(--bg-page-subtle)] border border-[var(--border-card)] shadow-inner justify-center items-center mb-1">
              <img src="assets/attijari_logo.png" alt="Attijari Bank" class="h-10 w-auto object-contain max-w-[180px]" />
            </div>
            <h1 class="text-2xl font-black tracking-tight text-[var(--text-primary)]">Connexion au Portail</h1>
            <p class="text-xs text-[var(--text-muted)] font-medium">Intelligence Réglementaire & Conformité BCT</p>
          </div>

          <!-- Error Message Banner -->
          @if (errorMessage()) {
            <div class="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 text-xs font-semibold flex items-center space-x-3">
              <svg class="w-4 h-4 text-rose-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span>{{ errorMessage() }}</span>
            </div>
          }

          <!-- Form Fields -->
          <form (ngSubmit)="onSubmit()" class="space-y-4">
            <div>
              <label class="block text-[11px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1.5">Identifiant Utilisateur</label>
              <div class="relative">
                <input type="text" [(ngModel)]="username" name="username" required placeholder="Ex: admin"
                  class="w-full pl-11 pr-4 py-3 rounded-xl bg-[var(--bg-input)] border border-[var(--border-input)] text-[var(--text-primary)] placeholder-[var(--text-faint)] focus:outline-none focus:border-[#E85D04] focus:ring-2 focus:ring-[#E85D04]/20 transition-all text-xs font-medium" />
                <svg class="w-4 h-4 text-[var(--text-muted)] absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
            </div>

            <div>
              <label class="block text-[11px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1.5">Mot de passe</label>
              <div class="relative">
                <input type="password" [(ngModel)]="password" name="password" required placeholder="••••••••"
                  class="w-full pl-11 pr-4 py-3 rounded-xl bg-[var(--bg-input)] border border-[var(--border-input)] text-[var(--text-primary)] placeholder-[var(--text-faint)] focus:outline-none focus:border-[#E85D04] focus:ring-2 focus:ring-[#E85D04]/20 transition-all text-xs font-medium" />
                <svg class="w-4 h-4 text-[var(--text-muted)] absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
            </div>

            <button type="submit" [disabled]="loading()"
              class="w-full py-3.5 px-4 rounded-xl font-bold brand-btn-primary transition-all text-xs flex items-center justify-center space-x-2">
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

          <!-- Demo Profiles Selector -->
          <div class="pt-4 border-t border-[var(--border-card)]">
            <div class="text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)] text-center mb-2.5">Comptes de Démonstration (Cliquez pour remplir)</div>
            <div class="grid grid-cols-5 gap-1.5">
              <button type="button" (click)="setRole('admin')" class="px-2 py-2 rounded-lg bg-[var(--bg-page-subtle)] hover:bg-[#E85D04]/10 hover:border-[#E85D04]/40 border border-[var(--border-card)] text-[10px] font-bold text-[var(--text-secondary)] transition-all text-center">
                Admin
              </button>
              <button type="button" (click)="setRole('compliance')" class="px-2 py-2 rounded-lg bg-[var(--bg-page-subtle)] hover:bg-[#E85D04]/10 hover:border-[#E85D04]/40 border border-[var(--border-card)] text-[10px] font-bold text-[var(--text-secondary)] transition-all text-center">
                Conformité
              </button>
              <button type="button" (click)="setRole('legal')" class="px-2 py-2 rounded-lg bg-[var(--bg-page-subtle)] hover:bg-[#E85D04]/10 hover:border-[#E85D04]/40 border border-[var(--border-card)] text-[10px] font-bold text-[var(--text-secondary)] transition-all text-center">
                Juridique
              </button>
              <button type="button" (click)="setRole('credit')" class="px-2 py-2 rounded-lg bg-[var(--bg-page-subtle)] hover:bg-[#E85D04]/10 hover:border-[#E85D04]/40 border border-[var(--border-card)] text-[10px] font-bold text-[var(--text-secondary)] transition-all text-center">
                Crédit
              </button>
              <button type="button" (click)="setRole('user')" class="px-2 py-2 rounded-lg bg-[var(--bg-page-subtle)] hover:bg-[#E85D04]/10 hover:border-[#E85D04]/40 border border-[var(--border-card)] text-[10px] font-bold text-[var(--text-secondary)] transition-all text-center">
                Analyste
              </button>
            </div>
          </div>

        </div>
      </div>

      <!-- Footer -->
      <footer class="w-full max-w-7xl mx-auto px-6 py-4 text-center text-xs text-[var(--text-faint)] relative z-20">
        Attijari Bank Tunisie &copy; 2026 — Plateforme d'Intelligence Réglementaire KUSOR v3. Tous droits réservés.
      </footer>
    </div>
  `
})
export class LoginComponent {
  auth = inject(AuthService);
  theme = inject(ThemeService);
  router = inject(Router);

  username = '';
  password = '';
  loading = signal(false);
  errorMessage = signal<string | null>(null);

  setRole(role: string) {
    this.username = role;
    this.password = 'Password123!';
    this.errorMessage.set(null);
  }

  onSubmit() {
    if (!this.username || !this.password) return;
    this.loading.set(true);
    this.errorMessage.set(null);

    this.auth.login({ username: this.username, password: this.password }).subscribe({
      next: () => {
        this.loading.set(false);
        this.router.navigate(['/dashboard']);
      },
      error: (err: any) => {
        this.loading.set(false);
        this.errorMessage.set(err?.error?.error || 'Identifiants invalides. Veuillez réessayer.');
      }
    });
  }
}
