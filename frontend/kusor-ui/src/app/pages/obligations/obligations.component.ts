import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { ExportService, AuditReportData } from '../../core/services/export.service';

interface DeonticObligation {
  id: string;
  circular_number: string;
  circular_title: string;
  article: string;
  deontic_type: 'PROHIBITION' | 'REQUIREMENT' | 'THRESHOLD' | 'DEADLINE' | 'EXEMPTION' | 'SANCTION';
  actor: string;
  process: string;
  text: string;
  severity: string;
  sanction_risk: string;
}

@Component({
  selector: 'app-obligations',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './obligations.component.html',
  styleUrl: './obligations.component.scss'
})
export class ObligationsComponent implements OnInit {
  api = inject(ApiService);
  exportService = inject(ExportService);
  router = inject(Router);

  obligations = signal<DeonticObligation[]>([]);
  counts = signal<any>({ total: 0, prohibitions: 0, requirements: 0, thresholds: 0, deadlines: 0, exemptions: 0 });
  loading = signal(false);

  selectedType: string = 'ALL';
  searchQuery: string = '';

  filteredObligations = computed(() => {
    let list = this.obligations();

    if (this.selectedType !== 'ALL') {
      list = list.filter(o => o.deontic_type === this.selectedType);
    }

    const q = this.searchQuery.trim().toLowerCase();
    if (q) {
      list = list.filter(o =>
        o.circular_number.toLowerCase().includes(q) ||
        o.circular_title.toLowerCase().includes(q) ||
        o.article.toLowerCase().includes(q) ||
        o.actor.toLowerCase().includes(q) ||
        o.process.toLowerCase().includes(q) ||
        o.text.toLowerCase().includes(q)
      );
    }

    return list;
  });

  ngOnInit(): void {
    this.loadObligations();
  }

  loadObligations(): void {
    this.loading.set(true);
    this.api.getObligations(undefined, this.selectedType).subscribe({
      next: (res) => {
        this.obligations.set(res.obligations || []);
        this.counts.set(res.counts || {});
        this.loading.set(false);
      },
      error: () => this.loading.set(false)
    });
  }

  setTypeFilter(type: string): void {
    this.selectedType = type;
  }

  askInChat(obligation: DeonticObligation): void {
    this.router.navigate(['/chat'], {
      queryParams: { q: `Explique l'exigence ${obligation.article} de la circulaire BCT ${obligation.circular_number} concernant : ${obligation.text}` }
    });
  }

  viewInGraph(circularNumber: string): void {
    this.router.navigate(['/graph'], { queryParams: { circular: circularNumber } });
  }

  exportDeonticReport(): void {
    const list = this.filteredObligations();
    const inspectedItems = list.map(o => ({
      rule: `${o.circular_number} — ${o.article} (${o.deontic_type})`,
      circularReference: `Circulaire BCT N° ${o.circular_number}`,
      status: 'CONFORME' as 'CONFORME',
      details: `[Acteur : ${o.actor}] ${o.text} (Risque : ${o.sanction_risk})`
    }));

    const reportData: AuditReportData = {
      reportTitle: `Référentiel des Exigences Déontiques & Obligations BCT`,
      reportType: `Matrice Déontique de Conformité Bancaire (${this.selectedType})`,
      referenceId: `OBL-DEONTIC-${new Date().getFullYear()}`,
      auditorName: 'Nour — Département Conformité & Veille Réglementaire Attijari Bank',
      auditDate: new Date().toISOString().split('T')[0],
      complianceScore: 100,
      verdict: 'CONFORME',
      executiveSummary: `Cartographie certifiée des obligations réglementaires extraites des circulaires de la Banque Centrale de Tunisie. Répertoire complet des interdictions strictes, seuils prudentiels obligatoires, échéances légales et dérogations applicables aux opérations d'Attijari Bank Tunisia.`,
      inspectedItems: inspectedItems
    };

    this.exportService.printCertifiedReport(reportData);
  }
}
