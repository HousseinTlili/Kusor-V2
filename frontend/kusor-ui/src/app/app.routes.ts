import { Routes } from '@angular/router';
import { LoginComponent } from './pages/login/login.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { ChatComponent } from './pages/chat/chat.component';
import { DocumentsComponent } from './pages/admin/documents.component';
import { GraphComponent } from './pages/graph/graph.component';
import { CreditComponent } from './pages/credit/credit.component';
import { ContractComponent } from './pages/contract/contract.component';
import { KycComponent } from './pages/kyc/kyc.component';
import { ImpactViewerComponent } from './pages/impact-viewer/impact-viewer.component';
import { TemporalExplorerComponent } from './pages/temporal-explorer/temporal-explorer.component';
import { DiffViewerComponent } from './pages/diff-viewer/diff-viewer.component';
import { authGuard, adminGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { 
    path: '', 
    canActivate: [authGuard], 
    children: [
      { path: 'dashboard', component: DashboardComponent },
      { path: 'chat', component: ChatComponent },
      { path: 'admin', component: DocumentsComponent, canActivate: [adminGuard] },
      { path: 'graph', component: GraphComponent },
      { path: 'diff-viewer', component: DiffViewerComponent },
      { path: 'credit', component: CreditComponent },
      { path: 'contract', component: ContractComponent },
      { path: 'kyc', component: KycComponent },
      { path: 'impact-viewer', component: ImpactViewerComponent },
      { path: 'temporal-explorer', component: TemporalExplorerComponent },
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' }
    ] 
  },
  { path: '**', redirectTo: 'login' }
];

