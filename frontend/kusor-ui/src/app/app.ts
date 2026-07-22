import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { SidebarComponent } from './shared/components/sidebar/sidebar.component';
import { AuthService } from './core/services/auth.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, SidebarComponent],
  template: `
    <div class="min-h-screen bg-[#03071E] text-slate-100 flex font-sans">
      @if (auth.isAuthenticated()) {
        <app-sidebar></app-sidebar>
      }
      <main [class]="auth.isAuthenticated() ? 'flex-1 pl-64 min-h-screen' : 'flex-1 min-h-screen'">
        <router-outlet></router-outlet>
      </main>
    </div>
  `
})
export class App {
  auth = inject(AuthService);
}
