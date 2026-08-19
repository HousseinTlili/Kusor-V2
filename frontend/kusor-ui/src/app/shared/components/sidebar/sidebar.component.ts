import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { ThemeService } from '../../../core/services/theme.service';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive],
  template: `
    <aside class="sidebar-wrapper">
      <!-- 1. Attijari Bank Header -->
      <div class="sidebar-brand" routerLink="/dashboard">
        <div class="brand-logo-container">
          <img 
            src="assets/attijari_logo.png" 
            alt="Attijari Bank" 
            class="attijari-logo-img"
          />
        </div>

        <div class="brand-text">
          <div class="brand-title-row">
            <span class="brand-attijari">Attijari</span>
            <span class="brand-bank">bank</span>
            <span class="brand-ai-badge">AI</span>
          </div>
          <span class="brand-subtitle">Veille & Conformité BCT</span>
        </div>
      </div>

      <!-- 2. Vertical Navigation Menu -->
      <nav class="sidebar-nav">
        <!-- Section: Vue d'Ensemble -->
        <div class="nav-group">
          <div class="nav-group-title">Vue d'Ensemble</div>
          
          <a routerLink="/dashboard" routerLinkActive="active" class="nav-item">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
            </svg>
            <span class="nav-label">Tableau de Bord</span>
          </a>

          <a routerLink="/chat" routerLinkActive="active" class="nav-item">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a.75.75 0 01-1.074-.85 5.97 5.97 0 00.92-2.427C3.805 16.32 3 14.28 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
            </svg>
            <span class="nav-label">Assistant Chat IA</span>
          </a>

          <a routerLink="/graph" routerLinkActive="active" class="nav-item">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 14.25v2.25m3-4.5v4.5m3-6.75v6.75m3-9v9M6 20.25h12A2.25 2.25 0 0020.25 18V6A2.25 2.25 0 0018 3.75H6A2.25 2.25 0 003.75 6v12A2.25 2.25 0 006 20.25z" />
            </svg>
            <span class="nav-label">Graphe Neo4j</span>
          </a>

          <a routerLink="/temporal-explorer" routerLinkActive="active" class="nav-item">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span class="nav-label">Explorateur Temporel</span>
          </a>

          <a routerLink="/impact-viewer" routerLinkActive="active" class="nav-item">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
            </svg>
            <span class="nav-label">Impact Réglementaire</span>
          </a>
        </div>

        <!-- Section: Modules Métiers -->
        <div class="nav-group">
          <div class="nav-group-title">Modules Métiers BCT</div>

          <a routerLink="/kyc" routerLinkActive="active" class="nav-item">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
            </svg>
            <span class="nav-label">Conformité AML / KYC</span>
          </a>

          <a routerLink="/contract" routerLinkActive="active" class="nav-item">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
            <span class="nav-label">Analyse Contrats BCT</span>
          </a>

          <a routerLink="/credit" routerLinkActive="active" class="nav-item">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" />
            </svg>
            <span class="nav-label">Supervision Crédit</span>
          </a>
        </div>

        <!-- Section: Administration -->
        <div class="nav-group">
          <div class="nav-group-title">Administration & Outils</div>
          @if (auth.isAdmin()) {
            <a routerLink="/admin" routerLinkActive="active" class="nav-item nav-item-admin">
              <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span class="nav-label">Gestion Documentaire</span>
            </a>
          }
          <a href="/swagger" target="_blank" class="nav-item">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
            </svg>
            <span class="nav-label">Swagger API (OpenAPI)</span>
          </a>
        </div>
      </nav>

      <!-- 3. Sidebar Footer (Theme Toggle + User Profile + Logout) -->
      <div class="sidebar-footer">
        <!-- Theme Toggle -->
        <button 
          (click)="theme.toggleTheme()" 
          class="theme-toggle-btn"
          [title]="theme.isDark() ? 'Basculer en Mode Clair' : 'Basculer en Mode Sombre'"
        >
          @if (theme.isDark()) {
            <svg class="theme-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
            </svg>
            <span>Mode Clair</span>
          } @else {
            <svg class="theme-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
            </svg>
            <span>Mode Sombre</span>
          }
        </button>

        <!-- User Identity Block -->
        <div class="user-profile-row">
          <div class="user-avatar">
            {{ (auth.currentUser()?.username || 'U')[0].toUpperCase() }}
          </div>
          <div class="user-meta truncate">
            <span class="user-name truncate">{{ auth.currentUser()?.username }}</span>
            <span class="user-role-badge">{{ auth.userRole() || 'Conformité' }}</span>
          </div>
          <button (click)="auth.logout()" class="btn-logout" title="Déconnexion">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75" />
            </svg>
          </button>
        </div>
      </div>
    </aside>
  `,
  styles: [`
    .sidebar-wrapper {
      width: 260px;
      height: 100vh;
      background: var(--bg-sidebar);
      border-right: 1px solid var(--border-sidebar);
      display: flex;
      flex-direction: column;
      flex-shrink: 0;
      user-select: none;
      transition: background-color 0.25s ease, border-color 0.25s ease;
      z-index: 100;
    }

    /* 1. Header & Brand */
    .sidebar-brand {
      padding: 1.25rem 1.15rem;
      border-bottom: 1px solid var(--border-sidebar);
      display: flex;
      align-items: center;
      gap: 0.85rem;
      cursor: pointer;
      text-decoration: none;

      .brand-logo-container {
        width: 42px;
        height: 42px;
        border-radius: 10px;
        background: #ffffff;
        padding: 2px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
        border: 1px solid rgba(245, 158, 11, 0.3);
        flex-shrink: 0;
      }

      .attijari-logo-img {
        width: 100%;
        height: 100%;
        object-fit: contain;
      }

      .brand-text {
        display: flex;
        flex-direction: column;
      }

      .brand-title-row {
        display: flex;
        align-items: baseline;
        gap: 0.2rem;
      }

      .brand-attijari {
        font-size: 1.05rem;
        font-weight: 800;
        color: var(--text-primary);
        letter-spacing: -0.02em;
      }

      .brand-bank {
        font-size: 1.05rem;
        font-weight: 800;
        color: #f59e0b;
        letter-spacing: -0.02em;
      }

      .brand-ai-badge {
        font-size: 0.6rem;
        font-weight: 800;
        color: #111827;
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
        padding: 0.1rem 0.35rem;
        border-radius: 4px;
        margin-left: 0.25rem;
      }

      .brand-subtitle {
        font-size: 0.68rem;
        color: var(--text-muted);
        font-weight: 500;
      }
    }

    /* 2. Navigation List */
    .sidebar-nav {
      flex: 1;
      overflow-y: auto;
      padding: 1rem 0.75rem;
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }

    .nav-group {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }

    .nav-group-title {
      font-size: 0.68rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--text-muted);
      padding: 0 0.65rem 0.4rem 0.65rem;
    }

    .nav-item {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.6rem 0.75rem;
      border-radius: 8px;
      color: var(--text-secondary);
      text-decoration: none;
      font-size: 0.84rem;
      font-weight: 600;
      transition: all 0.15s ease;
      border-left: 3px solid transparent;

      .nav-icon {
        width: 1.15rem;
        height: 1.15rem;
        flex-shrink: 0;
        color: var(--text-muted);
        transition: color 0.15s ease;
      }

      &:hover {
        background: var(--bg-card-hover);
        color: var(--text-primary);

        .nav-icon {
          color: #f59e0b;
        }
      }

      &.active {
        background: rgba(245, 158, 11, 0.1);
        color: #f59e0b;
        border-left-color: #f59e0b;
        font-weight: 700;

        .nav-icon {
          color: #f59e0b;
        }
      }

      &.nav-item-admin.active {
        background: rgba(56, 189, 248, 0.1);
        color: #38bdf8;
        border-left-color: #38bdf8;

        .nav-icon {
          color: #38bdf8;
        }
      }
    }

    /* 3. Footer Drawer */
    .sidebar-footer {
      padding: 1rem 0.85rem;
      border-top: 1px solid var(--border-sidebar);
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      background: var(--bg-sidebar);
    }

    .theme-toggle-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      width: 100%;
      padding: 0.5rem;
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border-sidebar);
      color: var(--text-secondary);
      font-size: 0.78rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;

      .theme-icon {
        width: 1rem;
        height: 1rem;
        color: #f59e0b;
      }

      &:hover {
        background: rgba(245, 158, 11, 0.1);
        border-color: rgba(245, 158, 11, 0.3);
        color: var(--text-primary);
      }
    }

    .user-profile-row {
      display: flex;
      align-items: center;
      gap: 0.65rem;
      padding: 0.4rem 0.5rem;
      background: rgba(255, 255, 255, 0.03);
      border-radius: 8px;
      border: 1px solid var(--border-sidebar);
    }

    .user-avatar {
      width: 1.85rem;
      height: 1.85rem;
      border-radius: 6px;
      background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
      color: #111827;
      font-weight: 800;
      font-size: 0.8rem;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }

    .user-meta {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .user-name {
      font-size: 0.78rem;
      font-weight: 700;
      color: var(--text-primary);
    }

    .user-role-badge {
      font-size: 0.65rem;
      color: #f59e0b;
      font-weight: 600;
      text-transform: uppercase;
    }

    .btn-logout {
      background: transparent;
      border: none;
      color: var(--text-muted);
      cursor: pointer;
      padding: 0.3rem;
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s ease;

      svg {
        width: 1rem;
        height: 1rem;
      }

      &:hover {
        color: #ef4444;
        background: rgba(239, 68, 68, 0.1);
      }
    }

    .truncate {
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  `]
})
export class SidebarComponent {
  auth = inject(AuthService);
  theme = inject(ThemeService);
}
