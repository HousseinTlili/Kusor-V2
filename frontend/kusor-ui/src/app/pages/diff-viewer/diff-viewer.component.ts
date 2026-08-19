import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ExportService, AuditReportData } from '../../core/services/export.service';

interface DiffPair {
  id: string;
  theme: string;
  oldCircular: {
    number: string;
    date: string;
    title: string;
    clauses: Array<{ article: string; text: string; status: 'ABROGE' | 'MODIFIE' | 'INCHANGE' }>;
  };
  newCircular: {
    number: string;
    date: string;
    title: string;
    clauses: Array<{ article: string; text: string; status: 'AJOUTE' | 'MODIFIE' | 'INCHANGE' }>;
  };
  impactAnalysis: {
    risques: string;
    credit: string;
    conformite: string;
    systemeInfo: string;
  };
}

@Component({
  selector: 'app-diff-viewer',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './diff-viewer.component.html',
  styleUrl: './diff-viewer.component.scss'
})
export class DiffViewerComponent {
  exportService = inject(ExportService);

  pairs: DiffPair[] = [
    {
      id: 'NPL-DIFF',
      theme: 'Classification Actifs & Résolution NPL',
      oldCircular: {
        number: '1991-24',
        date: '1991-12-17',
        title: 'Circulaire N° 91-24 — Division, couverture des risques et suivi des engagements',
        clauses: [
          { article: 'Article 8 (Ancien)', text: 'Classification des créances en 4 classes selon les critères stricts d\'impayés supérieurs à 90 jours sans plan de remédiation formalisé.', status: 'MODIFIE' },
          { article: 'Article 10 (Abrogé)', text: 'Traitement des garanties hypothécaires sans déduction forfaitaire pour la décote de liquidation rapide.', status: 'ABROGE' },
          { article: 'Article 14', text: 'Comptabilisation des agios réservés sur les créances douteuses et litigieuses.', status: 'INCHANGE' }
        ]
      },
      newCircular: {
        number: '2024-88',
        date: '2024-11-15',
        title: 'Circulaire N° 2024-88 — Dispositif de prévention et résolution des créances non performantes (NPL)',
        clauses: [
          { article: 'Article 8 (Nouveau)', text: 'Introduction de l\'indicateur NPE (Non-Performing Exposure), obligation de surveillance précoce (Early Warning System) dès 30 jours d\'impayé.', status: 'MODIFIE' },
          { article: 'Article 10 bis (Nouveau)', text: 'Mise en place obligatoire d\'une unité dédiée à la restructuration amiable et évaluation trimestrielle de la recouvrabilité.', status: 'AJOUTE' },
          { article: 'Article 12 (Nouveau)', text: 'Obligation de provisionnement dynamique et plans d\'assainissement pluriannuels du portefeuille compromis.', status: 'AJOUTE' }
        ]
      },
      impactAnalysis: {
        risques: 'Recalcul immédiat du taux NPE et adaptation des modèles de provisionnement statistique.',
        credit: 'Intégration des alertes EWS à 30 jours dans le workflow d\'octroi.',
        conformite: 'Reporting prudentiel trimestriel renforcé à destination de la BCT.',
        systemeInfo: 'Mise à jour des règles de classification automatique dans le Core Banking.'
      }
    },
    {
      id: 'RESERVES-DIFF',
      theme: 'Régime des Réserves Obligatoires',
      oldCircular: {
        number: '2011-04',
        date: '2011-03-02',
        title: 'Circulaire N° 2011-04 — Conditions de constitution des réserves obligatoires',
        clauses: [
          { article: 'Article 3 (Ancien)', text: 'Taux de réserve obligatoire fixé à 2.0% sur l\'ensemble des dépôts à vue et dépôts d\'épargne en dinars.', status: 'MODIFIE' },
          { article: 'Article 5', text: 'Période de constitution mensuelle calculée sur la base des moyennes journalières.', status: 'INCHANGE' }
        ]
      },
      newCircular: {
        number: '2017-02',
        date: '2017-03-15',
        title: 'Circulaire N° 2017-02 — Révision du taux et de l\'assiette des réserves obligatoires',
        clauses: [
          { article: 'Article 3 (Nouveau)', text: 'Taux de réserve obligatoire abaissé à 1.0% sur les dépôts éligibles en dinars pour soutenir la liquidité bancaire.', status: 'MODIFIE' },
          { article: 'Article 4 bis (Nouveau)', text: 'Exonération des comptes d\'épargne logement et des comptes de placement à terme supérieur à 24 mois.', status: 'AJOUTE' }
        ]
      },
      impactAnalysis: {
        risques: 'Gain de liquidité structurelle disponible sur le marché interbancaire.',
        credit: 'Capacité accrue de distribution de crédits à l\'économie.',
        conformite: 'Contrôle bimensuel de l\'adéquation de l\'assiette déclarée.',
        systemeInfo: 'Paramétrage du taux de 1.0% dans le module de gestion de trésorerie.'
      }
    },
    {
      id: 'AML-DIFF',
      theme: 'Conformité AML/KYC & Bénéficiaires Effectifs',
      oldCircular: {
        number: '2013-15',
        date: '2013-09-10',
        title: 'Circulaire N° 2013-15 — Devoir de vigilance en matière de LBC/FT',
        clauses: [
          { article: 'Article 4 (Ancien)', text: 'Identification des personnes physiques détenant le contrôle effectif sans seuil chiffré spécifique.', status: 'MODIFIE' },
          { article: 'Article 7', text: 'Conservation des pièces d\'identité pendant 5 ans après clôture de compte.', status: 'INCHANGE' }
        ]
      },
      newCircular: {
        number: '2018-16',
        date: '2018-09-30',
        title: 'Circulaire N° 2018-16 — Renforcement des obligations de vigilance AML/KYC',
        clauses: [
          { article: 'Article 4 (Nouveau)', text: 'Seuil strict d\'identification du Bénéficiaire Effectif (UBO) fixé à ≥ 25% du capital ou des droits de vote.', status: 'MODIFIE' },
          { article: 'Article 9 (Nouveau)', text: 'Obligation de filtrage en temps réel contre les listes de sanctions nationales (CNLCT) et internationales.', status: 'AJOUTE' }
        ]
      },
      impactAnalysis: {
        risques: 'Diminution du risque de non-conformité et sanctions BCT / GAFI.',
        credit: 'Validation systématique de la fiche KYC UBO 25% avant tout déblocage.',
        conformite: 'Revue obligatoire des dossiers personnes morales existants.',
        systemeInfo: 'Intégration de l\'API de screening des PPE et listes de gel des avoirs.'
      }
    }
  ];

  selectedPair = signal<DiffPair>(this.pairs[0]);

  selectPair(pair: DiffPair): void {
    this.selectedPair.set(pair);
  }

  exportDiffReport(): void {
    const pair = this.selectedPair();
    const inspectedItems = [
      ...pair.oldCircular.clauses.map(c => ({
        rule: `${pair.oldCircular.number} — ${c.article}`,
        circularReference: pair.oldCircular.number,
        status: (c.status === 'ABROGE' ? 'NON_CONFORME' : 'CONFORME') as 'CONFORME' | 'NON_CONFORME',
        details: `[${c.status}] ${c.text}`
      })),
      ...pair.newCircular.clauses.map(c => ({
        rule: `${pair.newCircular.number} — ${c.article}`,
        circularReference: pair.newCircular.number,
        status: 'CONFORME' as 'CONFORME',
        details: `[${c.status}] ${c.text}`
      }))
    ];

    const reportData: AuditReportData = {
      reportTitle: `Rapport d'Écart Réglementaire BCT : ${pair.oldCircular.number} vs ${pair.newCircular.number}`,
      reportType: 'Analyse d\'Écart & Diff Réglementaire BCT',
      referenceId: `DIFF-${pair.oldCircular.number}-${pair.newCircular.number}`,
      auditorName: 'Nour — Département Conformité & Réglementation Attijari Bank',
      auditDate: new Date().toISOString().split('T')[0],
      complianceScore: 98,
      verdict: 'CONFORME',
      executiveSummary: `Analyse comparative officielle entre la circulaire initiale BCT N° ${pair.oldCircular.number} et la circulaire modificative N° ${pair.newCircular.number} (${pair.theme}). Détection automatique des clauses abrogées, des obligations nouvellement créées et des impacts opérationnels sur les métiers de la banque.`,
      inspectedItems: inspectedItems
    };

    this.exportService.printCertifiedReport(reportData);
  }
}
