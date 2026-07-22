import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-admin-documents',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="max-w-7xl mx-auto p-6 space-y-6">
      <div class="glass-card p-6 flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold gold-gradient-text">Console Administration & Ingestion</h1>
          <p class="text-sm text-slate-400 mt-1">Gestion des circulaires, ré-indexation et déclenchement du scraping BCT</p>
        </div>
        <button (click)="triggerScrape()" [disabled]="scraping()" class="px-5 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-sm transition-all shadow-lg shadow-amber-500/20 disabled:opacity-50">
          {{ scraping() ? 'Scraping BCT...' : 'Lancer Scraping BCT' }}
        </button>
      </div>

      <div class="glass-card p-6 overflow-hidden">
        <h2 class="text-lg font-bold text-slate-200 mb-4">Circulaires Indexées dans le Système</h2>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="bg-slate-900/80 text-slate-400 uppercase border-b border-slate-800">
              <tr>
                <th class="p-3">Référence / Titre</th>
                <th class="p-3">Type</th>
                <th class="p-3">Statut Indexation</th>
                <th class="p-3">Chunks</th>
                <th class="p-3">Date Ingestion</th>
                <th class="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800">
              @for (doc of docs(); track doc.id) {
                <tr class="hover:bg-slate-900/40 transition-colors">
                  <td class="p-3 font-semibold text-slate-200">{{ doc.title }} (N° {{ doc.circular_reference }})</td>
                  <td class="p-3 text-amber-400 uppercase">{{ doc.doc_type }}</td>
                  <td class="p-3">
                    <span class="px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-400 font-bold border border-emerald-500/30">
                      {{ doc.indexation_state }}
                    </span>
                  </td>
                  <td class="p-3 text-slate-400">{{ doc.chunk_count }}</td>
                  <td class="p-3 text-slate-500">{{ doc.created_at?.slice(0, 10) }}</td>
                  <td class="p-3 text-right">
                    <button (click)="deleteDoc(doc.id)" class="px-3 py-1 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 transition-all">
                      Supprimer
                    </button>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `
})
export class DocumentsComponent implements OnInit {
  api = inject(ApiService);
  docs = signal<any[]>([]);
  scraping = signal(false);

  ngOnInit() {
    this.loadDocs();
  }

  loadDocs() {
    this.api.getDocuments().subscribe({
      next: (res) => this.docs.set(res),
      error: (err) => console.error('Failed to load docs', err)
    });
  }

  deleteDoc(id: string) {
    if (confirm('Êtes-vous sûr de vouloir supprimer ce document et tous ses nœuds graph ?')) {
      this.api.deleteDocument(id).subscribe({
        next: () => this.loadDocs()
      });
    }
  }

  triggerScrape() {
    this.scraping.set(true);
    this.api.triggerSync().subscribe({
      next: () => {
        this.scraping.set(false);
        this.loadDocs();
      },
      error: () => this.scraping.set(false)
    });
  }
}
