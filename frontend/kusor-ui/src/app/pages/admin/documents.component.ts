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
      <!-- Header Banner -->
      <div class="glass-card p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 relative overflow-hidden">
        <div class="absolute -right-20 -top-20 w-80 h-80 bg-[#E85D04]/10 rounded-full blur-3xl pointer-events-none"></div>

        <div>
          <h1 class="text-3xl font-black brand-gradient-text">Console Administration & Ingestion CRUD</h1>
          <p class="text-sm text-slate-400 mt-1">Gestion centralisée, filtrage multi-critères, édition et scraping automatisé</p>
        </div>

        <div class="flex items-center gap-3">
          <button (click)="openCreateModal()" class="px-5 py-3 rounded-xl bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-400 border border-emerald-500/40 text-xs font-bold transition-all flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
            </svg>
            <span>Nouveau Document</span>
          </button>

          <button (click)="triggerScrape()" [disabled]="scraping()" class="px-6 py-3 rounded-xl bg-gradient-to-r from-[#FAA307] via-[#E85D04] to-[#DC2F02] hover:from-[#E85D04] hover:to-[#9D0208] text-white font-bold text-xs transition-all shadow-xl shadow-[#E85D04]/30 disabled:opacity-50 flex items-center gap-2">
            @if (scraping()) {
              <svg class="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>Scraping...</span>
            } @else {
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
              </svg>
              <span>Scraping Multi-Sources</span>
            }
          </button>
        </div>
      </div>

      <!-- Sync Breakdown Panel -->
      @if (syncResult()) {
        <div class="glass-card p-6 border-l-4 border-emerald-500 bg-[#070A18] space-y-4">
          <div class="flex items-center justify-between">
            <h2 class="text-base font-black text-white flex items-center gap-2">
              <span class="inline-block w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
              Résultat de la Synchronisation
            </h2>
            <span class="text-xs font-black text-emerald-400">+{{ syncResult().totals?.total_added || 0 }} Éléments Ajoutés</span>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3">
            @for (src of syncResult().sources; track src.source_id) {
              <div class="p-3 rounded-xl bg-[#090D28] border border-slate-800 text-xs space-y-1">
                <div class="font-bold text-white truncate">{{ src.source_name }}</div>
                <div class="text-[10px] text-[#E85D04] font-semibold">{{ src.data_type }}</div>
                <div class="text-[10px] text-slate-400 pt-1 border-t border-slate-800">Scrapés: {{ src.items_scraped }} | Ajoutés: <strong class="text-emerald-400">+{{ src.items_added }}</strong></div>
              </div>
            }
          </div>
        </div>
      }

      <!-- Multi-Criteria Filters Bar -->
      <div class="glass-card p-6 bg-[#070A18] grid grid-cols-1 md:grid-cols-4 gap-4 items-center">
        <!-- Search Input -->
        <div>
          <label class="block text-[10px] font-black text-slate-400 uppercase tracking-wider mb-1">Recherche</label>
          <input [(ngModel)]="searchQuery" (ngModelChange)="applyFilters()" type="text" placeholder="Rechercher titre, N° circulaire..." class="w-full px-3 py-2 rounded-xl bg-[#090D28] border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-[#E85D04]">
        </div>

        <!-- Source Filter -->
        <div>
          <label class="block text-[10px] font-black text-slate-400 uppercase tracking-wider mb-1">Source</label>
          <select [(ngModel)]="selectedSource" (ngModelChange)="applyFilters()" class="w-full px-3 py-2 rounded-xl bg-[#090D28] border border-slate-800 text-xs text-white focus:outline-none focus:border-[#E85D04]">
            <option value="">Toutes les Sources</option>
            <option value="BCT Portal">BCT Portal</option>
            <option value="OFAC">OFAC SDN</option>
            <option value="EU Commission">Sanctions UE</option>
            <option value="UN Security Council">Sanctions ONU</option>
            <option value="GAFI / FATF">GAFI / FATF</option>
          </select>
        </div>

        <!-- Document Type Filter -->
        <div>
          <label class="block text-[10px] font-black text-slate-400 uppercase tracking-wider mb-1">Type de Document</label>
          <select [(ngModel)]="selectedType" (ngModelChange)="applyFilters()" class="w-full px-3 py-2 rounded-xl bg-[#090D28] border border-slate-800 text-xs text-white focus:outline-none focus:border-[#E85D04]">
            <option value="">Tous les Types</option>
            <option value="circular">Circulaire</option>
            <option value="sanction_list">Liste de Sanctions</option>
            <option value="guidance">Directive / Norme</option>
            <option value="note">Note d'Information</option>
            <option value="contract">Modèle de Contrat</option>
          </select>
        </div>

        <!-- Reset Button -->
        <div class="flex items-end h-full">
          <button (click)="resetFilters()" class="w-full py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold transition-all">
            Réinitialiser les Filtres
          </button>
        </div>
      </div>

      <!-- Document Table -->
      <div class="glass-card p-8 overflow-hidden">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-lg font-black text-white">Circulaires & Documents ({{ docs().length }})</h2>
          <span class="text-xs text-slate-400 font-medium">Affichage filtré en temps réel</span>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="bg-[#090D28] text-slate-400 uppercase border-b border-slate-800">
              <tr>
                <th class="p-4 font-black">Source</th>
                <th class="p-4 font-black">Référence / Titre</th>
                <th class="p-4 font-black">Type</th>
                <th class="p-4 font-black">Statut Indexation</th>
                <th class="p-4 font-black">Chunks</th>
                <th class="p-4 font-black">Date Ingestion</th>
                <th class="p-4 font-black text-right">Actions CRUD</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800/80">
              @for (doc of docs(); track doc.id) {
                <tr class="hover:bg-slate-900/40 transition-colors">
                  <td class="p-4 font-bold text-amber-400">{{ doc.source || 'BCT Portal' }}</td>
                  <td class="p-4 font-bold text-white">{{ doc.title }} <span class="text-slate-400 font-normal">(N° {{ doc.circular_reference || 'N/A' }})</span></td>
                  <td class="p-4 text-[#E85D04] uppercase font-bold">{{ doc.doc_type }}</td>
                  <td class="p-4">
                    <span class="px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 font-bold border border-emerald-500/30">
                      {{ doc.indexation_state }}
                    </span>
                  </td>
                  <td class="p-4 text-slate-400 font-semibold">{{ doc.chunk_count }}</td>
                  <td class="p-4 text-slate-500 font-medium">{{ doc.created_at?.slice(0, 10) }}</td>
                  <td class="p-4 text-right space-x-2">
                    <button (click)="openEditModal(doc)" class="px-3 py-1.5 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 font-semibold transition-all">
                      Éditer
                    </button>
                    <button (click)="deleteDoc(doc.id)" class="px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 font-semibold transition-all">
                      Supprimer
                    </button>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>

      <!-- Create Document Modal -->
      @if (showCreateModal()) {
        <div class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div class="glass-card p-8 max-w-lg w-full space-y-6 bg-[#070A18] border border-slate-800">
            <h3 class="text-xl font-black text-white">Ajouter un Nouveau Document</h3>

            <div class="space-y-4 text-xs">
              <div>
                <label class="block font-bold text-slate-400 mb-1">Titre du Document</label>
                <input [(ngModel)]="newDoc.title" type="text" placeholder="Ex: Circulaire BCT N° 2026-06" class="w-full px-3 py-2 rounded-xl bg-[#090D28] border border-slate-800 text-white focus:outline-none focus:border-[#E85D04]">
              </div>

              <div>
                <label class="block font-bold text-slate-400 mb-1">Référence Circulaire</label>
                <input [(ngModel)]="newDoc.circular_reference" type="text" placeholder="Ex: 2026-06" class="w-full px-3 py-2 rounded-xl bg-[#090D28] border border-slate-800 text-white focus:outline-none focus:border-[#E85D04]">
              </div>

              <div>
                <label class="block font-bold text-slate-400 mb-1">Source</label>
                <select [(ngModel)]="newDoc.source" class="w-full px-3 py-2 rounded-xl bg-[#090D28] border border-slate-800 text-white focus:outline-none focus:border-[#E85D04]">
                  <option value="BCT Portal">BCT Portal</option>
                  <option value="OFAC">OFAC SDN</option>
                  <option value="EU Commission">Sanctions UE</option>
                  <option value="UN Security Council">Sanctions ONU</option>
                  <option value="GAFI / FATF">GAFI / FATF</option>
                </select>
              </div>

              <div>
                <label class="block font-bold text-slate-400 mb-1">Type de Document</label>
                <select [(ngModel)]="newDoc.doc_type" class="w-full px-3 py-2 rounded-xl bg-[#090D28] border border-slate-800 text-white focus:outline-none focus:border-[#E85D04]">
                  <option value="circular">Circulaire</option>
                  <option value="sanction_list">Liste de Sanctions</option>
                  <option value="guidance">Directive / Norme</option>
                  <option value="note">Note d'Information</option>
                  <option value="contract">Modèle de Contrat</option>
                </select>
              </div>

              <div>
                <label class="block font-bold text-slate-400 mb-1">Fichier PDF / Document</label>
                <input (change)="onFileSelected($event)" type="file" class="w-full text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-[#E85D04]/20 file:text-[#E85D04]">
              </div>
            </div>

            <div class="flex justify-end gap-3 pt-4 border-t border-slate-800">
              <button (click)="closeModals()" class="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 font-bold text-xs">Annuler</button>
              <button (click)="saveNewDoc()" class="px-4 py-2 rounded-xl bg-[#E85D04] text-white font-bold text-xs">Téléverser et Indexer</button>
            </div>
          </div>
        </div>
      }

      <!-- Edit Document Modal -->
      @if (showEditModal()) {
        <div class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div class="glass-card p-8 max-w-lg w-full space-y-6 bg-[#070A18] border border-slate-800">
            <h3 class="text-xl font-black text-white">Éditer le Document</h3>

            <div class="space-y-4 text-xs">
              <div>
                <label class="block font-bold text-slate-400 mb-1">Titre</label>
                <input [(ngModel)]="editDoc.title" type="text" class="w-full px-3 py-2 rounded-xl bg-[#090D28] border border-slate-800 text-white focus:outline-none focus:border-[#E85D04]">
              </div>

              <div>
                <label class="block font-bold text-slate-400 mb-1">Référence Circulaire</label>
                <input [(ngModel)]="editDoc.circular_reference" type="text" class="w-full px-3 py-2 rounded-xl bg-[#090D28] border border-slate-800 text-white focus:outline-none focus:border-[#E85D04]">
              </div>

              <div>
                <label class="block font-bold text-slate-400 mb-1">Source</label>
                <select [(ngModel)]="editDoc.source" class="w-full px-3 py-2 rounded-xl bg-[#090D28] border border-slate-800 text-white focus:outline-none focus:border-[#E85D04]">
                  <option value="BCT Portal">BCT Portal</option>
                  <option value="OFAC">OFAC SDN</option>
                  <option value="EU Commission">Sanctions UE</option>
                  <option value="UN Security Council">Sanctions ONU</option>
                  <option value="GAFI / FATF">GAFI / FATF</option>
                </select>
              </div>

              <div>
                <label class="block font-bold text-slate-400 mb-1">Type de Document</label>
                <select [(ngModel)]="editDoc.doc_type" class="w-full px-3 py-2 rounded-xl bg-[#090D28] border border-slate-800 text-white focus:outline-none focus:border-[#E85D04]">
                  <option value="circular">Circulaire</option>
                  <option value="sanction_list">Liste de Sanctions</option>
                  <option value="guidance">Directive / Norme</option>
                  <option value="note">Note d'Information</option>
                  <option value="contract">Modèle de Contrat</option>
                </select>
              </div>
            </div>

            <div class="flex justify-end gap-3 pt-4 border-t border-slate-800">
              <button (click)="closeModals()" class="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 font-bold text-xs">Annuler</button>
              <button (click)="saveEditedDoc()" class="px-4 py-2 rounded-xl bg-[#E85D04] text-white font-bold text-xs">Enregistrer les Modifications</button>
            </div>
          </div>
        </div>
      }

    </div>
  `
})
export class DocumentsComponent implements OnInit {
  api = inject(ApiService);
  docs = signal<any[]>([]);
  scraping = signal(false);
  syncResult = signal<any>(null);

  // Filters
  searchQuery = '';
  selectedSource = '';
  selectedType = '';

  // Modals
  showCreateModal = signal(false);
  showEditModal = signal(false);

  newDoc: any = { title: '', circular_reference: '', source: 'BCT Portal', doc_type: 'circular' };
  selectedFile: File | null = null;
  editDoc: any = {};

  ngOnInit() {
    this.loadDocs();
  }

  loadDocs() {
    const filters: any = {};
    if (this.searchQuery) filters.search = this.searchQuery;
    if (this.selectedSource) filters.source = this.selectedSource;
    if (this.selectedType) filters.doc_type = this.selectedType;

    this.api.getDocuments(filters).subscribe({
      next: (res) => this.docs.set(res),
      error: (err) => console.error('Failed to load docs', err)
    });
  }

  applyFilters() {
    this.loadDocs();
  }

  resetFilters() {
    this.searchQuery = '';
    this.selectedSource = '';
    this.selectedType = '';
    this.loadDocs();
  }

  triggerScrape() {
    this.scraping.set(true);
    this.syncResult.set(null);
    this.api.triggerSync().subscribe({
      next: (res) => {
        this.scraping.set(false);
        this.syncResult.set(res);
        this.loadDocs();
      },
      error: () => this.scraping.set(false)
    });
  }

  openCreateModal() {
    this.newDoc = { title: '', circular_reference: '', source: 'BCT Portal', doc_type: 'circular' };
    this.selectedFile = null;
    this.showCreateModal.set(true);
  }

  onFileSelected(event: any) {
    if (event.target.files && event.target.files.length > 0) {
      this.selectedFile = event.target.files[0];
    }
  }

  saveNewDoc() {
    if (!this.selectedFile) {
      alert('Veuillez sélectionner un fichier PDF / document');
      return;
    }

    const formData = new FormData();
    formData.append('file', this.selectedFile);
    formData.append('title', this.newDoc.title || this.selectedFile.name);
    formData.append('doc_type', this.newDoc.doc_type);
    formData.append('source', this.newDoc.source);
    if (this.newDoc.circular_reference) {
      formData.append('circular_reference', this.newDoc.circular_reference);
    }

    this.api.uploadDocument(formData).subscribe({
      next: () => {
        this.closeModals();
        this.loadDocs();
      },
      error: (err) => console.error('Failed upload', err)
    });
  }

  openEditModal(doc: any) {
    this.editDoc = { ...doc };
    this.showEditModal.set(true);
  }

  saveEditedDoc() {
    this.api.updateDocument(this.editDoc.id, {
      title: this.editDoc.title,
      circular_reference: this.editDoc.circular_reference,
      source: this.editDoc.source,
      doc_type: this.editDoc.doc_type,
    }).subscribe({
      next: () => {
        this.closeModals();
        this.loadDocs();
      },
      error: (err) => console.error('Failed update', err)
    });
  }

  deleteDoc(id: string) {
    if (confirm('Êtes-vous sûr de vouloir supprimer ce document et tous ses nœuds graph ?')) {
      this.api.deleteDocument(id).subscribe({
        next: () => this.loadDocs()
      });
    }
  }

  closeModals() {
    this.showCreateModal.set(false);
    this.showEditModal.set(false);
  }
}
