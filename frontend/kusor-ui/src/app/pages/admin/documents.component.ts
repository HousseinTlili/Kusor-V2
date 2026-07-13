import { Component, OnInit, OnDestroy, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { Document } from '../../core/models/document.model';
import { LoadingSpinnerComponent } from '../../shared/components/loading-spinner/loading-spinner.component';
import { Subscription, interval } from 'rxjs';
import { startWith, switchMap } from 'rxjs/operators';

@Component({
  selector: 'app-documents',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, LoadingSpinnerComponent],
  templateUrl: './documents.component.html',
  styleUrl: './documents.component.scss'
})
export class DocumentsComponent implements OnInit, OnDestroy {
  private apiService = inject(ApiService);
  private fb = inject(FormBuilder);

  // Pagination and lists
  documents = signal<Document[]>([]);
  totalDocuments = signal<number>(0);
  currentPage = signal<number>(1);
  pageSize = 10;
  totalPages = signal<number>(1);

  // Loading and alerts
  isLoading = signal<boolean>(true);
  errorMessage = signal<string | null>(null);
  successMessage = signal<string | null>(null);

  // File Upload
  uploadForm: FormGroup = this.fb.group({
    file: [null, [Validators.required]],
    number: ['', [Validators.pattern(/^\d{4}-\d+$/)]], // e.g., 2024-01
    title: [''],
    category: ['Politique monétaire'],
    date: ['']
  });
  
  selectedFile: File | null = null;
  isUploading = signal<boolean>(false);
  isDragOver = signal<boolean>(false);

  // Polling for index status
  private pollingSub?: Subscription;

  ngOnInit(): void {
    this.loadDocuments();
    this.startStatusPolling();
  }

  ngOnDestroy(): void {
    if (this.pollingSub) {
      this.pollingSub.unsubscribe();
    }
  }

  loadDocuments(page: number = this.currentPage()): void {
    this.currentPage.set(page);
    this.isLoading.set(true);
    this.errorMessage.set(null);

    this.apiService.getDocuments(page, this.pageSize).subscribe({
      next: (res) => {
        this.documents.set(res.items);
        this.totalDocuments.set(res.total);
        this.totalPages.set(res.pages);
        this.isLoading.set(false);
      },
      error: (err) => {
        console.error('Error fetching documents', err);
        this.errorMessage.set('Impossible de charger les circulaires.');
        this.isLoading.set(false);
      }
    });
  }

  // File selection handlers
  onFileSelected(event: any): void {
    const file = event.target.files[0];
    if (file && file.type === 'application/pdf') {
      this.setFile(file);
    } else {
      this.errorMessage.set('Veuillez sélectionner un fichier PDF valide.');
    }
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.isDragOver.set(true);
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    this.isDragOver.set(false);
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.isDragOver.set(false);
    
    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.type === 'application/pdf') {
        this.setFile(file);
      } else {
        this.errorMessage.set('Veuillez déposer un fichier PDF uniquement.');
      }
    }
  }

  private setFile(file: File): void {
    this.selectedFile = file;
    this.uploadForm.patchValue({ file });
    this.uploadForm.get('file')?.updateValueAndValidity();
    
    // Try parsing circular number from filename, e.g. "circulaire-2024-01.pdf"
    const nameMatch = file.name.match(/(\d{4}-\d+)/);
    if (nameMatch) {
      this.uploadForm.patchValue({ number: nameMatch[1] });
    }
  }

  uploadDocument(): void {
    if (this.uploadForm.invalid || !this.selectedFile) return;

    this.isUploading.set(true);
    this.errorMessage.set(null);
    this.successMessage.set(null);

    const { number, title, category, date } = this.uploadForm.value;

    this.apiService.uploadDocument(
      this.selectedFile,
      number || undefined,
      title || undefined,
      category || undefined,
      date || undefined
    ).subscribe({
      next: (res) => {
        this.isUploading.set(false);
        this.successMessage.set(`Fichier "${this.selectedFile?.name}" téléversé avec succès. Indexation en cours...`);
        this.selectedFile = null;
        this.uploadForm.reset({ category: 'Politique monétaire' });
        this.loadDocuments();
      },
      error: (err) => {
        console.error('Error uploading file', err);
        this.isUploading.set(false);
        this.errorMessage.set(err.error?.message || 'Erreur lors du téléversement.');
      }
    });
  }

  deleteDocument(id: string): void {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette circulaire ? Cela effacera tous les fragments et liens du graphe associés.')) return;

    this.successMessage.set(null);
    this.errorMessage.set(null);

    this.apiService.deleteDocument(id).subscribe({
      next: (res) => {
        this.successMessage.set(`La circulaire a été supprimée.`);
        this.loadDocuments();
      },
      error: (err) => {
        console.error('Error deleting document', err);
        this.errorMessage.set('Erreur lors de la suppression de la circulaire.');
      }
    });
  }

  reindexDocument(id: string): void {
    this.successMessage.set(null);
    this.errorMessage.set(null);

    this.apiService.reindexDocument(id).subscribe({
      next: (res) => {
        this.successMessage.set('Indexation relancée avec succès.');
        this.loadDocuments();
      },
      error: (err) => {
        console.error('Error reindexing document', err);
        this.errorMessage.set('Erreur lors de la relance de l\'indexation.');
      }
    });
  }

  private startStatusPolling(): void {
    // Poll index state of active documents every 5 seconds
    this.pollingSub = interval(5000).pipe(
      startWith(0),
      switchMap(() => {
        const hasProcessing = this.documents().some(
          doc => doc.indexation_state === 'PENDING' || doc.indexation_state === 'PROCESSING'
        );
        if (hasProcessing) {
          return this.apiService.getDocuments(this.currentPage(), this.pageSize);
        }
        return [];
      })
    ).subscribe({
      next: (res: any) => {
        if (res && res.items) {
          this.documents.set(res.items);
          this.totalDocuments.set(res.total);
          this.totalPages.set(res.pages);
        }
      },
      error: (err) => console.error('Error polling document status', err)
    });
  }

  getStateBadgeClass(state: string): string {
    switch (state) {
      case 'INDEXED': return 'badge-success';
      case 'PROCESSING': return 'badge-warning';
      case 'PENDING': return 'badge-info';
      case 'FAILED': return 'badge-danger';
      default: return 'badge-secondary';
    }
  }

  getStateLabel(state: string): string {
    switch (state) {
      case 'INDEXED': return 'Indexé';
      case 'PROCESSING': return 'En cours';
      case 'PENDING': return 'En attente';
      case 'FAILED': return 'Échoué';
      default: return state;
    }
  }
}
