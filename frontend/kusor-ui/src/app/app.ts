import { Component, inject, signal, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, Router, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs';
import { SidebarComponent } from './shared/components/sidebar/sidebar.component';
import { AuthService } from './core/services/auth.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, SidebarComponent],
  template: `
    <div class="min-h-screen bg-[#000000] text-slate-100 flex font-sans">
      @if (showSidebar()) {
        <app-sidebar></app-sidebar>
      }
      <main [class]="showSidebar() ? 'flex-1 pl-64 min-h-screen' : 'w-full min-h-screen'">
        <router-outlet></router-outlet>
      </main>
    </div>
  `
})
export class App {
  auth = inject(AuthService);
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
