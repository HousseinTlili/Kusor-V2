import { Component, inject, signal, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, Router, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs';
import { SidebarComponent } from './shared/components/sidebar/sidebar.component';
import { AuthService } from './core/services/auth.service';
import { ThemeService } from './core/services/theme.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, SidebarComponent],
  template: `
    <div class="min-h-screen bg-[var(--bg-page)] text-[var(--text-primary)] flex font-sans transition-colors duration-200">
      @if (showSidebar()) {
        <app-sidebar></app-sidebar>
      }
      <main [class]="showSidebar() ? 'flex-1 lg:pl-64 min-h-screen transition-all duration-200' : 'w-full min-h-screen'">
        <router-outlet></router-outlet>
      </main>
    </div>
  `
})
export class App {
  auth = inject(AuthService);
  theme = inject(ThemeService);
  router = inject(Router);

  isLoginRoute = signal<boolean>(false);
  showSidebar = signal<boolean>(false);

  constructor() {
    this.router.events.pipe(
      filter(event => event instanceof NavigationEnd)
    ).subscribe((event: any) => {
      const isLogin = event.urlAfterRedirects.includes('/login') || event.url.includes('/login');
      this.isLoginRoute.set(isLogin);
      this.updateSidebarVisibility();
    });

    effect(() => {
      this.updateSidebarVisibility();
    }, { allowSignalWrites: true });
  }

  private updateSidebarVisibility() {
    const authenticated = this.auth.isAuthenticated();
    const isLogin = this.isLoginRoute();
    this.showSidebar.set(authenticated && !isLogin);
  }
}
