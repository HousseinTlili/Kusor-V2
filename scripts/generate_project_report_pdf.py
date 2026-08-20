#!/usr/bin/env python3
"""
scripts/generate_project_report_pdf.py
Generates an executive-level, beautifully formatted 2-page PDF report for KUSOR v3.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

PDF_OUTPUT_PATH = "/home/houssein/kusor-v3/KUSOR_v3_Project_Report.pdf"

# ── Color Palette (Attijari Bank & KUSOR Theme) ───────────────────────────
C_PRIMARY = colors.HexColor("#E85D04")      # Sunset Fire Orange
C_PRIMARY_DARK = colors.HexColor("#DC2F02") # Deep Orange
C_NAVY = colors.HexColor("#0F172A")          # Dark Slate
C_BG_CARD = colors.HexColor("#F8FAFC")       # Soft Gray/Card bg
C_TEXT_MAIN = colors.HexColor("#1E293B")     # Dark Charcoal Text
C_TEXT_MUTED = colors.HexColor("#64748B")    # Slate Muted Text
C_BORDER = colors.HexColor("#CBD5E1")        # Border Gray
C_ACCENT_GREEN = colors.HexColor("#10B981")  # Emerald Green
C_WHITE = colors.HexColor("#FFFFFF")


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(C_TEXT_MUTED)

        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(1.8 * cm, 28.5 * cm, "KUSOR v3 — Plateforme d'Intelligence Réglementaire & Conformité Bancaire")
            self.drawRightString(19.2 * cm, 28.5 * cm, "Attijari Bank Tunisie • BCT")
            self.setStrokeColor(C_PRIMARY)
            self.setLineWidth(1)
            self.line(1.8 * cm, 28.3 * cm, 19.2 * cm, 28.3 * cm)

        # Footer (all pages)
        self.setStrokeColor(C_BORDER)
        self.setLineWidth(0.5)
        self.line(1.8 * cm, 1.6 * cm, 19.2 * cm, 1.6 * cm)

        self.setFont("Helvetica", 7.5)
        self.drawString(1.8 * cm, 1.2 * cm, "Document Technique & Fonctionnel • Confidentiel Attijari Bank")
        self.drawRightString(19.2 * cm, 1.2 * cm, f"Page {self._pageNumber} sur {page_count}")
        self.restoreState()


def build_pdf():
    os.makedirs(os.path.dirname(PDF_OUTPUT_PATH), exist_ok=True)
    doc = SimpleDocTemplate(
        PDF_OUTPUT_PATH,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=2.0 * cm,
        bottomMargin=2.0 * cm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=C_NAVY,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=C_PRIMARY,
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=C_NAVY,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=C_PRIMARY_DARK,
        spaceBefore=6,
        spaceAfter=2,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.8,
        textColor=C_TEXT_MAIN,
        spaceAfter=4
    )

    bullet_style = ParagraphStyle(
        'BulletText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.2,
        textColor=C_TEXT_MAIN,
        leftIndent=10,
        spaceAfter=2
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.2,
        leading=11.5,
        textColor=C_NAVY
    )

    table_header_style = ParagraphStyle(
        'TH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=C_WHITE,
        alignment=1
    )

    table_cell_style = ParagraphStyle(
        'TD',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=C_TEXT_MAIN
    )

    story = []

    # ── PAGE 1: TITLE, SUMMARY, PROBLEM & TECH STACK ──────────────────────
    badge_p = Paragraph("<b>RAPPORT DE SYNTHÈSE TECHNIQUE & FONCTIONNELLE DU PROJET</b>", ParagraphStyle('B', fontName='Helvetica-Bold', fontSize=7.5, textColor=C_PRIMARY, alignment=0))
    date_p = Paragraph("<b>Attijari Bank Tunisie • Version 3.0 (2026)</b>", ParagraphStyle('D', fontName='Helvetica-Bold', fontSize=7.5, textColor=C_NAVY, alignment=2))
    badge_table = Table([[badge_p, date_p]], colWidths=[10.5 * cm, 6.9 * cm])
    badge_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(badge_table)
    story.append(Spacer(1, 0.15 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=C_PRIMARY, spaceBefore=1, spaceAfter=8))

    story.append(Paragraph("KUSOR v3 — Plateforme d'Intelligence Réglementaire & Conformité Bancaire", title_style))
    story.append(Paragraph("Système d'Agents Autonomes, Graph RAG 4-Canaux et Analyse Automatisée de Dossiers Multi-PDF", subtitle_style))

    # Executive Overview Box
    exec_summary_html = """
    <b>Résumé Exécutif :</b> KUSOR v3 est une solution d'IA bancaire d'entreprise conçue pour le cadre réglementaire de la <b>Banque Centrale de Tunisie (BCT)</b>. Elle automatise le traitement documentaire multi-fichiers, le contrôle de conformité KYC/AML, le pré-filtrage des crédits (respect du ratio d'endettement ≤ 40%) et l'audit juridique des contrats de financement à travers un graphe de connaissances temporel Neo4j et un LLM fine-tuné à 97.96% de précision.
    """
    callout_data = [[Paragraph(exec_summary_html, callout_style)]]
    callout_t = Table(callout_data, colWidths=[17.4 * cm])
    callout_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), C_BG_CARD),
        ('BOX', (0, 0), (-1, -1), 1, C_PRIMARY),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(callout_t)
    story.append(Spacer(1, 0.25 * cm))

    # 1. Problématique & Objectifs
    story.append(Paragraph("1. Problématique Métier & Objectifs", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceBefore=1, spaceAfter=5))
    story.append(Paragraph("• <b>Complexité et évolution des textes BCT :</b> Des centaines de circulaires denses avec des amendements temporels partiels difficiles à suivre manuellement.", bullet_style))
    story.append(Paragraph("• <b>Lenteur du traitement des pièces justificatives :</b> L'audit manuel des CIN, fiches de paie, factures STEG et expertises retarde les décisions de plusieurs jours.", bullet_style))
    story.append(Paragraph("• <b>Risques de non-conformité et sanctions :</b> Tout dépassement du taux d'endettement (40% BCT) ou omission sur les listes de sanctions (CTAF/OFAC) expose la banque.", bullet_style))
    story.append(Paragraph("• <b>Objectif KUSOR v3 :</b> Réduire de 85% le délai de traitement des dossiers avec 100% de traçabilité certifiée par journal SHA-256.", bullet_style))
    story.append(Spacer(1, 0.2 * cm))

    # 2. Architecture & Technologies
    story.append(Paragraph("2. Architecture Système & Pile Technologique", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceBefore=1, spaceAfter=5))

    stack_data = [
        [Paragraph("<b>Composant</b>", table_header_style), Paragraph("<b>Technologies</b>", table_header_style), Paragraph("<b>Rôle & Spécifications</b>", table_header_style)],
        [Paragraph("<b>Orchestration Agentique</b>", table_cell_style), Paragraph("LangGraph + State Graph", table_cell_style), Paragraph("Machine d'états à 7 nœuds coordonnant les sous-agents d'extraction, calcul et validation.", table_cell_style)],
        [Paragraph("<b>Moteur RAG 4 Canaux</b>", table_cell_style), Paragraph("ChromaDB + BM25 + Neo4j + RRF", table_cell_style), Paragraph("Fusion RRF (k=60) combinant recherche vectorielle, mots-clés et graphe temporel.", table_cell_style)],
        [Paragraph("<b>LLM Spécialisé BCT</b>", table_cell_style), Paragraph("kusor-qwen:v1 (Fine-Tuned)", table_cell_style), Paragraph("Modèle QLoRA fine-tuné sur 503 cas réglementaires BCT avec 97.96% de précision.", table_cell_style)],
        [Paragraph("<b>Extraction Documentaire</b>", table_cell_style), Paragraph("PyMuPDF + Tesseract OCR", table_cell_style), Paragraph("Extraction structurée des CIN, fiches de salaire, factures STEG, compromis et contrats.", table_cell_style)],
        [Paragraph("<b>Interface Utilisateur</b>", table_cell_style), Paragraph("Angular 17+ (Sunset Fire / Black)", table_cell_style), Paragraph("Console bancaire avec emplacements dédiés par document et disposition horizontale.", table_cell_style)],
        [Paragraph("<b>Déploiement Conteneurisé</b>", table_cell_style), Paragraph("Docker Compose + Nginx Alpine", table_cell_style), Paragraph("Stack 100% conteneurisée prête pour la production avec Gunicorn et reverse proxy.", table_cell_style)],
    ]
    t_stack = Table(stack_data, colWidths=[3.8 * cm, 4.4 * cm, 9.2 * cm])
    t_stack.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_NAVY),
        ('GRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [C_WHITE, C_BG_CARD]),
    ]))
    story.append(t_stack)

    # ── PAGE BREAK ────────────────────────────────────────────────────────
    story.append(PageBreak())

    # ── PAGE 2: FUNCTIONAL MODULES, IMPACT & CONCLUSION ───────────────────
    story.append(Paragraph("3. Modules Métiers & Cas d'Usage Réalisés", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceBefore=1, spaceAfter=6))

    story.append(Paragraph("<b>A. Module Conformité AML / KYC (Circulaire BCT 2018-09)</b>", h2_style))
    story.append(Paragraph("• <b>Emplacements dédiés :</b> Slots distincts pour CIN, Justificatif de domicile (< 3 mois), Fiche de paie, et Spécimen de signature.", bullet_style))
    story.append(Paragraph("• <b>Extraction automatique :</b> Capture du numéro CIN 8 chiffres, date de naissance, employeur et salaire net.", bullet_style))
    story.append(Paragraph("• <b>Filtrage Sanctions & PPE :</b> Détection instantanée des correspondances avec les listes CTAF/OFAC/ONU et évaluation du score de similarité.", bullet_style))

    story.append(Paragraph("<b>B. Module Pré-filtrage Crédit Multi-Agent (Circulaire BCT 2016-01)</b>", h2_style))
    story.append(Paragraph("• <b>Sous-Agent Complétude :</b> Contrôle la présence des pièces requises selon le type de prêt (Hypothécaire, Personnel, PME).", bullet_style))
    story.append(Paragraph("• <b>Sous-Agent Financier :</b> Reconstitue l'échéance mensuelle exacte ($M = P \\cdot \\frac{r(1+r)^n}{(1+r)^n - 1}$) et vérifie le respect strict du plafond de 40% d'endettement.", bullet_style))
    story.append(Paragraph("• <b>Sous-Agent Concordance :</b> Valide la cohérence entre l'identité déclarée, l'employeur et les pièces justificatives.", bullet_style))
    story.append(Paragraph("• <b>Superviseur Crédit :</b> Émet un verdict unifié (<code>APPROVE</code>, <code>REVIEW</code>, <code>REJECT</code>).", bullet_style))

    story.append(Paragraph("<b>C. Module Analyse de Risque Juridique des Contrats</b>", h2_style))
    story.append(Paragraph("• <b>Segmentation automatique :</b> Découpe du contrat PDF en articles juridiques individuels.", bullet_style))
    story.append(Paragraph("• <b>Détection des non-conformités :</b> Identification des pénalités excessives (usure) et des clauses léonines.", bullet_style))
    story.append(Paragraph("• <b>Vérification temporelle Neo4j :</b> Contrôle que les circulaires citées dans le contrat sont toujours en vigueur.", bullet_style))

    story.append(Paragraph("<b>D. Graphe de Connaissances Réglementaires Neo4j</b>", h2_style))
    story.append(Paragraph("• Modélisation 2D interactive des relations : <code>MANDATES</code>, <code>ABROGATES</code>, <code>AMENDS</code>, <code>APPLIES_TO</code>.", bullet_style))
    story.append(Spacer(1, 0.25 * cm))

    # 4. Impact Opérationnel & Métriques
    story.append(Paragraph("4. Impact Opérationnel pour Attijari Bank & Conclusion", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceBefore=1, spaceAfter=6))

    impact_data = [
        [Paragraph("<b>Métrique Clé</b>", table_header_style), Paragraph("<b>Avant KUSOR (Manuel)</b>", table_header_style), Paragraph("<b>Avec KUSOR v3 (IA Agentique)</b>", table_header_style)],
        [Paragraph("Temps d'audit d'un dossier KYC", table_cell_style), Paragraph("45 à 90 minutes", table_cell_style), Paragraph("<b>< 10 secondes</b> (Extraction + Filtrage automatique)", table_cell_style)],
        [Paragraph("Pré-qualification d'un crédit", table_cell_style), Paragraph("24 à 48 heures", table_cell_style), Paragraph("<b>Instantané</b> (Calcul du ratio & cross-validation)", table_cell_style)],
        [Paragraph("Traçabilité des décisions", table_cell_style), Paragraph("Dispersée (papier/mails)", table_cell_style), Paragraph("<b>100% Auditable</b> (Journal SHA-256 inviolable)", table_cell_style)],
        [Paragraph("Précision réglementaire BCT", table_cell_style), Paragraph("Sujette à oublis de circulaires", table_cell_style), Paragraph("<b>97.96% de précision</b> avec citations d'articles exactes", table_cell_style)],
    ]
    t_impact = Table(impact_data, colWidths=[4.5 * cm, 4.5 * cm, 8.4 * cm])
    t_impact.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_PRIMARY),
        ('GRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [C_WHITE, C_BG_CARD]),
    ]))
    story.append(t_impact)
    story.append(Spacer(1, 0.25 * cm))

    conclusion_text = """
    <b>Conclusion & Perspective :</b> KUSOR v3 constitue un saut qualitatif majeur pour la transformation numérique d'Attijari Bank. En alliant la rigueur du droit bancaire tunisien à l'autonomie des agents d'intelligence artificielle, la plateforme sécurise les opérations, protège l'institution contre les risques de non-conformité et libère un temps précieux pour les équipes métiers.
    """
    story.append(Paragraph(conclusion_text, body_style))

    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"✅ Executive 2-Page PDF successfully generated at: {PDF_OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()
