#!/usr/bin/env python3
"""
KUSOR v3 — Enterprise PDF Report Generator
Generates a bank-grade compliance & architecture PDF report for Attijari Bank & BCT.
"""
import os
import sys
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        self.saveState()
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#D97706"))
            self.drawString(40, A4[1] - 30, "ATTIJARI BANK")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawString(110, A4[1] - 30, "• Direction de la Conformité & Sécurité Financière — Plateforme KUSOR v3")
            
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.75)
            self.line(40, A4[1] - 35, A4[0] - 40, A4[1] - 35)

        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.75)
        self.line(40, 40, A4[0] - 40, 40)
        
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(colors.HexColor("#0F172A"))
        self.drawString(40, 26, "CONFIDENTIEL BANCAIRE")
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(145, 26, "• Système Expert KUSOR v3 — Conforme BCT n° 2017-08 & LCB-FT n° 2015-26")
        
        page_str = f"Page {self._pageNumber} sur {page_count}"
        self.drawRightString(A4[0] - 40, 26, page_str)
        
        self.restoreState()


def build_pdf(filename: str):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=50,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    primary_color = colors.HexColor("#0F172A")
    gold_color = colors.HexColor("#D97706")
    dark_gold = colors.HexColor("#B45309")
    slate_color = colors.HexColor("#475569")
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=primary_color,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=slate_color,
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=primary_color,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=4
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10.5,
        textColor=colors.HexColor("#1E293B")
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=table_cell,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor("#0F172A")
    )

    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=colors.white
    )

    elements = []

    # ---------------------------------------------------------
    # COVER / HEADER BOX
    # ---------------------------------------------------------
    header_data = [
        [
            Paragraph("<b>ATTIJARI BANK TUNISIE</b><br/><font size=7 color='#64748B'>Direction de la Conformité & Sécurité Financière</font>", table_cell_bold),
            Paragraph(f"<b>RÉFÉRENCE D'AUDIT :</b> ATB-KUSOR-2026<br/><b>DATE DU RAPPORT :</b> {datetime.now().strftime('%d/%m/%Y à %H:%M')}", ParagraphStyle('RightMeta', parent=table_cell, alignment=2))
        ]
    ]
    t_header = Table(header_data, colWidths=[260, 255])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(t_header)
    elements.append(HRFlowable(width="100%", thickness=1.5, color=gold_color, spaceBefore=4, spaceAfter=8))

    # Title Banner
    elements.append(Paragraph("RAPPORT COMPLET DU PROJET KUSOR v3", title_style))
    elements.append(Paragraph("Plateforme d'Intelligence Réglementaire, GraphRAG & Audit de Conformité Bancaire BCT", subtitle_style))

    # Summary Box
    summary_text = """
    <b>KUSOR (Knowledge-Unified System for Official Regulations)</b> est une solution d'intelligence artificielle souveraine développée pour la Banque Centrale de Tunisie (BCT) et Attijari Bank. Elle combine un moteur <b>GraphRAG hybride</b>, une base de connaissances en graphe <b>Neo4j</b>, une base vectorielle <b>ChromaDB</b>, un modèle de langage local <b>Qwen 2.5</b>, et une suite d'applications d'audit de conformité (Crédit, AML/KYC, Contrats, Impact Réglementaire, Logique Déontique).
    """
    box_data = [[Paragraph(summary_text, body_style)]]
    box_table = Table(box_data, colWidths=[515])
    box_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FEF3C7")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#F59E0B")),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(box_table)
    elements.append(Spacer(1, 8))

    # ---------------------------------------------------------
    # 1. METRIQUES ET BASES DE DONNEES
    # ---------------------------------------------------------
    elements.append(Paragraph("1. Volume de Données & Métriques Opérationnelles", h1_style))
    
    metrics_data = [
        [
            Paragraph("Moteur de Stockage", table_header),
            Paragraph("Rôle dans le Système", table_header),
            Paragraph("Volume Actif", table_header),
            Paragraph("Statut Technique", table_header)
        ],
        [
            Paragraph("<b>PostgreSQL 16</b>", table_cell_bold),
            Paragraph("Métadonnées documents, utilisateurs, journalisation d'audit", table_cell),
            Paragraph("<b>118</b> circulaires<br/><b>1 358</b> chunks<br/><b>64</b> comptes", table_cell),
            Paragraph("<font color='#059669'><b>Opérationnel</b></font><br/>Indexé & Migré", table_cell)
        ],
        [
            Paragraph("<b>ChromaDB 1.5</b>", table_cell_bold),
            Paragraph("Base vectorielle dense (Embeddings 768d <i>nomic-embed-text</i>)", table_cell),
            Paragraph("<b>1 358</b> vecteurs actifs", table_cell),
            Paragraph("<font color='#059669'><b>Opérationnel</b></font><br/>Stockage /data persistant", table_cell)
        ],
        [
            Paragraph("<b>Neo4j 5.18</b>", table_cell_bold),
            Paragraph("Graphe de connaissances (abrogations, modifications, entités)", table_cell),
            Paragraph("<b>1 881</b> nœuds<br/><b>2 303</b> relations", table_cell),
            Paragraph("<font color='#059669'><b>Opérationnel</b></font><br/>Cypher APOC activé", table_cell)
        ],
        [
            Paragraph("<b>Piste d'Audit SHA-256</b>", table_cell_bold),
            Paragraph("Chaîne de blocs cryptographique pour la traçabilité des décisions", table_cell),
            Paragraph("<b>54</b> blocs certifiés", table_cell),
            Paragraph("<font color='#059669'><b>Intègre</b></font><br/>audit_chain.jsonl", table_cell)
        ]
    ]

    t_metrics = Table(metrics_data, colWidths=[95, 200, 110, 110])
    t_metrics.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t_metrics)
    elements.append(Spacer(1, 8))

    # ---------------------------------------------------------
    # 2. ARCHITECTURE TECHNIQUE & PIPELINE IA
    # ---------------------------------------------------------
    elements.append(Paragraph("2. Architecture GraphRAG Hybride & NLP", h1_style))
    
    rag_text = """
    Le moteur d'inférence de KUSOR repose sur une stratégie <b>Multi-Retrieval & Reranking</b> garantissant l'absence d'hallucinations :<br/>
    • <b>Recherche Hybride RRF (Reciprocal Rank Fusion) :</b> Combine la recherche sémantique dense (ChromaDB), la recherche lexicale exacte (BM25) et l'exploration de voisinage de graphe (Neo4j).<br/>
    • <b>Cross-Encoder Reranking :</b> Réordonnancement temps réel via <code>cross-encoder/ms-marco-MiniLM-L-6-v2</code> pour isoler les 5 fragments les plus pertinents.<br/>
    • <b>LangGraph Agent State Machine :</b> Classification automatique de l'intention utilisateur (Factuelle, Temporelle, Évaluation de risque, Audit de contrat) et routage dynamique vers les outils spécialisés.
    """
    elements.append(Paragraph(rag_text, body_style))
    elements.append(Spacer(1, 6))

    # ---------------------------------------------------------
    # 3. PANORAMA DES MODULES METIERS
    # ---------------------------------------------------------
    elements.append(Paragraph("3. Synthèse des Modules Métiers & Fonctionnalités", h1_style))

    modules_data = [
        [
            Paragraph("Module KUSOR", table_header),
            Paragraph("Normes Réglementaires BCT / Intention", table_header),
            Paragraph("Fonctions Clés & Garanties", table_header)
        ],
        [
            Paragraph("<b>1. Assistant IA GraphRAG</b>", table_cell_bold),
            Paragraph("Toutes circulaires BCT", table_cell),
            Paragraph("Réponses explicables, citations d'articles avec numéros de page, questions de suivi recommandées.", table_cell)
        ],
        [
            Paragraph("<b>2. Octroi de Crédit</b>", table_cell_bold),
            Paragraph("Circulaire BCT n° 2018-06", table_cell),
            Paragraph("Contrôle automatique du plafond d'endettement maximal de <b>40%</b>, vérification des pièces justificatives obligatoires.", table_cell)
        ],
        [
            Paragraph("<b>3. Screening AML / KYC</b>", table_cell_bold),
            Paragraph("Norme BCT 2017-08 & LCB-FT 2015-26", table_cell),
            Paragraph("Filtrage sanctions (OFAC, GAFI, UE, ONU), détection des Personnes Politiquement Exposées (PPE) et Bénéficiaires Effectifs (UBO).", table_cell)
        ],
        [
            Paragraph("<b>4. Audit de Contrats</b>", table_cell_bold),
            Paragraph("Code des obligations & contrats BCT", table_cell),
            Paragraph("Détection des clauses léonines, pénalités abusives, vérification de la transparence du TEG.", table_cell)
        ],
        [
            Paragraph("<b>5. Impact Réglementaire</b>", table_cell_bold),
            Paragraph("Graphe de propagation Neo4j", table_cell),
            Paragraph("Arbre de dépendance des risques : identifie les processus internes de la banque impactés par toute nouvelle circulaire.", table_cell)
        ],
        [
            Paragraph("<b>6. Explorateur Temporel</b>", table_cell_bold),
            Paragraph("Gestion du cycle de vie juridique", table_cell),
            Paragraph("Navigation rétroactive pour restituer le cadre légal exact applicable à une date passée précise.", table_cell)
        ],
        [
            Paragraph("<b>7. Logique Déontique</b>", table_cell_bold),
            Paragraph("Extraction sémantique fine", table_cell),
            Paragraph("Classification des obligations (DOIT), interdictions (INTERDIT) et permissions (PEUT) dans les textes BCT.", table_cell)
        ]
    ]

    t_modules = Table(modules_data, colWidths=[115, 140, 260])
    t_modules.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t_modules)
    elements.append(Spacer(1, 8))

    # ---------------------------------------------------------
    # 4. SYSTEME D'AUTOMATISATION & ALERTES n8n
    # ---------------------------------------------------------
    elements.append(Paragraph("4. Automatisation de Veille & Notifications n8n", h1_style))
    
    notif_text = """
    KUSOR intègre une suite de workflows d'orchestration <b>n8n</b> reliés aux webhooks du backend :<br/>
    • <b>Alerte Immédiate Haute Sévérité (CRITICAL / HIGH) :</b> Dès qu'une nouvelle circulaire modifie des processus critiques, un webhook déclenche l'envoi instantané d'un email d'alerte rouge à la Direction de la Conformité.<br/>
    • <b>Veille Quotidienne & Synchronisation GAFI (7h00) :</b> Rapport matinal consolidé validant la fraîcheur des listes OFAC, UE, ONU et des publications BCT.<br/>
    • <b>Digest Hebdomadaire :</b> Synthèse analytique transmise au Comité de Risques et d'Audit.
    """
    elements.append(Paragraph(notif_text, body_style))
    elements.append(Spacer(1, 6))

    # ---------------------------------------------------------
    # 5. SOUVERAINETE ET SECURITE
    # ---------------------------------------------------------
    elements.append(Paragraph("5. Sécurité, Souveraineté & Piste d'Audit", h1_style))
    
    sec_data = [
        [
            Paragraph("<b>Souveraineté des Données</b>", table_cell_bold),
            Paragraph("Exécution 100% sur site (On-Premise) via conteneurs Docker et Ollama local. Aucun transfert de données bancaires vers des API tierces.", table_cell)
        ],
        [
            Paragraph("<b>Bouclier PII (Anonymisation)</b>", table_cell_bold),
            Paragraph("Masquage automatique préalable des identifiants (CIN, Passeport, RIB, Noms) avant tout traitement par le modèle de langage.", table_cell)
        ],
        [
            Paragraph("<b>Piste d'Audit Immuable</b>", table_cell_bold),
            Paragraph("Scellement SHA-256 séquentiel de chaque audit et interrogation RAG dans <code>backend/data/audit_chain.jsonl</code> pour l'inspection générale.", table_cell)
        ]
    ]
    t_sec = Table(sec_data, colWidths=[140, 375])
    t_sec.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_sec)
    elements.append(Spacer(1, 10))

    # ---------------------------------------------------------
    # SIGNATURE / AUDIT STAMP
    # ---------------------------------------------------------
    stamp_data = [
        [
            Paragraph("<b>CERTIFICATION TECHNIQUE DU SYSTÈME</b><br/><font size=7 color='#64748B'>Moteur KUSOR v3 validé pour l'environnement de production bancaire.</font>", table_cell),
            Paragraph("<b>DIRECTION DE LA CONFORMITÉ</b><br/><font size=7 color='#059669'>✓ Document certifié & archivé</font>", ParagraphStyle('RightSign', parent=table_cell, alignment=2))
        ]
    ]
    t_stamp = Table(stamp_data, colWidths=[260, 255])
    t_stamp.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(KeepTogether(t_stamp))

    # Build Document
    doc.build(elements, canvasmaker=NumberedCanvas)
    print(f"✓ PDF generated successfully at: {filename}")

if __name__ == "__main__":
    out_dir = "/home/nour/kusor/frontend/kusor-ui/dist/kusor-ui/browser"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "rapport_kusor.pdf")
    build_pdf(out_path)
    
    pub_dir = "/home/nour/kusor/frontend/kusor-ui/public"
    os.makedirs(pub_dir, exist_ok=True)
    build_pdf(os.path.join(pub_dir, "rapport_kusor.pdf"))

    root_path = "/home/nour/kusor/rapport_complet_kusor.pdf"
    build_pdf(root_path)
