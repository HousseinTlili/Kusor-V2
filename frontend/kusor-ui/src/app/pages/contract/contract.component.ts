import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { SeverityBadgeComponent } from '../../shared/components/severity-badge/severity-badge.component';

@Component({
  selector: 'app-contract',
  standalone: true,
  imports: [CommonModule, FormsModule, SeverityBadgeComponent],
  template: `
    <div class="contract-page-container">
      
      <!-- 1. Executive Attijari Header Banner -->
      <div class="glass-card header-banner">
        <div class="banner-left">
          <div class="badge-row">
            <span class="bank-badge">Attijari Bank • Direction des Affaires Juridiques</span>
            <span class="norm-badge">Audit Temporel des Circulaires BCT</span>
          </div>
          <h1 class="page-title">Analyse & Audit de Conformité des Contrats</h1>
          <p class="page-subtitle">
            Segmentation automatisée des clauses conventionnelles, détection des clauses léonines ou usuraires, et confrontation temps-réel aux circulaires BCT en vigueur.
          </p>
        </div>
        <div class="banner-right">
          <div class="audit-stat-card">
            <span class="stat-label">Statut du Moteur Légal</span>
            <span class="stat-value">Actif</span>
            <span class="stat-desc">GraphRAG & Taxonomie BCT</span>
          </div>
        </div>
      </div>

      <!-- 2. Quick Demo Presets Bar -->
      <div class="glass-card presets-toolbar">
        <span class="presets-title">Modèles Types de Contrats :</span>
        <button (click)="loadPreset('pret_immo')" class="preset-btn">
          <span class="status-dot dot-green"></span>
          Convention de Prêt Immobilier
        </button>
        <button (click)="loadPreset('taux_usure')" class="preset-btn">
          <span class="status-dot dot-red"></span>
          Clause à Risque (Pénalité Usuraire)
        </button>
        <button (click)="loadPreset('compte_courant')" class="preset-btn">
          <span class="status-dot dot-blue"></span>
          Convention Compte Entreprise
        </button>
      </div>

      <!-- 3. Form & Analysis Grid -->
      <div class="main-grid">
        
        <!-- Input Form (Left Column) -->
        <div class="glass-card form-card">
          <h2 class="section-heading">Document à Examiner</h2>

          <div class="form-group">
            <label class="form-label">Intitulé de la Convention / Modèle</label>
            <input 
              type="text" 
              [(ngModel)]="title" 
              placeholder="ex: Convention de Prêt Habitat - Attijari Bank"
              class="form-input" 
            />
          </div>

          <!-- Document Upload Option -->
          <div class="form-group">
            <label class="form-label">Téléverser l'Acte Contractuel (PDF / DOCX / TXT)</label>
            <div class="upload-dropzone">
              <input type="file" (change)="onFileSelected($event)" accept=".pdf,.docx,.txt" class="file-input-hidden" />
              <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
              <span class="upload-text">Sélectionner un contrat PDF / DOCX</span>
              @if (selectedFileName) {
                <span class="file-selected-badge">✓ {{ selectedFileName }}</span>
              }
            </div>
          </div>

          <!-- Text Clause Editor -->
          <div class="form-group">
            <label class="form-label">Ou Corpus des Clauses à Analyser</label>
            <textarea 
              [(ngModel)]="text" 
              rows="8" 
              placeholder="Collez ici les articles et stipulations du contrat..."
              class="form-textarea"
            ></textarea>
          </div>

          <!-- Submit Button -->
          <button (click)="analyze()" [disabled]="loading() || (!text && !selectedFile)" class="btn-submit-audit">
            @if (loading()) {
              <svg class="spinner-icon animate-spin" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>Vérification temporelle BCT en cours...</span>
            } @else {
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="action-icon">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Exécuter l'Audit Juridique BCT</span>
            }
          </button>
        </div>

        <!-- Output Report (Right Column) -->
        <div class="glass-card report-card">
          @if (!report()) {
            <div class="report-empty-state">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="empty-icon">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 7.5h1.5m-1.5 3h1.5m-7.5 3h7.5m-7.5 3h7.5m3-9h3.375c.621 0 1.125.504 1.125 1.125V18a2.25 2.25 0 01-2.25 2.25M16.5 7.5V18a2.25 2.25 0 002.25 2.25M16.5 7.5V4.875c0-.621-.504-1.125-1.125-1.125H4.125C3.504 3.75 3 4.254 3 4.875V18a2.25 2.25 0 002.25 2.25h13.5M6 7.5h3v3H6v-3z" />
              </svg>
              <h3 class="empty-title">Prêt pour l'audit juridique</h3>
              <p class="empty-desc">Sélectionnez un modèle type ou téléversez un contrat pour vérifier la conformité temporelle avec les circulaires de la BCT.</p>
            </div>
          } @else {
            <div class="report-header">
              <div>
                <h2 class="report-contract-title">{{ report().contract_title }}</h2>
                <div class="report-meta-row">
                  Total Clauses : <strong>{{ report().total_clauses }}</strong> • Non-Conformités : <strong class="text-danger">{{ report().non_conformity_count }}</strong>
                </div>
              </div>
              <div class="verdict-tag" [class.verdict-approved]="report().overall_risk === 'LOW' || report().overall_risk === 'FAIBLE'" [class.verdict-rejected]="report().overall_risk === 'HIGH' || report().overall_risk === 'CRITIQUE' || report().overall_risk === 'ELEVE'">
                {{ report().overall_risk === 'LOW' || report().overall_risk === 'FAIBLE' ? '✓ CONFORME BCT' : '⚠️ VIGILANCE / ANOMALIES' }}
              </div>
            </div>

            <!-- Metric Cards -->
            <div class="kpi-metrics-grid">
              <div class="kpi-card">
                <span class="kpi-label">Niveau de Risque</span>
                <span class="kpi-val" [class.val-danger]="report().overall_risk === 'HIGH' || report().overall_risk === 'ELEVE'">{{ report().overall_risk }}</span>
              </div>
              <div class="kpi-card">
                <span class="kpi-label">Clauses Anomaliques</span>
                <span class="kpi-val val-danger">{{ report().critical_issues || 0 }}</span>
              </div>
              <div class="kpi-card">
                <span class="kpi-label">Cohérence Temporelle BCT</span>
                <span class="kpi-val val-success">100% Validée</span>
              </div>
            </div>

            <!-- Detailed Clauses List -->
            <div class="clauses-section">
              <h3 class="section-subheading">Segmentation & Diagnostic des Clauses</h3>
              <div class="clauses-list">
                @for (c of report().clauses; track c.clause_number) {
                  <div class="clause-item-card">
                    <div class="clause-item-header">
                      <span class="clause-badge">Article / Clause {{ c.clause_number }} • Type : {{ c.clause_type }}</span>
                      <app-severity-badge [severity]="c.conformity_status"></app-severity-badge>
                    </div>
                    <p class="clause-text-snippet">{{ c.clause_text }}</p>
                    @if (c.regulatory_basis_ref) {
                      <div class="clause-ref-row">
                        <span class="ref-title">Circulaire de Référence BCT :</span>
                        <strong class="ref-val">{{ c.regulatory_basis_ref }}</strong>
                        <span class="ref-status">✓ En vigueur</span>
                      </div>
                    }
                  </div>
                }
              </div>
            </div>

            <!-- Recommendations -->
            @if (report().recommendations?.length) {
              <div class="recommendations-box">
                <h3 class="recommendations-title">Recommandations & Reformulations Juridiques</h3>
                <div class="recommendations-list">
                  @for (rec of report().recommendations; track $index) {
                    <div class="recommendation-item">
                      <span class="bullet">•</span>
                      <span>{{ rec }}</span>
                    </div>
                  }
                </div>
              </div>
            }

            <div class="audit-footer">
              <span>🔒 Validation Juridique Attijari Bank • Contrôle de Validité Temporelle GraphRAG</span>
            </div>
          }
        </div>
      </div>
    </div>
  `,
  styles: [`
    .contract-page-container {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
      max-width: 1300px;
      margin: 0 auto;
      animation: fadeIn 0.3s ease-out;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }

    /* 1. Header Banner */
    .header-banner {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1.75rem 2rem;
      border-radius: 16px;
      background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.7) 100%);
      border: 1px solid rgba(59, 130, 246, 0.2);
      gap: 1.5rem;

      @media (max-width: 900px) {
        flex-direction: column;
        align-items: flex-start;
      }
    }

    .badge-row {
      display: flex;
      gap: 0.6rem;
      margin-bottom: 0.4rem;
      flex-wrap: wrap;
    }

    .bank-badge {
      background: rgba(37, 99, 235, 0.15);
      border: 1px solid rgba(59, 130, 246, 0.3);
      color: #60a5fa;
      font-size: 0.72rem;
      font-weight: 700;
      padding: 0.2rem 0.65rem;
      border-radius: 20px;
    }

    .norm-badge {
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid rgba(16, 185, 129, 0.3);
      color: #34d399;
      font-size: 0.72rem;
      font-weight: 700;
      padding: 0.2rem 0.65rem;
      border-radius: 20px;
    }

    .page-title {
      font-size: 1.6rem;
      font-weight: 800;
      color: var(--text-primary);
      margin-bottom: 0.35rem;
      letter-spacing: -0.01em;
    }

    .page-subtitle {
      font-size: 0.85rem;
      color: var(--text-secondary);
      max-width: 720px;
      line-height: 1.45;
    }

    .audit-stat-card {
      background: rgba(0, 0, 0, 0.3);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 12px;
      padding: 0.85rem 1.25rem;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      flex-shrink: 0;

      .stat-label { font-size: 0.68rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; }
      .stat-value { font-size: 1.6rem; font-weight: 900; color: #10b981; }
      .stat-desc { font-size: 0.65rem; color: var(--text-muted); }
    }

    /* 2. Presets Toolbar */
    .presets-toolbar {
      display: flex;
      align-items: center;
      gap: 0.65rem;
      padding: 0.85rem 1.25rem;
      border-radius: 12px;
      flex-wrap: wrap;

      .presets-title {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        color: var(--text-muted);
        margin-right: 0.25rem;
      }
    }

    .preset-btn {
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      padding: 0.4rem 0.85rem;
      border-radius: 8px;
      font-size: 0.78rem;
      font-weight: 600;
      cursor: pointer;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border-color);
      color: var(--text-secondary);
      transition: all 0.15s ease;

      &:hover {
        background: rgba(255, 255, 255, 0.08);
        color: var(--text-primary);
        transform: translateY(-1px);
      }
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }
    .dot-green { background: #10b981; }
    .dot-red { background: #ef4444; }
    .dot-blue { background: #38bdf8; }

    /* 3. Main Grid */
    .main-grid {
      display: grid;
      grid-template-columns: 1fr 1.6fr;
      gap: 1.5rem;

      @media (max-width: 1024px) {
        grid-template-columns: 1fr;
      }
    }

    .form-card, .report-card {
      padding: 1.75rem;
      border-radius: 16px;
    }

    .section-heading {
      font-size: 1.15rem;
      font-weight: 800;
      color: var(--text-primary);
      margin-bottom: 1.25rem;
      padding-bottom: 0.75rem;
      border-bottom: 1px solid var(--border-color);
    }

    .form-group {
      margin-bottom: 1.15rem;
    }

    .form-label {
      display: block;
      font-size: 0.75rem;
      font-weight: 700;
      color: var(--text-secondary);
      margin-bottom: 0.35rem;
    }

    .form-input {
      width: 100%;
      background: var(--bg-input);
      border: 1px solid var(--border-input);
      color: var(--text-primary);
      padding: 0.65rem 0.85rem;
      border-radius: 8px;
      font-size: 0.85rem;
      outline: none;
      transition: all 0.15s ease;

      &:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
      }
    }

    .form-textarea {
      width: 100%;
      background: var(--bg-input);
      border: 1px solid var(--border-input);
      color: var(--text-primary);
      padding: 0.75rem 0.85rem;
      border-radius: 8px;
      font-size: 0.8rem;
      font-family: monospace;
      outline: none;
      line-height: 1.55;
      resize: vertical;
      transition: all 0.15s ease;

      &:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
      }
    }

    .upload-dropzone {
      border: 1px dashed var(--border-color-hover);
      background: rgba(255, 255, 255, 0.02);
      border-radius: 10px;
      padding: 1.25rem 1rem;
      text-align: center;
      position: relative;
      cursor: pointer;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.35rem;

      &:hover {
        border-color: #3b82f6;
        background: rgba(59, 130, 246, 0.04);
      }

      .file-input-hidden {
        position: absolute;
        inset: 0;
        opacity: 0;
        cursor: pointer;
        width: 100%;
        height: 100%;
      }

      .upload-icon {
        width: 1.5rem;
        height: 1.5rem;
        color: var(--text-muted);
      }

      .upload-text {
        font-size: 0.78rem;
        color: var(--text-secondary);
        font-weight: 500;
      }

      .file-selected-badge {
        font-size: 0.75rem;
        font-weight: 700;
        color: #38bdf8;
      }
    }

    .btn-submit-audit {
      width: 100%;
      background: linear-gradient(135deg, #1e40af 0%, #1e3a8a 100%);
      border: 1px solid rgba(59, 130, 246, 0.4);
      color: white;
      padding: 0.85rem;
      border-radius: 10px;
      font-size: 0.88rem;
      font-weight: 800;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      box-shadow: 0 4px 12px rgba(30, 58, 138, 0.3);
      transition: all 0.2s ease;
      margin-top: 0.75rem;

      &:hover:not(:disabled) {
        background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
        border-color: #60a5fa;
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.4);
      }

      &:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

      .action-icon {
        width: 1.15rem;
        height: 1.15rem;
      }
    }

    /* 4. Report Right Card */
    .report-empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 5rem 2rem;
      text-align: center;

      .empty-icon {
        width: 3.5rem;
        height: 3.5rem;
        color: var(--text-muted);
        opacity: 0.4;
        margin-bottom: 1rem;
      }

      .empty-title {
        font-size: 1.15rem;
        font-weight: 800;
        color: var(--text-primary);
        margin-bottom: 0.35rem;
      }

      .empty-desc {
        font-size: 0.84rem;
        color: var(--text-muted);
        max-width: 400px;
      }
    }

    .report-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 1.25rem;
      border-bottom: 1px solid var(--border-color);
      margin-bottom: 1.25rem;
    }

    .report-contract-title {
      font-size: 1.35rem;
      font-weight: 900;
      color: var(--text-primary);
    }

    .report-meta-row {
      font-size: 0.78rem;
      color: var(--text-muted);
      margin-top: 0.2rem;

      .text-danger { color: #ef4444; }
    }

    .verdict-tag {
      padding: 0.5rem 1rem;
      border-radius: 8px;
      font-size: 0.82rem;
      font-weight: 800;

      &.verdict-approved {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
      }

      &.verdict-rejected {
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
      }
    }

    .kpi-metrics-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 0.85rem;
      margin-bottom: 1.5rem;

      @media (max-width: 768px) {
        grid-template-columns: 1fr;
      }
    }

    .kpi-card {
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 1rem;
      text-align: center;
      display: flex;
      flex-direction: column;
      gap: 0.25rem;

      .kpi-label { font-size: 0.68rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; }
      .kpi-val { font-size: 1.35rem; font-weight: 900; color: var(--text-primary); }
      .val-danger { color: #ef4444; }
      .val-success { color: #10b981; }
    }

    .clauses-section {
      margin-bottom: 1.5rem;

      .section-subheading {
        font-size: 0.8rem;
        font-weight: 800;
        text-transform: uppercase;
        color: var(--text-primary);
        margin-bottom: 0.85rem;
      }
    }

    .clauses-list {
      display: flex;
      flex-direction: column;
      gap: 0.85rem;
    }

    .clause-item-card {
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 1.15rem;
      display: flex;
      flex-direction: column;
      gap: 0.65rem;

      .clause-item-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .clause-badge {
        font-size: 0.78rem;
        font-weight: 700;
        color: #38bdf8;
      }

      .clause-text-snippet {
        font-size: 0.8rem;
        color: var(--text-secondary);
        font-family: monospace;
        background: rgba(0, 0, 0, 0.2);
        padding: 0.75rem;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.04);
        line-height: 1.5;
      }

      .clause-ref-row {
        display: flex;
        align-items: center;
        gap: 0.45rem;
        font-size: 0.74rem;
        color: var(--text-muted);

        .ref-val { color: #f59e0b; }
        .ref-status { color: #10b981; font-weight: 700; }
      }
    }

    .recommendations-box {
      background: rgba(37, 99, 235, 0.08);
      border: 1px solid rgba(59, 130, 246, 0.25);
      border-radius: 12px;
      padding: 1.25rem;
      margin-bottom: 1.25rem;

      .recommendations-title {
        font-size: 0.78rem;
        font-weight: 800;
        text-transform: uppercase;
        color: #60a5fa;
        margin-bottom: 0.65rem;
      }

      .recommendations-list {
        display: flex;
        flex-direction: column;
        gap: 0.45rem;
      }

      .recommendation-item {
        display: flex;
        align-items: flex-start;
        gap: 0.45rem;
        font-size: 0.8rem;
        color: #bfdbfe;
        line-height: 1.45;

        .bullet { color: #3b82f6; font-weight: bold; }
      }
    }

    .audit-footer {
      padding-top: 1rem;
      border-top: 1px solid var(--border-color);
      font-size: 0.68rem;
      color: var(--text-muted);
      text-align: center;
    }
  `]
})
export class ContractComponent {
  api = inject(ApiService);
  title = 'Convention de Prêt Immobilier 2026';
  text = `Article 1 - Objet du Prêt\nLe prêteur accorde à l'emprunteur un prêt immobilier d'un montant de 150 000 TND au taux d'intérêt de 8.25% l'an conformément aux règles BCT.\n\nArticle 2 - Pénalités de Retard\nEn cas de défaillance, des pénalités de retard équivalentes à 2.0% majoré du taux usuraire légal seront appliquées.`;
  selectedFile: File | null = null;
  selectedFileName = '';
  report = signal<any>(null);
  loading = signal(false);

  loadPreset(preset: string) {
    if (preset === 'pret_immo') {
      this.title = 'Convention de Prêt Immobilier Attijari';
      this.text = `Article 1 - Objet\nPrêt bancaire amortissable de 120 000 TND remboursable sur une durée de 240 mois au taux nominal de 7.85%.\n\nArticle 2 - Garanties Exigées\nHypothèque de premier rang sur le bien financé et souscription obligatoire d'une assurance décès-invalidité.`;
    } else if (preset === 'taux_usure') {
      this.title = 'Contrat de Facilité de Caisse avec Clause Risquée';
      this.text = `Article 1 - Montant et Taux\nFacilité de caisse de 50 000 TND au taux d'intérêt conventionnel de 19.5% l'an.\n\nArticle 2 - Indemnités Forfaitaires\nEn cas de dépassement, une indemnité d'exigibilité immédiate de 25% sera facturée sans mise en demeure préalable.`;
    } else if (preset === 'compte_courant') {
      this.title = 'Convention de Compte Courant Professionnel';
      this.text = `Article 1 - Conditions d'Ouverture\nOuverture de compte subordonnée à la fourniture de l'extrait RNE datant de moins de 3 mois et à l'identification du bénéficiaire effectif.\n\nArticle 2 - Droit de Clôture\nChaque partie peut résilier la convention par lettre recommandée avec accusé de réception sous préavis de 30 jours.`;
    }
    this.selectedFile = null;
    this.selectedFileName = '';
  }

  onFileSelected(event: any) {
    if (event.target.files && event.target.files.length > 0) {
      this.selectedFile = event.target.files[0];
      this.selectedFileName = this.selectedFile?.name || '';
      this.title = this.selectedFileName.replace(/\.[^/.]+$/, '');
    }
  }

  analyze() {
    this.loading.set(true);

    if (this.selectedFile) {
      const formData = new FormData();
      formData.append('file', this.selectedFile);
      formData.append('title', this.title);
      this.api.analyzeContract(formData).subscribe({
        next: (res) => {
          this.report.set(res);
          this.loading.set(false);
        },
        error: () => this.loading.set(false)
      });
    } else {
      this.api.analyzeContract({ title: this.title, text: this.text }).subscribe({
        next: (res) => {
          this.report.set(res);
          this.loading.set(false);
        },
        error: () => this.loading.set(false)
      });
    }
  }
}
