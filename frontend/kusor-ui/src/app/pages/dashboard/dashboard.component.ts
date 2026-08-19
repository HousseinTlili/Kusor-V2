import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { AdminStats } from '../../core/models/admin.model';
import { LoadingSpinnerComponent } from '../../shared/components/loading-spinner/loading-spinner.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, LoadingSpinnerComponent],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent implements OnInit {
  private apiService = inject(ApiService);
  private router = inject(Router);

  stats = signal<AdminStats | null>(null);
  summaryData = signal<any>(null);
  isLoading = signal<boolean>(true);
  isSyncing = signal<boolean>(false);
  syncMessage = signal<string | null>(null);
  syncError = signal<string | null>(null);

  ngOnInit(): void {
    this.loadStats();
    this.loadSummary();
  }

  loadStats(): void {
    this.isLoading.set(true);
    this.apiService.getStats().subscribe({
      next: (data) => {
        this.stats.set(data);
        this.isLoading.set(false);
      },
      error: (err) => {
        console.error('Error fetching dashboard stats', err);
        this.isLoading.set(false);
      }
    });
  }

  loadSummary(): void {
    this.apiService.getSummary().subscribe({
      next: (data) => {
        this.summaryData.set(data);
      },
      error: (err) => {
        console.error('Error fetching summary data', err);
      }
    });
  }

  navigateTo(path: string, queryParams?: any): void {
    this.router.navigate([path], { queryParams });
  }

  triggerManualSync(): void {
    this.isSyncing.set(true);
    this.syncMessage.set(null);
    this.syncError.set(null);

    this.apiService.triggerSync().subscribe({
      next: (res) => {
        this.isSyncing.set(false);
        if (res.new_count !== undefined) {
          this.syncMessage.set(
            `Synchronisation réussie. ${res.new_count || 0} nouvelles circulaires importées.`
          );
          this.loadStats();
        } else {
          this.syncMessage.set('La synchronisation a démarré en arrière-plan.');
        }
      },
      error: (err) => {
        console.error('Error syncing circulars', err);
        this.isSyncing.set(false);
        this.syncError.set(
          err.error?.message || 'Échec de la synchronisation. Veuillez réessayer.'
        );
      }
    });
  }

  formatDate(dateStr?: string): string {
    if (!dateStr) return 'Jamais';
    try {
      const date = new Date(dateStr);
      return date.toLocaleString('fr-FR', {
        dateStyle: 'short',
        timeStyle: 'short'
      });
    } catch {
      return dateStr;
    }
  }
}
