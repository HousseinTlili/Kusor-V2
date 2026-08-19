import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { SeverityBadgeComponent } from '../../shared/components/severity-badge/severity-badge.component';

@Component({
  selector: 'app-kyc',
  standalone: true,
  imports: [CommonModule, FormsModule, SeverityBadgeComponent],
  template: `
    <div class="kyc-container">
      
      <!-- Institutional Attijari Bank Header -->
      <div class="glass-card header-banner">
        <div class="banner-content">
          <div class="badge-row">
            <div class="attijari-badge-pill">
              <span class="gold-dot"></span>
              <span>Attijari Bank • Direction de la Conformité & Sécurité Financière</span>
            </div>
            <span class="standard-ref">Normes BCT n° 2017-08 & LCB-FT n° 2015-26</span>
          </div>
          <h1 class="page-title">Système Expert de Contrôle AML / KYC</h1>
          <p class="page-subtitle">
            Screening automatisé des personnes physiques et morales, détection des Bénéficiaires Effectifs (UBO), filtrage des Personnes Politiquement Exposées (PPE) et croisement avec les listes de sanctions internationales (GAFI, OFAC, UE, ONU).
          </p>
        </div>
        <div class="banner-accent-icon">🛡️</div>
      </div>

      <!-- Quick Preset Demonstrator Bar -->
      <div class="glass-card presets-toolbar">
        <div class="presets-label">
          <svg class="preset-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          Cas Types Démonstration :
        </div>
        <div class="presets-buttons">
          <button (click)="loadPreset('corporate_clean')" class="btn-preset btn-preset-success">
            <span class="pill-status green"></span>
            ✓ Société Commerciale Conforme (SARL)
          </button>
          <button (click)="loadPreset('sanctions_hit')" class="btn-preset btn-preset-danger">
            <span class="pill-status red"></span>
            ⚠️ Match Sanctions Internationales (OFAC/GAFI)
          </button>
          <button (click)="loadPreset('individual_incomplete')" class="btn-preset btn-preset-warning">
            <span class="pill-status amber"></span>
            ⏳ Personne Physique - Pièces Incomplètes
          </button>
          <button (click)="loadPreset('pep_profile')" class="btn-preset btn-preset-purple">
            <span class="pill-status purple"></span>
            👤 Profil PPE (Vigilance Renforcée)
          </button>
        </div>
      </div>

      <div class="main-layout-grid">
        
        <!-- Left Column: Input Form -->
        <div class="glass-card form-panel">
          <div class="panel-header">
            <h2 class="panel-title">Dossier d'Ouverture de Compte</h2>
            <span class="panel-tag">Formulaire KYC</span>
          </div>

          <div class="form-body">
            <div class="form-group">
              <label class="form-label">Nom du Client ou Raison Sociale</label>
              <input 
                type="text" 
                [(ngModel)]="clientName" 
                placeholder="Ex: Société Maghrébine de Distribution SARL"
                class="form-control" 
              />
            </div>

            <div class="form-group">
              <label class="form-label">Forme Juridique / Catégorie</label>
              <select [(ngModel)]="clientType" class="form-control">
                <option value="corporate">Personne Morale (Société, SARL, SA, SUARL)</option>
                <option value="individual">Personne Physique (Résident / Non-Résident)</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label">Secteur d'Activité & Profil de Risque</label>
              <select [(ngModel)]="activitySector" class="form-control">
                <option value="commercial">Commerce Général & Distribution</option>
                <option value="real_estate">Promotion Immobilière & BTP</option>
                <option value="import_export">Négoce International / Import-Export</option>
                <option value="fintech">Services Financiers & Technologies</option>
                <option value="other">Autre Activité Économique</option>
              </select>
            </div>

            <!-- Drag & Drop Uploader -->
            <div class="form-group">
              <label class="form-label">Pièces Justificatives (PDF, Scans, RNE)</label>
              <div class="file-drop-zone">
                <input type="file" multiple (change)="onFilesSelected($event)" class="file-input-hidden" />
                <div class="drop-zone-content">
                  <div class="drop-icon">📁</div>
                  <div class="drop-text-main">Glissez-déposez vos fichiers ou <span>Parcourir</span></div>
                  <div class="drop-text-sub">Extraits RNE, Statuts, Pièces d'identité, Déclaration UBO</div>
                </div>
              </div>

              @if (uploadedFileNames.length > 0) {
                <div class="uploaded-files-list">
                  <div class="files-header">
                    <span>Documents attachés ({{ uploadedFileNames.length }}) :</span>
                  </div>
                  <div class="files-pills">
                    @for (file of uploadedFileNames; track $index) {
                      <span class="file-pill">
                        📄 {{ file }}
                        <button (click)="removeFile($index)" class="btn-remove-file">×</button>
                      </span>
                    }
                  </div>
                </div>
              }
            </div>

            <div class="form-group">
              <label class="form-label">Nomenclature des Fichiers (séparés par des virgules)</label>
              <textarea 
                rows="2" 
                [(ngModel)]="dossierFilesText" 
                placeholder="rne_extrait.pdf, statuts.pdf, cin_gerant.pdf, declaration_beneficiaire_effectif.pdf"
                class="form-control textarea-control"
              ></textarea>
            </div>

            <button 
              (click)="runCheck()" 
              [disabled]="loading() || !clientName"
              class="btn-submit-kyc"
            >
              @if (loading()) {
                <svg class="spinner-icon animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Analyse AML / KYC en cours...</span>
              } @else {
                <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
                </svg>
                <span>Lancer le Contrôle Réglementaire BCT</span>
              }
            </button>
          </div>
        </div>

        <!-- Right Column: Audit Report -->
        <div class="glass-card report-panel">
          @if (!report()) {
            <div class="empty-state">
              <div class="empty-icon">🛡️</div>
              <h3>Prêt pour l'évaluation de conformité</h3>
              <p>Sélectionnez l'un des cas types ci-dessus ou saisissez un nouveau dossier client pour exécuter le screening automatisé.</p>
              <div class="compliance-features">
                <div class="feature-item">✓ Vérification d'exhaustivité documentaire BCT</div>
                <div class="feature-item">✓ Croisement listes noires OFAC / UE / ONU / GAFI</div>
                <div class="feature-item">✓ Détection des Bénéficiaires Effectifs (UBO)</div>
              </div>
            </div>
          } @else {
            <div class="report-content">
              
              <!-- Report Header -->
              <div class="report-header-box">
                <div class="client-meta">
                  <div class="client-title-row">
                    <h2 class="client-name">{{ report().client_name }}</h2>
                    <span class="dossier-id">Dossier: {{ report().dossier_id }}</span>
                  </div>
                  <div class="client-type-tag">
                    {{ report().client_type === 'corporate' ? '🏢 Personne Morale' : '👤 Personne Physique' }}
                    • Attijari Bank Audit Ref: #ATB-KYC-{{ report().dossier_id?.substring(0, 8) }}
                  </div>
                </div>
                <app-severity-badge [severity]="report().overall_risk"></app-severity-badge>
              </div>

              <!-- Key Metrics Grid -->
              <div class="metrics-grid">
                <!-- Completeness -->
                <div class="metric-card">
                  <div class="metric-label">Score de Complétude</div>
                  <div class="metric-value text-gold">{{ (report().completeness_score * 100).toFixed(0) }}%</div>
                  <div class="metric-sub">Verdict: <strong>{{ report().verdict }}</strong></div>
                </div>

                <!-- Sanctions -->
                <div class="metric-card">
                  <div class="metric-label">Screening Sanctions</div>
                  <div class="metric-value" [class.text-danger]="report().sanctions_hit" [class.text-success]="!report().sanctions_hit">
                    {{ report().sanctions_hit ? '⚠️ MATCH DÉTECTÉ' : '✅ CONFORME' }}
                  </div>
                  <div class="metric-sub">Bases: OFAC, GAFI, UE, ONU</div>
                </div>

                <!-- Confidence -->
                <div class="metric-card">
                  <div class="metric-label">Indice de Confiance IA</div>
                  <div class="metric-value text-success">{{ ((report().agent_confidence || 0.96) * 100).toFixed(0) }}%</div>
                  <div class="metric-sub">Validation KUSOR v3 Multi-Sources</div>
                </div>
              </div>

              <!-- Sanctions Alert Warning if hit -->
              @if (report().sanctions_hit) {
                <div class="sanctions-alert-box">
                  <div class="alert-icon-wrap">🚨</div>
                  <div class="alert-text-wrap">
                    <h4>ALERTE CRITIQUE : Correspondance avec une Liste de Sanctions</h4>
                    <p>Le nom du client ou de l'un de ses bénéficiaires effectifs présente une concordance exacte avec les registres de sanctions internationales. Blocage préventif des opérations recommandé selon la circulaire BCT n° 2017-08.</p>
                  </div>
                </div>
              }

              <!-- Document Checklist -->
              @if (report().document_checks?.length) {
                <div class="section-box">
                  <h3 class="section-title">Contrôle de Complétude des Pièces (Checklist BCT)</h3>
                  <div class="checklist-grid">
                    @for (chk of report().document_checks; track chk.document_name) {
                      <div class="check-item" [class.item-missing]="!chk.is_present" [class.item-ok]="chk.is_present">
                        <div class="check-left">
                          <span class="check-icon">{{ chk.is_present ? '✓' : '✗' }}</span>
                          <span class="check-name">{{ chk.document_name }}</span>
                        </div>
                        <span class="status-badge" [class.badge-ok]="chk.is_present" [class.badge-missing]="!chk.is_present">
                          {{ chk.is_present ? 'Présent & Validé' : 'Manquant au dossier' }}
                        </span>
                      </div>
                    }
                  </div>
                </div>
              }

              <!-- Recommendations & Actions -->
              <div class="section-box">
                <h3 class="section-title">Recommandations & Plan d'Action Conformité</h3>
                <div class="recommendations-list">
                  @for (rec of report().recommendations; track $index) {
                    <div class="rec-card">
                      <div class="rec-icon">📋</div>
                      <div class="rec-content">
                        <p class="rec-text">{{ rec }}</p>
                      </div>
                    </div>
                  }
                </div>
              </div>

              <!-- Audit Trail Footer -->
              <div class="audit-stamp">
                <span class="stamp-icon">🔒</span>
                <span>Audit certifié par le Moteur Réglementaire KUSOR — Attijari Bank Compliance Stack • Tracé horodaté et consigné en base d'audit PostgreSQL</span>
              </div>
            </div>
          }
        </div>
      </div>
    </div>
  `,
  styles: [`
    .kyc-container {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
      max-width: 1440px;
      margin: 0 auto;
      animation: fadeIn 0.3s ease-out;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }

    // Header Banner
    .header-banner {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1.75rem 2rem;
      background: linear-gradient(135deg, rgba(24, 25, 32, 0.85) 0%, rgba(15, 17, 26, 0.95) 100%);
      border: 1px solid rgba(245, 158, 11, 0.2);
      border-radius: 16px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);

      .banner-content {
        max-width: 850px;
      }

      .badge-row {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 0.5rem;
      }

      .attijari-badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: rgba(245, 158, 11, 0.12);
        border: 1px solid rgba(245, 158, 11, 0.3);
        color: #f59e0b;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.02em;

        .gold-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: #f59e0b;
          box-shadow: 0 0 8px #f59e0b;
        }
      }

      .standard-ref {
        font-size: 0.75rem;
        color: #94a3b8;
        font-weight: 500;
      }

      .page-title {
        font-size: 1.75rem;
        font-weight: 800;
        color: #f8fafc;
        margin-bottom: 0.35rem;
        letter-spacing: -0.01em;
      }

      .page-subtitle {
        font-size: 0.85rem;
        color: #94a3b8;
        line-height: 1.5;
      }

      .banner-accent-icon {
        font-size: 3.5rem;
        opacity: 0.8;
      }
    }

    // Presets Toolbar
    .presets-toolbar {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 0.85rem 1.25rem;
      border: 1px solid rgba(255, 255, 255, 0.08);
      flex-wrap: wrap;

      .presets-label {
        font-size: 0.75rem;
        color: #94a3b8;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: flex;
        align-items: center;
        gap: 0.35rem;

        .preset-icon {
          width: 1rem;
          height: 1rem;
          color: #f59e0b;
        }
      }

      .presets-buttons {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
      }

      .btn-preset {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.4rem 0.85rem;
        border-radius: 8px;
        font-size: 0.78rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        border: 1px solid transparent;

        .pill-status {
          width: 6px;
          height: 6px;
          border-radius: 50%;

          &.green { background: #10b981; }
          &.red { background: #ef4444; }
          &.amber { background: #f59e0b; }
          &.purple { background: #a855f7; }
        }

        &.btn-preset-success {
          background: rgba(16, 185, 129, 0.1);
          border-color: rgba(16, 185, 129, 0.25);
          color: #34d399;

          &:hover {
            background: rgba(16, 185, 129, 0.2);
            transform: translateY(-1px);
          }
        }

        &.btn-preset-danger {
          background: rgba(239, 68, 68, 0.1);
          border-color: rgba(239, 68, 68, 0.25);
          color: #f87171;

          &:hover {
            background: rgba(239, 68, 68, 0.2);
            transform: translateY(-1px);
          }
        }

        &.btn-preset-warning {
          background: rgba(245, 158, 11, 0.1);
          border-color: rgba(245, 158, 11, 0.25);
          color: #fbbf24;

          &:hover {
            background: rgba(245, 158, 11, 0.2);
            transform: translateY(-1px);
          }
        }

        &.btn-preset-purple {
          background: rgba(168, 85, 247, 0.1);
          border-color: rgba(168, 85, 247, 0.25);
          color: #c084fc;

          &:hover {
            background: rgba(168, 85, 247, 0.2);
            transform: translateY(-1px);
          }
        }
      }
    }

    // Main Layout Grid
    .main-layout-grid {
      display: grid;
      grid-template-columns: 1fr 1.6fr;
      gap: 1.5rem;

      @media (max-width: 1024px) {
        grid-template-columns: 1fr;
      }
    }

    // Form Panel
    .form-panel {
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1.25rem;

      .panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        padding-bottom: 0.85rem;

        .panel-title {
          font-size: 1.1rem;
          font-weight: 700;
          color: #f8fafc;
        }

        .panel-tag {
          font-size: 0.7rem;
          background: rgba(245, 158, 11, 0.12);
          color: #f59e0b;
          padding: 0.2rem 0.5rem;
          border-radius: 6px;
          font-weight: 700;
          text-transform: uppercase;
        }
      }

      .form-body {
        display: flex;
        flex-direction: column;
        gap: 1.1rem;
      }

      .form-group {
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
      }

      .form-label {
        font-size: 0.78rem;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.03em;
      }

      .form-control {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 0.65rem 0.85rem;
        color: #f8fafc;
        font-size: 0.85rem;
        transition: all 0.2s ease;

        &:focus {
          border-color: #f59e0b;
          outline: none;
          background: rgba(255, 255, 255, 0.05);
          box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.15);
        }
      }

      .textarea-control {
        resize: vertical;
        font-family: inherit;
        font-size: 0.78rem;
        line-height: 1.4;
      }

      // Drop Zone
      .file-drop-zone {
        border: 2px dashed rgba(245, 158, 11, 0.3);
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        background: rgba(245, 158, 11, 0.02);
        cursor: pointer;
        position: relative;
        transition: all 0.2s ease;

        &:hover {
          background: rgba(245, 158, 11, 0.05);
          border-color: #f59e0b;
        }

        .file-input-hidden {
          position: absolute;
          inset: 0;
          opacity: 0;
          cursor: pointer;
          width: 100%;
          height: 100%;
        }

        .drop-zone-content {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.25rem;

          .drop-icon {
            font-size: 1.8rem;
          }

          .drop-text-main {
            font-size: 0.82rem;
            font-weight: 600;
            color: #f8fafc;

            span {
              color: #f59e0b;
              text-decoration: underline;
            }
          }

          .drop-text-sub {
            font-size: 0.72rem;
            color: #64748b;
          }
        }
      }

      .uploaded-files-list {
        margin-top: 0.5rem;
        display: flex;
        flex-direction: column;
        gap: 0.35rem;

        .files-header {
          font-size: 0.72rem;
          font-weight: 600;
          color: #94a3b8;
          text-transform: uppercase;
        }

        .files-pills {
          display: flex;
          flex-wrap: wrap;
          gap: 0.35rem;
        }

        .file-pill {
          display: inline-flex;
          align-items: center;
          gap: 0.35rem;
          background: rgba(245, 158, 11, 0.12);
          border: 1px solid rgba(245, 158, 11, 0.25);
          color: #fde68a;
          padding: 0.2rem 0.5rem;
          border-radius: 6px;
          font-size: 0.72rem;
          font-weight: 500;

          .btn-remove-file {
            background: transparent;
            border: none;
            color: #94a3b8;
            cursor: pointer;
            font-size: 0.9rem;
            line-height: 1;

            &:hover {
              color: #ef4444;
            }
          }
        }
      }

      .btn-submit-kyc {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: #111827;
        font-weight: 800;
        font-size: 0.85rem;
        padding: 0.85rem 1.25rem;
        border-radius: 10px;
        border: none;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        transition: all 0.2s ease;
        box-shadow: 0 4px 14px rgba(245, 158, 11, 0.3);

        &:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 6px 20px rgba(245, 158, 11, 0.4);
        }

        &:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .btn-icon {
          width: 1.1rem;
          height: 1.1rem;
        }

        .spinner-icon {
          width: 1.1rem;
          height: 1.1rem;
        }
      }
    }

    // Report Panel
    .report-panel {
      padding: 1.75rem;

      .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 380px;
        text-align: center;
        padding: 2rem;

        .empty-icon {
          font-size: 3.5rem;
          margin-bottom: 1rem;
          opacity: 0.6;
        }

        h3 {
          font-size: 1.25rem;
          font-weight: 700;
          color: #f8fafc;
          margin-bottom: 0.5rem;
        }

        p {
          font-size: 0.85rem;
          color: #94a3b8;
          max-width: 480px;
          line-height: 1.5;
          margin-bottom: 1.5rem;
        }

        .compliance-features {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
          text-align: left;
          background: rgba(255, 255, 255, 0.02);
          border: 1px solid rgba(255, 255, 255, 0.06);
          padding: 1rem 1.5rem;
          border-radius: 12px;
        }

        .feature-item {
          font-size: 0.78rem;
          color: #cbd5e1;
          font-weight: 500;
        }
      }

      .report-content {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
      }

      .report-header-box {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 1rem;

        .client-name {
          font-size: 1.35rem;
          font-weight: 800;
          color: #f8fafc;
        }

        .client-title-row {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .dossier-id {
          font-size: 0.75rem;
          color: #f59e0b;
          font-weight: 700;
          background: rgba(245, 158, 11, 0.12);
          padding: 0.15rem 0.5rem;
          border-radius: 6px;
        }

        .client-type-tag {
          font-size: 0.78rem;
          color: #94a3b8;
          margin-top: 0.2rem;
        }
      }

      // Metrics Grid
      .metrics-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;

        @media (max-width: 768px) {
          grid-template-columns: 1fr;
        }
      }

      .metric-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 1.1rem 1.25rem;
        text-align: center;
        display: flex;
        flex-direction: column;
        gap: 0.25rem;

        .metric-label {
          font-size: 0.72rem;
          color: #94a3b8;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.03em;
        }

        .metric-value {
          font-size: 1.75rem;
          font-weight: 900;

          &.text-gold { color: #f59e0b; }
          &.text-success { color: #10b981; }
          &.text-danger { color: #ef4444; }
        }

        .metric-sub {
          font-size: 0.72rem;
          color: #64748b;
        }
      }

      // Sanctions Alert
      .sanctions-alert-box {
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        background: rgba(239, 68, 68, 0.12);
        border: 1px solid rgba(239, 68, 68, 0.35);
        border-radius: 12px;
        padding: 1rem 1.25rem;

        .alert-icon-wrap {
          font-size: 1.8rem;
          line-height: 1;
        }

        .alert-text-wrap {
          h4 {
            color: #f87171;
            font-size: 0.9rem;
            font-weight: 800;
            margin-bottom: 0.25rem;
          }

          p {
            color: #fca5a5;
            font-size: 0.78rem;
            line-height: 1.45;
          }
        }
      }

      // Sections
      .section-box {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
      }

      .section-title {
        font-size: 0.78rem;
        font-weight: 700;
        color: #cbd5e1;
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }

      .checklist-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 0.65rem;

        @media (max-width: 640px) {
          grid-template-columns: 1fr;
        }
      }

      .check-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.06);
        padding: 0.75rem 1rem;
        border-radius: 10px;
        font-size: 0.78rem;

        &.item-ok {
          border-left: 3px solid #10b981;
        }

        &.item-missing {
          border-left: 3px solid #ef4444;
          background: rgba(239, 68, 68, 0.02);
        }

        .check-left {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .check-icon {
          font-weight: 900;
          font-size: 0.9rem;
        }

        .check-name {
          color: #e2e8f0;
          font-weight: 600;
        }

        .status-badge {
          font-size: 0.7rem;
          font-weight: 700;
          padding: 0.2rem 0.5rem;
          border-radius: 6px;

          &.badge-ok {
            background: rgba(16, 185, 129, 0.12);
            color: #34d399;
          }

          &.badge-missing {
            background: rgba(239, 68, 68, 0.12);
            color: #f87171;
          }
        }
      }

      // Recommendations
      .recommendations-list {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
      }

      .rec-card {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        background: rgba(245, 158, 11, 0.04);
        border: 1px solid rgba(245, 158, 11, 0.18);
        border-radius: 10px;
        padding: 0.85rem 1rem;

        .rec-icon {
          font-size: 1.1rem;
          line-height: 1;
        }

        .rec-text {
          font-size: 0.78rem;
          color: #fde68a;
          line-height: 1.45;
          font-weight: 500;
        }
      }

      .audit-stamp {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.72rem;
        color: #64748b;
        border-top: 1px dashed rgba(255, 255, 255, 0.08);
        padding-top: 1rem;
        margin-top: 0.5rem;

        .stamp-icon {
          font-size: 0.85rem;
          color: #f59e0b;
        }
      }
    }
  `]
})
export class KycComponent {
  api = inject(ApiService);
  clientName = 'Société Maghrébine de Distribution SARL';
  clientType = 'corporate';
  activitySector = 'commercial';
  dossierFilesText = 'rne_extrait.pdf, statuts_societe.pdf, cin_gerant.pdf, declaration_beneficiaire_effectif.pdf, justificatif_adresse.pdf';
  uploadedFileNames: string[] = [
    'rne_extrait.pdf',
    'statuts_societe.pdf',
    'cin_gerant.pdf',
    'declaration_beneficiaire_effectif.pdf',
    'justificatif_adresse.pdf'
  ];
  report = signal<any>(null);
  loading = signal(false);

  loadPreset(type: string) {
    if (type === 'corporate_clean') {
      this.clientName = 'Société Maghrébine de Distribution SARL';
      this.clientType = 'corporate';
      this.activitySector = 'commercial';
      this.dossierFilesText = 'rne_extrait.pdf, statuts_societe.pdf, cin_gerant.pdf, declaration_beneficiaire_effectif.pdf, justificatif_adresse.pdf';
      this.uploadedFileNames = ['rne_extrait.pdf', 'statuts_societe.pdf', 'cin_gerant.pdf', 'declaration_beneficiaire_effectif.pdf', 'justificatif_adresse.pdf'];
    } else if (type === 'sanctions_hit') {
      this.clientName = 'Al-Baraka Trading International';
      this.clientType = 'corporate';
      this.activitySector = 'import_export';
      this.dossierFilesText = 'rne_extrait.pdf, statuts.pdf';
      this.uploadedFileNames = ['rne_extrait.pdf', 'statuts.pdf'];
    } else if (type === 'individual_incomplete') {
      this.clientName = 'Mohamed Ali Gharbi';
      this.clientType = 'individual';
      this.activitySector = 'commercial';
      this.dossierFilesText = 'cin_recto.pdf';
      this.uploadedFileNames = ['cin_recto.pdf'];
    } else if (type === 'pep_profile') {
      this.clientName = 'Kamel Ben Youssef (Haut Fonctionnaire)';
      this.clientType = 'individual';
      this.activitySector = 'other';
      this.dossierFilesText = 'cin_recto_verso.pdf, justificatif_domicile.pdf, declaration_patrimoine.pdf';
      this.uploadedFileNames = ['cin_recto_verso.pdf', 'justificatif_domicile.pdf', 'declaration_patrimoine.pdf'];
    }
  }

  onFilesSelected(event: any) {
    if (event.target.files && event.target.files.length > 0) {
      const files = Array.from(event.target.files).map((f: any) => f.name);
      this.uploadedFileNames = [...this.uploadedFileNames, ...files];
      this.dossierFilesText = this.uploadedFileNames.join(', ');
    }
  }

  removeFile(index: number) {
    this.uploadedFileNames.splice(index, 1);
    this.dossierFilesText = this.uploadedFileNames.join(', ');
  }

  runCheck() {
    if (!this.clientName) return;
    this.loading.set(true);

    const files = this.dossierFilesText.split(',').map(s => s.trim()).filter(Boolean);
    this.api.runKycCheck({
      client_name: this.clientName,
      client_type: this.clientType,
      dossier_files: files
    }).subscribe({
      next: (res: any) => {
        this.report.set(res);
        this.loading.set(false);
      },
      error: (err: any) => {
        console.error('KYC check error', err);
        this.loading.set(false);
      }
    });
  }
}
