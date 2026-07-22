import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-admin-documents',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="p-8 max-w-7xl mx-auto space-y-8">
      <div class="glass-card p-8 flex items-center justify-between gap-6 relative overflow-hidden">
        <div class="absolute -right-20 -top-20 w-80 h-80 bg-[#E85D04]/10 rounded-full blur-3xl pointer-events-none"></div>

        <div>
          <h1 class="text-3xl font-black brand-gradient-text">Console Administration & Ingestion</h1>
          <p class="text-sm text-slate-400 mt-1">Gestion des circulaires, ré-indexation et déclenchement du scraping BCT</p>
        </div>

        <button (click)="triggerScrape()" [disabled]="scraping()" class="px-6 py-3.5 rounded-xl bg-gradient-to-r from-[#FAA307] via-[#E85D04] to-[#DC2F02] hover:from-[#E85D04] hover:to-[#9D0208] text-white font-bold text-sm transition-all shadow-xl shadow-[#E85D04]/30 disabled:opacity-50">
          {{ scraping() ? 'Scraping BCT en cours...' : 'Lancer Scraping BCT' }}
        </button>
      </div>

      <div class="glass-card p-8 overflow-hidden">
        <h2 class="text-lg font-black text-white mb-6">Circulaires Indexées dans le Système</h2>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="bg-[#090D28] text-slate-400 uppercase border-b border-slate-800">
              <tr>
                <th class="p-4 font-black">Référence / Titre</th>
                <th class="p-4 font-black">Type</th>
                <th class="p-4 font-black">Statut Indexation</th>
                <th class="p-4 font-black">Chunks</th>
                <th class="p-4 font-black">Date Ingestion</th>
                <th class="p-4 font-black text-right">Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800/80">
              @for (doc of docs(); track doc.id) {
                <tr class="hover:bg-slate-900/40 transition-colors">
                  <td class="p-4 font-bold text-white">{{ doc.title }} (N° {{ doc.circular_reference }})</td>
                  <td class="p-4 text-[#E85D04] uppercase font-bold">{{ doc.doc_type }}</td>
                  <td class="p-4">
                    <span class="px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 font-bold border border-emerald-500/30">
                      {{ doc.indexation_state }}
                    </span>
                  </td>
                  <td class="p-4 text-slate-400 font-semibold">{{ doc.chunk_count }}</td>
                  <td class="p-4 text-slate-500 font-medium">{{ doc.created_at?.slice(0, 10) }}</td>
                  <td class="p-4 text-right">
                    <button (click)="deleteDoc(doc.id)" class="px-3.5 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 transition-all font-semibold">
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
