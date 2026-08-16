import { Routes } from '@angular/router';
import { authGuard, roleGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./pages/login/login.component').then(m => m.LoginComponent)
  },
  {
    path: 'dashboard',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/dashboard/dashboard.component').then(m => m.DashboardComponent)
  },
  {
    path: 'chat',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/chat/chat.component').then(m => m.ChatComponent)
  },
  {
    path: 'graph',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/graph/graph.component').then(m => m.GraphComponent)
  },
  {
    path: 'temporal-explorer',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/temporal-explorer/temporal-explorer.component').then(m => m.TemporalExplorerComponent)
  },
  {
    path: 'kyc',
    canActivate: [authGuard, roleGuard(['compliance'])],
    loadComponent: () => import('./pages/kyc/kyc.component').then(m => m.KycComponent)
  },
  {
    path: 'contract',
    canActivate: [authGuard, roleGuard(['legal'])],
    loadComponent: () => import('./pages/contract/contract.component').then(m => m.ContractComponent)
  },
  {
    path: 'credit',
    canActivate: [authGuard, roleGuard(['credit'])],
    loadComponent: () => import('./pages/credit/credit.component').then(m => m.CreditComponent)
  },
  {
    path: 'impact-viewer',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/impact-viewer/impact-viewer.component').then(m => m.ImpactViewerComponent)
  },
  {
    path: 'impact-viewer/:circularId',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/impact-viewer/impact-viewer.component').then(m => m.ImpactViewerComponent)
  },
  {
    path: 'admin/documents',
    canActivate: [authGuard, roleGuard(['admin'])],
    loadComponent: () => import('./pages/admin/documents.component').then(m => m.DocumentsComponent)
  },
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  { path: '**', redirectTo: 'dashboard' }
];
