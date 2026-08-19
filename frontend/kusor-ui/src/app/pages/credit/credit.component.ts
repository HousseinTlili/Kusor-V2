import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { SeverityBadgeComponent } from '../../shared/components/severity-badge/severity-badge.component';

@Component({
  selector: 'app-credit',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="credit-page-container">
      
      <!-- 1. Executive Attijari Header Banner -->
      <div class="glass-card header-banner">
        <div class="banner-left">
          <div class="badge-row">
            <span class="bank-badge">Attijari Bank • Direction Centrale des Engagements</span>
            <span class="norm-badge">Norme BCT n° 2016-01 (Ratio ≤ 40%)</span>
          </div>
          <h1 class="page-title">Supervision & Pré-filtrage des Risques de Crédit</h1>
          <p class="page-subtitle">
            Système multi-agent d'évaluation automatisée de la solvabilité, du taux d'effort mensuel et de la conformité réglementaire des demandes de financement.
          </p>
        </div>
        <div class="banner-right">
          <div class="bct-limit-card">
            <span class="limit-label">Seuil Réglementaire BCT</span>
            <span class="limit-value">40.0%</span>
            <span class="limit-desc">Capacité maximale d'endettement</span>
          </div>
        </div>
      </div>

      <!-- 2. Quick Demo Presets Bar -->
      <div class="glass-card presets-toolbar">
        <span class="presets-title">Cas Types d'Emprunteurs :</span>
        <button (click)="loadPreset('approve')" class="preset-btn btn-eligible">
          <span class="status-dot dot-green"></span>
          Dossier Éligible (Endettement 22.5%)
        </button>
        <button (click)="loadPreset('reject_debt')" class="preset-btn btn-rejected">
          <span class="status-dot dot-red"></span>
          Sur-Endettement (52.5% > 40% BCT)
        </button>
        <button (click)="loadPreset('missing_docs')" class="preset-btn btn-incomplete">
          <span class="status-dot dot-amber"></span>
          Dossier Incomplet (Pièces Manquantes)
        </button>
        <button (click)="loadPreset('corporate')" class="preset-btn btn-corporate">
          <span class="status-dot dot-blue"></span>
          Financement Entreprise / PME
        </button>
      </div>

      <!-- 3. Form & Analysis Grid -->
      <div class="main-grid">
        
        <!-- Input Form (Left Column) -->
        <div class="glass-card form-card">
          <h2 class="section-heading">Paramètres de la Demande</h2>
          
          <div class="form-group">
            <label class="form-label">Nom ou Raison Sociale de l'Emprunteur</label>
            <input 
              type="text" 
              [(ngModel)]="applicantName" 
              placeholder="ex: Société Maghrebienne d'Industrie ou Ahmed Ben Ali"
              class="form-input" 
            />
          </div>

          <div class="form-group">
            <label class="form-label">Type de Financement Demandé</label>
            <select [(ngModel)]="loanType" class="form-select">
              <option value="personal">Prêt Personnel / Consommation (Particulier)</option>
              <option value="mortgage">Prêt Immobilier & Habitat (Particulier)</option>
              <option value="corporate">Financement d'Investissement & Exploitation (PME)</option>
            </select>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Revenu Net Mensuel (TND)</label>
              <input type="number" [(ngModel)]="income" class="form-input" />
            </div>

            <div class="form-group">
              <label class="form-label">Engagements Existants (TND)</label>
              <input type="number" [(ngModel)]="monthlyDebt" class="form-input" />
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Mensualité du Nouveau Prêt (TND)</label>
            <input type="number" [(ngModel)]="loanAnnuity" class="form-input" />
          </div>

          <!-- Document Upload Dropzone -->
          <div class="form-group">
            <label class="form-label">Justificatifs Financiers & Relevés</label>
            <div class="upload-dropzone">
              <input type="file" multiple (change)="onFilesSelected($event)" class="file-input-hidden" />
              <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z" />
              </svg>
              <span class="upload-text">Glisser les pièces justificatives ou cliquer pour parcourir</span>
            </div>
            @if (uploadedFiles.length > 0) {
              <div class="file-chips-container">
                @for (file of uploadedFiles; track $index) {
                  <span class="file-chip">
                    📄 {{ file }}
                  </span>
                }
              </div>
            }
          </div>

          <!-- Submit Button -->
          <button (click)="prescreen()" [disabled]="loading() || !applicantName" class="btn-submit-audit">
            @if (loading()) {
              <svg class="spinner-icon animate-spin" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>Évaluation multi-agent en cours...</span>
            } @else {
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="action-icon">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Lancer le Pré-filtrage Crédit BCT</span>
            }
          </button>
        </div>

        <!-- Output Report (Right Column) -->
        <div class="glass-card report-card">
          @if (!report()) {
            <div class="report-empty-state">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="empty-icon">
                <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" />
              </svg>
              <h3 class="empty-title">Prêt pour l'évaluation des risques</h3>
              <p class="empty-desc">Sélectionnez un cas type ci-dessus ou ajustez les paramètres financiers pour générer l'audit d'éligibilité.</p>
            </div>
          } @else {
            <div class="report-header">
              <div>
                <h2 class="report-applicant-name">{{ report().applicant_name }}</h2>
                <div class="report-dossier-meta">
                  Dossier Ref : <strong>{{ report().dossier_id }}</strong> • Type : <strong>{{ loanType | uppercase }}</strong>
                </div>
              </div>
              <div class="verdict-tag" [class.verdict-approved]="report().overall_verdict === 'APPROVED' || report().overall_verdict === 'CONFORME'" [class.verdict-rejected]="report().overall_verdict === 'REJECTED' || report().overall_verdict === 'REFUSE'">
                {{ report().overall_verdict === 'APPROVED' || report().overall_verdict === 'CONFORME' ? '✓ ÉLIGIBLE & CONFORME BCT' : '⚠️ NON CONFORME / REFUS BCT' }}
              </div>
            </div>

            <!-- Sub-Agents Results Cards -->
            <div class="agent-cards-grid">
              <!-- Agent 1 : Complétude -->
              <div class="agent-card">
                <div class="agent-card-top">
                  <span class="agent-name">1. Agent Complétude Documentaire</span>
                  <span class="agent-score">{{ ((report().document_completeness?.completeness_ratio || 1) * 100).toFixed(0) }}%</span>
                </div>
                <div class="agent-detail">Pièces fournies : <strong>{{ uploadedFiles.length }} / 4</strong></div>
                <div class="agent-status" [class.status-ok]="report().document_completeness?.verdict === 'COMPLETE'" [class.status-ko]="report().document_completeness?.verdict !== 'COMPLETE'">
                  Verdict : {{ report().document_completeness?.verdict || 'CONFORME' }}
                </div>
              </div>

              <!-- Agent 2 : Ratio d'Endettement -->
              <div class="agent-card">
                <div class="agent-card-top">
                  <span class="agent-name">2. Agent Ratio d'Endettement BCT</span>
                  <span class="agent-score" [class.score-bad]="((report().numerical_validation?.debt_ratio || 0) * 100) > 40">
                    {{ ((report().numerical_validation?.debt_ratio || 0) * 100).toFixed(1) }}%
                  </span>
                </div>
                <div class="agent-detail">Seuil BCT légal maximal : <strong>40.0%</strong></div>
                <div class="agent-status" [class.status-ok]="report().numerical_validation?.debt_ratio_compliant" [class.status-ko]="!report().numerical_validation?.debt_ratio_compliant">
                  {{ report().numerical_validation?.debt_ratio_compliant ? '✓ Conforme au plafond réglementaire' : '⚠️ Dépassement de la limite BCT' }}
                </div>
              </div>
            </div>

            <!-- Blocking issues -->
            @if (report().blocking_issues?.length) {
              <div class="blocking-box">
                <h3 class="blocking-title">Motifs de Non-Conformité Identifiés</h3>
                <div class="blocking-list">
                  @for (issue of report().blocking_issues; track $index) {
                    <div class="blocking-item">
                      <svg class="blocking-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                      </svg>
                      <span>{{ issue }}</span>
                    </div>
                  }
                </div>
              </div>
            }

            <!-- Regulatory References -->
            @if (report().regulatory_references?.length) {
              <div class="references-box">
                <h3 class="references-title">Textes & Circulaires BCT de Référence</h3>
                <div class="references-chips">
                  @for (ref of report().regulatory_references; track $index) {
                    <span class="ref-chip">
                      📜 {{ ref }}
                    </span>
                  }
                </div>
              </div>
            }

            <!-- Audit Trail Certification -->
            <div class="audit-footer">
              <span>🔒 Consigné dans le Registre d'Audit des Engagements Attijari Bank • Validation Cryptographique PostgreSQL</span>
            </div>
          }
        </div>
      </div>
    </div>
  `,
  styles: [`
    .credit-page-container {
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

    .bct-limit-card {
      background: rgba(0, 0, 0, 0.3);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 12px;
      padding: 0.85rem 1.25rem;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      flex-shrink: 0;

      .limit-label { font-size: 0.68rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; }
      .limit-value { font-size: 1.8rem; font-weight: 900; color: #38bdf8; }
      .limit-desc { font-size: 0.65rem; color: var(--text-muted); }
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
    .dot-amber { background: #f59e0b; }
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

    .form-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.85rem;
    }

    .form-label {
      display: block;
      font-size: 0.75rem;
      font-weight: 700;
      color: var(--text-secondary);
      margin-bottom: 0.35rem;
    }

    .form-input, .form-select {
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
    }

    .file-chips-container {
      display: flex;
      flex-wrap: wrap;
      gap: 0.35rem;
      margin-top: 0.5rem;
    }

    .file-chip {
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid rgba(16, 185, 129, 0.25);
      color: #34d399;
      font-size: 0.7rem;
      font-weight: 600;
      padding: 0.2rem 0.5rem;
      border-radius: 6px;
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
      margin-top: 1.25rem;

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
      margin-bottom: 1.5rem;
    }

    .report-applicant-name {
      font-size: 1.4rem;
      font-weight: 900;
      color: var(--text-primary);
    }

    .report-dossier-meta {
      font-size: 0.78rem;
      color: var(--text-muted);
      margin-top: 0.2rem;
    }

    .verdict-tag {
      padding: 0.5rem 1rem;
      border-radius: 8px;
      font-size: 0.82rem;
      font-weight: 800;
      letter-spacing: 0.02em;

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

    .agent-cards-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
      margin-bottom: 1.5rem;

      @media (max-width: 768px) {
        grid-template-columns: 1fr;
      }
    }

    .agent-card {
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 0.4rem;

      .agent-card-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.25rem;
      }

      .agent-name {
        font-size: 0.8rem;
        font-weight: 700;
        color: var(--text-primary);
      }

      .agent-score {
        font-size: 1.35rem;
        font-weight: 900;
        color: #10b981;

        &.score-bad {
          color: #ef4444;
        }
      }

      .agent-detail {
        font-size: 0.75rem;
        color: var(--text-secondary);
      }

      .agent-status {
        font-size: 0.75rem;
        font-weight: 700;
        margin-top: 0.25rem;

        &.status-ok { color: #10b981; }
        &.status-ko { color: #ef4444; }
      }
    }

    .blocking-box {
      background: rgba(239, 68, 68, 0.08);
      border: 1px solid rgba(239, 68, 68, 0.25);
      border-radius: 12px;
      padding: 1.25rem;
      margin-bottom: 1.25rem;

      .blocking-title {
        font-size: 0.78rem;
        font-weight: 800;
        text-transform: uppercase;
        color: #ef4444;
        margin-bottom: 0.65rem;
      }

      .blocking-list {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
      }

      .blocking-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.82rem;
        color: #fca5a5;
        font-weight: 600;

        .blocking-icon {
          width: 1rem;
          height: 1rem;
          flex-shrink: 0;
          color: #ef4444;
        }
      }
    }

    .references-box {
      margin-bottom: 1.5rem;

      .references-title {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        color: var(--text-muted);
        margin-bottom: 0.5rem;
      }

      .references-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
      }

      .ref-chip {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid var(--border-color);
        color: var(--text-secondary);
        padding: 0.3rem 0.65rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
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
export class CreditComponent {
  api = inject(ApiService);
  applicantName = 'Ahmed Ben Ali';
  loanType = 'personal';
  income = 3500;
  monthlyDebt = 350;
  loanAnnuity = 450;
  uploadedFiles: string[] = ['cin_recto_verso.pdf', 'bulletin_paie_recent.pdf', 'releve_bancaire_3mois.pdf', 'attestation_travail.pdf'];
  report = signal<any>(null);
  loading = signal(false);

  loadPreset(type: string) {
    if (type === 'approve') {
      this.applicantName = 'Karim Mansour';
      this.loanType = 'personal';
      this.income = 4000;
      this.monthlyDebt = 300;
      this.loanAnnuity = 600;
      this.uploadedFiles = ['cin.pdf', 'bulletin_paie.pdf', 'releve_bancaire.pdf', 'attestation_travail.pdf'];
    } else if (type === 'reject_debt') {
      this.applicantName = 'Sami Trabelsi';
      this.loanType = 'personal';
      this.income = 2000;
      this.monthlyDebt = 750;
      this.loanAnnuity = 300;
      this.uploadedFiles = ['cin.pdf', 'bulletin_paie.pdf', 'releve_bancaire.pdf', 'attestation_travail.pdf'];
    } else if (type === 'missing_docs') {
      this.applicantName = 'Leila Bouazizi';
      this.loanType = 'mortgage';
      this.income = 2800;
      this.monthlyDebt = 200;
      this.loanAnnuity = 500;
      this.uploadedFiles = ['cin.pdf'];
    } else if (type === 'corporate') {
      this.applicantName = 'STE MAGHREB ENERGIE SARL';
      this.loanType = 'corporate';
      this.income = 15000;
      this.monthlyDebt = 2000;
      this.loanAnnuity = 2500;
      this.uploadedFiles = ['bilans_certifies_3ans.pdf', 'extrait_rne.pdf', 'statuts.pdf', 'declaration_fiscale.pdf'];
    }
  }

  onFilesSelected(event: any) {
    if (event.target.files && event.target.files.length > 0) {
      this.uploadedFiles = Array.from(event.target.files).map((f: any) => f.name);
    }
  }

  prescreen() {
    if (!this.applicantName) return;
    this.loading.set(true);

    this.api.prescreenCredit({
      dossier_id: `cred_${Date.now().toString().slice(-4)}`,
      applicant_name: this.applicantName,
      loan_type: this.loanType,
      files: this.uploadedFiles,
      financial_data: {
        income: this.income,
        monthly_debt: this.monthlyDebt,
        loan_annuity: this.loanAnnuity
      }
    }).subscribe({
      next: (res) => {
        this.report.set(res);
        this.loading.set(false);
      },
      error: () => this.loading.set(false)
    });
  }
}

