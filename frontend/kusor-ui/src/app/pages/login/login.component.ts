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
    <div class="min-h-screen w-full bg-[var(--bg-page)] text-[var(--text-primary)] grid grid-cols-1 lg:grid-cols-12 font-sans transition-colors duration-200 overflow-x-hidden">
      
      <!-- LEFT HALF: Hero Visual with Theme Image & Compliance Features -->
      <div class="lg:col-span-7 relative hidden lg:flex flex-col justify-between p-10 xl:p-14 overflow-hidden border-r border-[var(--border-card)]">
        
        <!-- Hero Background Image with Gradient Overlay -->
        <div class="absolute inset-0 z-0">
          <img src="assets/images/login_hero.jpg" alt="KUSOR AI Banking Compliance Hero" 
            class="w-full h-full object-cover object-center transform scale-105 transition-transform duration-1000 hover:scale-100" />
          <div class="absolute inset-0 bg-gradient-to-t from-[#0F172A] via-[#0F172A]/70 to-transparent"></div>
          <div class="absolute inset-0 bg-gradient-to-r from-transparent via-[#0F172A]/40 to-[#0F172A]/90"></div>
        </div>

        <!-- Top Badge -->
        <div class="relative z-10">
          <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#E85D04]/20 border border-[#E85D04]/40 text-[#E85D04] text-xs font-bold uppercase tracking-wider backdrop-blur-md">
            <span>🛡️ Intelligence Réglementaire & Sécurité Bancaire</span>
          </div>
        </div>

        <!-- Center Tagline & Feature Pills -->
        <div class="relative z-10 space-y-4 my-auto max-w-lg">
          <h1 class="text-3xl xl:text-4xl font-black text-white leading-tight tracking-tight drop-shadow-md">
            L'Intelligence Artificielle au Service de la Conformité Bancaire
          </h1>

          <p class="text-sm text-slate-200 leading-relaxed drop-shadow-sm font-normal">
            Orchestration d'agents d'IA autonomes, extraction multi-fichiers PDF et validation temporelle des circulaires de la Banque Centrale de Tunisie.
          </p>

          <!-- Feature Pills Grid -->
          <div class="grid grid-cols-2 gap-3 pt-2">
            <div class="p-3 rounded-2xl bg-black/40 border border-white/10 backdrop-blur-md space-y-1">
              <div class="text-base">🪪</div>
              <div class="text-xs font-bold text-white">Contrôle KYC & Sanctions</div>
              <div class="text-[10px] text-slate-300">Extraction CIN & filtrage CTAF/OFAC</div>
            </div>

            <div class="p-3 rounded-2xl bg-black/40 border border-white/10 backdrop-blur-md space-y-1">
              <div class="text-base">💳</div>
              <div class="text-xs font-bold text-white">Pré-filtrage Crédit 3-Agents</div>
              <div class="text-[10px] text-slate-300">Plafond ratio d'endettement &le; 40%</div>
            </div>

            <div class="p-3 rounded-2xl bg-black/40 border border-white/10 backdrop-blur-md space-y-1">
              <div class="text-base">⚖️</div>
              <div class="text-xs font-bold text-white">Audit Juridique Contrats</div>
              <div class="text-[10px] text-slate-300">Segmentation des clauses & usure</div>
            </div>

            <div class="p-3 rounded-2xl bg-black/40 border border-white/10 backdrop-blur-md space-y-1">
              <div class="text-base">🕸️</div>
              <div class="text-xs font-bold text-white">Graphe Temporel Neo4j</div>
              <div class="text-[10px] text-slate-300">Traçabilité des abrogations BCT</div>
            </div>
          </div>
        </div>

        <!-- Bottom Left Compliance Footer -->
        <div class="relative z-10 text-[11px] text-slate-400 font-medium flex items-center justify-between border-t border-white/10 pt-4">
          <span>Plateforme Certifiée BCT • Version 3.0</span>
          <span>100% Conforme aux Normes Prudentielles</span>
        </div>

      </div>

      <!-- RIGHT HALF: Brand Header, Logo & Modern Login Form -->
      <div class="lg:col-span-5 flex flex-col justify-between p-6 sm:p-10 xl:p-12 relative z-10 bg-[var(--bg-page)]">
        
        <!-- Top Header Bar with Logo and Text on the Right Side -->
        <div class="flex items-center justify-between pb-6 border-b border-[var(--border-card)]">
          <!-- Logo and Title on Right Side -->
          <div class="flex items-center space-x-3.5">
            <img src="assets/attijari_logo.png" alt="Attijari Bank Logo" 
              class="h-10 w-auto object-contain rounded-xl shadow-md border border-[var(--border-card)] bg-white p-1" />
            <div class="h-8 w-px bg-[var(--border-card)]"></div>
            <div>
              <div class="text-xs font-black uppercase tracking-widest text-[#E85D04]">KUSOR v3</div>
              <div class="text-[11px] text-[var(--text-muted)] font-semibold">Attijari Bank Tunisie</div>
            </div>
          </div>

          <!-- Controls: Theme toggle & Status -->
          <div class="flex items-center space-x-2.5">
            <span class="hidden sm:inline-flex items-center px-2.5 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-400 text-[10px] font-semibold">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse mr-1.5"></span>
              BCT Connecté
            </span>

            <button (click)="theme.toggleTheme()" [title]="theme.isDark() ? 'Activer le mode clair' : 'Activer le mode sombre'"
              class="p-2 rounded-xl text-[var(--text-muted)] hover:text-[#E85D04] border border-[var(--border-card)] bg-[var(--bg-card)] shadow-sm transition-all">
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
          </div>
        </div>

        <!-- Center Login Form Area -->
        <div class="my-auto w-full max-w-md mx-auto space-y-6 py-6">
          
          <div class="space-y-1.5">
            <h2 class="text-2xl sm:text-3xl font-black tracking-tight text-[var(--text-primary)]">Connexion au Portail</h2>
            <p class="text-xs text-[var(--text-muted)]">Accédez à votre espace d'intelligence réglementaire et conformité BCT.</p>
          </div>

          <!-- Error Alert Banner -->
          @if (errorMessage()) {
            <div class="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 text-xs font-semibold flex items-center space-x-3 animate-fadeIn">
              <svg class="w-4 h-4 text-rose-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span>{{ errorMessage() }}</span>
            </div>
          }

          <!-- Form Inputs -->
          <form (ngSubmit)="onSubmit()" class="space-y-4">
            <div>
              <label class="block text-[11px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1.5">Identifiant Utilisateur</label>
              <div class="relative">
                <input type="text" [(ngModel)]="username" name="username" required placeholder="Ex: admin ou compliance_user"
                  class="w-full pl-11 pr-4 py-3 rounded-xl bg-[var(--bg-input)] border border-[var(--border-input)] text-[var(--text-primary)] placeholder-[var(--text-faint)] focus:outline-none focus:border-[#E85D04] focus:ring-2 focus:ring-[#E85D04]/20 transition-all text-xs font-medium" />
                <svg class="w-4 h-4 text-[var(--text-muted)] absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
            </div>

            <div>
              <label class="block text-[11px] font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1.5">Mot de Passe</label>
              <div class="relative">
                <input type="password" [(ngModel)]="password" name="password" required placeholder="••••••••"
                  class="w-full pl-11 pr-4 py-3 rounded-xl bg-[var(--bg-input)] border border-[var(--border-input)] text-[var(--text-primary)] placeholder-[var(--text-faint)] focus:outline-none focus:border-[#E85D04] focus:ring-2 focus:ring-[#E85D04]/20 transition-all text-xs font-medium" />
                <svg class="w-4 h-4 text-[var(--text-muted)] absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
            </div>

            <button type="submit" [disabled]="loading() || !username || !password"
              class="w-full py-3.5 px-4 rounded-xl font-bold bg-gradient-to-r from-[#E85D04] to-[#F48C06] hover:from-[#DC2F02] hover:to-[#E85D04] text-white shadow-lg shadow-[#E85D04]/25 transition-all text-xs flex items-center justify-center space-x-2 disabled:opacity-50">
              @if (loading()) {
                <svg class="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Authentification en cours...</span>
              } @else {
                <span>Se Connecter à KUSOR</span>
                <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              }
            </button>
          </form>

          <!-- Quick Preset Demo Accounts -->
          <div class="pt-4 border-t border-[var(--border-card)] space-y-2.5">
            <div class="text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)] text-center">
              Comptes Démonstration (1-Clic pour Remplir) :
            </div>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <button type="button" (click)="setRole('admin')" class="px-2.5 py-2 rounded-xl bg-[var(--bg-page-subtle)] hover:bg-[#E85D04]/10 hover:border-[#E85D04]/40 border border-[var(--border-card)] text-[10px] font-bold text-[var(--text-secondary)] hover:text-[#E85D04] transition-all text-center">
                👑 Admin
              </button>
              <button type="button" (click)="setRole('compliance')" class="px-2.5 py-2 rounded-xl bg-[var(--bg-page-subtle)] hover:bg-[#E85D04]/10 hover:border-[#E85D04]/40 border border-[var(--border-card)] text-[10px] font-bold text-[var(--text-secondary)] hover:text-[#E85D04] transition-all text-center">
                🛡️ Conformité
              </button>
              <button type="button" (click)="setRole('credit')" class="px-2.5 py-2 rounded-xl bg-[var(--bg-page-subtle)] hover:bg-[#E85D04]/10 hover:border-[#E85D04]/40 border border-[var(--border-card)] text-[10px] font-bold text-[var(--text-secondary)] hover:text-[#E85D04] transition-all text-center">
                💳 Crédit
              </button>
              <button type="button" (click)="setRole('legal')" class="px-2.5 py-2 rounded-xl bg-[var(--bg-page-subtle)] hover:bg-[#E85D04]/10 hover:border-[#E85D04]/40 border border-[var(--border-card)] text-[10px] font-bold text-[var(--text-secondary)] hover:text-[#E85D04] transition-all text-center">
                ⚖️ Juridique
              </button>
            </div>
          </div>

        </div>

        <!-- Bottom Security Notice -->
        <div class="pt-6 text-center text-[10px] text-[var(--text-muted)] space-y-1 border-t border-[var(--border-card)]">
          <div>🔒 Authentification sécurisée JWT • Journal d'audit certifié SHA-256</div>
          <div>Attijari Bank Tunisie &copy; 2026. Tous droits réservés.</div>
        </div>

      </div>

    </div>
  `,
  styles: [`
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(-4px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .animate-fadeIn {
      animation: fadeIn 0.25s ease-out forwards;
    }
  `]
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
    if (role === 'admin') {
      this.username = 'admin';
      this.password = 'Admin123!';
    } else if (role === 'compliance') {
      this.username = 'compliance_user';
      this.password = 'User123!';
    } else if (role === 'credit') {
      this.username = 'credit_officer';
      this.password = 'User123!';
    } else if (role === 'legal') {
      this.username = 'legal_advisor';
      this.password = 'User123!';
    } else {
      this.username = 'compliance_user';
      this.password = 'User123!';
    }
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
