import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../core/services/api.service';

interface TemporalRecord {
  id: string;
  circular_number: string;
  reference: string;
  title: string;
  category: string;
  date_issued: string;
  status_at_date: string;
  status_badge: string;
  current_status: string;
  summary: string;
  relations: Array<{ type: string; target: string; desc: string }>;
}

interface TimelineEvent {
  date: string;
  year: string;
  circular: string;
  title: string;
  category: string;
  status: string;
}

interface SampleAuditDossier {
  id: string;
  title: string;
  type: string;
  signatureDate: string;
  description: string;
  expectedApplicable: string[];
  expectedInapplicable: string[];
}

@Component({
  selector: 'app-temporal-explorer',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './temporal-explorer.component.html',
  styleUrl: './temporal-explorer.component.scss'
})
export class TemporalExplorerComponent implements OnInit {
  api = inject(ApiService);
  router = inject(Router);

  asOfDate = '2024-02-10';
  selectedFilter: 'ALL' | 'EN_VIGUEUR' | 'NON_PUBLIEE' = 'ALL';
  searchQuery = '';

  records = signal<TemporalRecord[]>([]);
  timelineEvents = signal<TimelineEvent[]>([]);
  loading = signal(false);

  presets = [
    { label: 'Aujourd\'hui (2026)', date: '2026-08-19', icon: '🟢' },
    { label: 'Régime NPL (2024)', date: '2024-11-20', icon: '📑' },
    { label: 'Gouvernance & AML (2018)', date: '2018-10-01', icon: '🛡️' },
    { label: 'Réserves Obligatoires (2017)', date: '2017-04-01', icon: '💰' },
    { label: 'Plafond DSTI 40% (2016)', date: '2016-02-01', icon: '💳' },
  ];

  // Point-in-time test dossiers
  sampleDossiers: SampleAuditDossier[] = [
    {
      id: 'DOS-2017-CR',
      title: 'Crédit Consommation Particulier 45 kDT',
      type: 'Crédit Particuliers',
      signatureDate: '2017-06-15',
      description: 'Dossier de prêt personnel instruit en juin 2017 avec mensualité de 650 TND.',
      expectedApplicable: ['2016-01 (DSTI ≤ 40%)', '2017-02 (Réserves Obligatoires)'],
      expectedInapplicable: ['2024-88 (NPL - Non encore publiée)', '2018-16 (AML/KYC UBO 25%)']
    },
    {
      id: 'DOS-2018-CORP',
      title: 'Convention d\'Ouverture de Compte Société SARL',
      type: 'AML / KYC',
      signatureDate: '2018-11-05',
      description: 'Ouverture de compte commercial avec identification des actionnaires détenant > 25%.',
      expectedApplicable: ['2018-16 (AML/KYC Beneficiaires Effectifs)', '2018-09 (Gouvernance)', '2016-01'],
      expectedInapplicable: ['2024-88 (NPL 2024)']
    },
    {
      id: 'DOS-2024-NPL',
      title: 'Dossier de Recouvrement Créance Impayée Classe 4',
      type: 'Contentieux & Risques',
      signatureDate: '2024-12-01',
      description: 'Dossier compromis avec provisionnement intégral suite à 180 jours de retard.',
      expectedApplicable: ['2024-88 (Prévention & Résolution NPL)', '2018-09', '2016-01'],
      expectedInapplicable: []
    }
  ];

  selectedDossier = signal<SampleAuditDossier | null>(this.sampleDossiers[0]);

  activeCount = computed(() => this.records().filter(r => r.status_at_date === 'EN_VIGUEUR').length);
  futureCount = computed(() => this.records().filter(r => r.status_at_date === 'NON_PUBLIEE').length);

  filteredRecords = computed(() => {
    let list = this.records();
    
    // Status filter
    if (this.selectedFilter === 'EN_VIGUEUR') {
      list = list.filter(r => r.status_at_date === 'EN_VIGUEUR');
    } else if (this.selectedFilter === 'NON_PUBLIEE') {
      list = list.filter(r => r.status_at_date === 'NON_PUBLIEE');
    }

    // Text search query
    const q = this.searchQuery.trim().toLowerCase();
    if (q) {
      list = list.filter(r => 
        r.circular_number.toLowerCase().includes(q) ||
        r.title.toLowerCase().includes(q) ||
        r.category.toLowerCase().includes(q) ||
        r.summary.toLowerCase().includes(q)
      );
    }
    return list;
  });

  ngOnInit(): void {
    this.loadTemporalGraph();
  }

  selectPreset(date: string): void {
    this.asOfDate = date;
    this.loadTemporalGraph();
  }

  selectDossier(dossier: SampleAuditDossier): void {
    this.selectedDossier.set(dossier);
    this.asOfDate = dossier.signatureDate;
    this.loadTemporalGraph();
  }

  loadTemporalGraph(): void {
    this.loading.set(true);
    this.api.getTemporalGraph(this.asOfDate).subscribe({
      next: (res) => {
        this.records.set(res.records || []);
        this.timelineEvents.set(res.timeline_events || []);
        this.loading.set(false);
      },
      error: () => this.loading.set(false)
    });
  }

  askInChat(circularNumber: string): void {
    this.router.navigate(['/chat'], { queryParams: { q: `Que dit la circulaire BCT ${circularNumber} et quelles sont ses obligations principales ?` } });
  }

  viewInGraph(circularNumber: string): void {
    this.router.navigate(['/graph'], { queryParams: { circular: circularNumber } });
  }
}
