import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { NavbarComponent } from './shared/components/navbar/navbar.component';
import { AuthService } from './core/services/auth.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, NavbarComponent],
  template: `
    <div class="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      @if (auth.isAuthenticated()) {
        <app-navbar></app-navbar>
      }
      <main class="flex-1">
        <router-outlet></router-outlet>
      </main>
    </div>
  `
})
export class App {
  auth = inject(AuthService);
}
