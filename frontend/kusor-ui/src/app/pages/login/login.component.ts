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
    <div class="min-h-screen flex items-center justify-center p-6 bg-[#03071E] relative overflow-hidden">
      <!-- Ambient Glow Blobs -->
      <div class="absolute -top-40 -left-40 w-96 h-96 bg-[#E85D04]/15 rounded-full blur-3xl pointer-events-none"></div>
      <div class="absolute -bottom-40 -right-40 w-96 h-96 bg-[#DC2F02]/10 rounded-full blur-3xl pointer-events-none"></div>

      <div class="w-full max-w-md p-8 glass-card space-y-6 relative z-10 bg-[#070A18]">
        <div class="text-center space-y-2">
          <img src="assets/attijari_logo.png" alt="Attijari Bank Logo" class="h-16 w-16 mx-auto object-cover rounded-2xl shadow-lg border border-[#E85D04]/30 mb-3" />
          <h1 class="text-3xl font-black tracking-tight brand-gradient-text">Attijari Bank Tunisia</h1>
          <p class="text-xs text-slate-400 font-medium">KUSOR v3 — Plateforme d'Intelligence Réglementaire</p>
        </div>

        @if (errorMessage()) {
          <div class="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-semibold">
            {{ errorMessage() }}
          </div>
        }

        <form (ngSubmit)="onSubmit()" class="space-y-4">
          <div>
            <label class="block text-[11px] font-extrabold text-slate-300 uppercase tracking-wider mb-2">Nom d'utilisateur</label>
            <input type="text" [(ngModel)]="username" name="username" required placeholder="ex: admin"
              class="w-full px-4 py-3.5 rounded-xl bg-[#03071E] border border-slate-800 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#E85D04] transition-all text-sm" />
          </div>

          <div>
            <label class="block text-[11px] font-extrabold text-slate-300 uppercase tracking-wider mb-2">Mot de passe</label>
            <input type="password" [(ngModel)]="password" name="password" required placeholder="••••••••"
              class="w-full px-4 py-3.5 rounded-xl bg-[#03071E] border border-slate-800 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#E85D04] transition-all text-sm" />
          </div>

          <button type="submit" [disabled]="loading()"
            class="w-full py-4 px-4 rounded-xl font-bold text-white bg-gradient-to-r from-[#FAA307] via-[#E85D04] to-[#DC2F02] hover:from-[#E85D04] hover:to-[#9D0208] shadow-xl shadow-[#E85D04]/30 transition-all disabled:opacity-50 text-sm">
            {{ loading() ? 'Connexion en cours...' : 'Se Connecter' }}
          </button>
        </form>
      </div>
    </div>
  `
})
export class LoginComponent {
  auth = inject(AuthService);
  router = inject(Router);

  username = '';
  password = '';
  loading = signal(false);
  errorMessage = signal('');

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
        this.errorMessage.set(err.error?.error || 'Échec de la connexion');
      }
    });
  }
}
