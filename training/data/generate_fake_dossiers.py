# training/data/generate_fake_dossiers.py
"""
Generates realistic, formatted Tunisian banking and compliance test dossiers in PDF format using PyMuPDF.
Produces:
1. training/data/fake_dossiers/kyc_individuel/ (fake_cin.pdf, fake_salary_slip.pdf, fake_proof_of_address.pdf)
2. training/data/fake_dossiers/credit_hypothecaire/ (fake_cin.pdf, fake_salary_slip_1..3.pdf, fake_property_valuation.pdf, fake_sale_agreement.pdf)
3. training/data/fake_dossiers/contract_credit/ (fake_credit_contract.pdf)
"""

import os
import fitz  # PyMuPDF


def create_pdf(filepath: str, title: str, lines: list[str], header_color=(0.91, 0.36, 0.02)):
    """Helper to create a visually styled, structured banking PDF document."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4

    # Draw Top Header Banner
    page.draw_rect(fitz.Rect(0, 0, 595, 75), color=header_color, fill=header_color)
    page.insert_text(fitz.Point(35, 45), "ATTIJARI BANK TUNISIA — DOSSIER CLIENT", fontsize=15, color=(1, 1, 1), fontname="helv")
    page.insert_text(fitz.Point(35, 60), "Conformité & Intelligence Réglementaire BCT", fontsize=9, color=(0.95, 0.95, 0.95), fontname="helv")

    # Document Title
    page.insert_text(fitz.Point(35, 110), title, fontsize=14, color=(0.1, 0.1, 0.1), fontname="helv")
    page.draw_line(fitz.Point(35, 118), fitz.Point(560, 118), color=(0.8, 0.8, 0.8), width=1)

    # Document Content Lines
    y = 145
    for line in lines:
        if line.startswith("###"):
            y += 10
            page.insert_text(fitz.Point(35, y), line.replace("###", "").strip(), fontsize=11, color=(0.91, 0.36, 0.02), fontname="helv")
            y += 16
        elif ":" in line:
            parts = line.split(":", 1)
            page.insert_text(fitz.Point(35, y), parts[0] + " :", fontsize=10, color=(0.2, 0.2, 0.2), fontname="helv")
            page.insert_text(fitz.Point(200, y), parts[1].strip(), fontsize=10, color=(0.0, 0.0, 0.0), fontname="helv")
            y += 18
        else:
            page.insert_text(fitz.Point(35, y), line, fontsize=9.5, color=(0.15, 0.15, 0.15), fontname="helv")
            y += 16

    # Draw Footer
    page.draw_line(fitz.Point(35, 800), fitz.Point(560, 800), color=(0.85, 0.85, 0.85), width=0.8)
    page.insert_text(fitz.Point(35, 815), "Document généré pour banc d'essai réglementaire KUSOR v3 — Strictement confidentiel", fontsize=8, color=(0.5, 0.5, 0.5), fontname="helv")

    doc.save(filepath)
    doc.close()
    print(f"Generated: {filepath}")


def generate_all_dossiers(base_dir="training/data/fake_dossiers"):
    # ── 1. KYC Individuel Dossier ──────────────────────────────────
    kyc_dir = os.path.join(base_dir, "kyc_individuel")
    
    create_pdf(
        os.path.join(kyc_dir, "fake_cin.pdf"),
        "RÉPUBLIQUE TUNISIENNE — CARTE NATIONALE D'IDENTITÉ",
        [
            "### INFORMATIONS D'IDENTITÉ CIVILE",
            "Titulaire : Mohamed Ben Salem",
            "Numéro CIN : 12345678",
            "Date de naissance : 15/03/1985",
            "Lieu de naissance : Tunis, Tunisie",
            "Nationalité : Tunisienne",
            "Profession : Ingénieur d'Affaires",
            "Adresse : 12 Rue de la Liberté, Tunis 1001",
            "Délivrée le : 10/01/2017",
            "Expire le : 10/01/2027",
            "Statut du document : Valide et certifié conforme",
        ],
    )

    create_pdf(
        os.path.join(kyc_dir, "fake_salary_slip.pdf"),
        "BULLETIN DE PAIE MENSUEL — SALARIÉ",
        [
            "### INFORMATIONS EMPLOYEUR & SALARIÉ",
            "Employeur : Société Tunisienne de Services SARL",
            "Matricule Fiscal : 1245789/A/M/000",
            "Salarié : Mohamed Ben Salem",
            "CIN : 12345678",
            "Poste / Qualification : Ingénieur Principal",
            "Période : Juillet 2026",
            "### DÉCOMPTE DES RÉMUNÉRATIONS",
            "Salaire Brut : 3 650,000 TND",
            "Cotisations CNSS (9.18%) : 335,070 TND",
            "Impôt sur le Revenu (IRPP) : 514,930 TND",
            "Salaire Net à payer : 2 800,000 TND",
            "Mode de règlement : Virement bancaire direct",
        ],
    )

    create_pdf(
        os.path.join(kyc_dir, "fake_proof_of_address.pdf"),
        "STEG — FACTURE D'ÉLECTRICITÉ & GAZ (JUSTIFICATIF DE DOMICILE)",
        [
            "### COORDONNÉES DU TITULAIRE DU COMPTEUR",
            "Client / Titulaire : Mohamed Ben Salem",
            "Référence Contrat STEG : 987456123",
            "Adresse : 12 Rue de la Liberté, Tunis 1001",
            "Date de facture : 05/08/2026",
            "Période de consommation : Mai 2026 - Juillet 2026",
            "Montant total TTC : 148,500 TND",
            "Statut de la facture : Payée",
        ],
    )

    # ── 2. Crédit Hypothécaire Dossier ──────────────────────────────
    credit_dir = os.path.join(base_dir, "credit_hypothecaire")

    create_pdf(
        os.path.join(credit_dir, "fake_cin.pdf"),
        "RÉPUBLIQUE TUNISIENNE — CARTE NATIONALE D'IDENTITÉ",
        [
            "### INFORMATIONS D'IDENTITÉ CIVILE",
            "Titulaire : Mohamed Ben Salem",
            "Numéro CIN : 12345678",
            "Date de naissance : 15/03/1985",
            "Profession : Ingénieur Principal",
            "Adresse : 12 Rue de la Liberté, Tunis 1001",
            "Expire le : 10/01/2027",
        ],
    )

    for i, month in enumerate(["Mai 2026", "Juin 2026", "Juillet 2026"], 1):
        create_pdf(
            os.path.join(credit_dir, f"fake_salary_slip_{i}.pdf"),
            f"BULLETIN DE SALAIRE N° {i} — {month.upper()}",
            [
                "### DONNÉES DE RÉMUNÉRATION",
                "Employeur : Société Tunisienne de Services SARL",
                "Salarié : Mohamed Ben Salem",
                "CIN : 12345678",
                f"Période : {month}",
                "Salaire Brut : 3 650,000 TND",
                "Salaire Net à payer : 2 800,000 TND",
            ],
        )

    create_pdf(
        os.path.join(credit_dir, "fake_property_valuation.pdf"),
        "RAPPORT D'EXPERTISE IMMOBILIÈRE — ÉVALUATION VÉNALE",
        [
            "### DONNÉES D'EXPERTISE DU BIEN",
            "Cabinet d'expertise : Cabinet Tunisien d'Expertise Foncière",
            "Expert Agréé : Maître Ridha Mansouri (Agréé BCT)",
            "Situation du bien : 45 Avenue Habib Bourguiba, La Marsa",
            "Nature du bien : Appartement Haut Standing S+3",
            "Superficie totale : 165 m2",
            "Valeur Vénale Estimée : 320 000,000 TND",
            "Date d'expertise : 01/08/2026",
            "Titre foncier N° : 15487/Tunis",
            "Conclusion : Bien en excellent état, hypothèque de premier rang recommandée.",
        ],
    )

    create_pdf(
        os.path.join(credit_dir, "fake_sale_agreement.pdf"),
        "PROMESSE SYNALLAGMATIQUE DE VENTE (COMPROMIS DE VENTE)",
        [
            "### CLAUSES DU COMPROMIS DE VENTE IMMOBILIÈRE",
            "Vendeur : M. Slimane Ben Khelil (CIN 04561238)",
            "Acquéreur : M. Mohamed Ben Salem (CIN 12345678)",
            "Désignation du bien : Appartement S+3 sis à 45 Avenue Habib Bourguiba, La Marsa",
            "Prix de vente convenu : 310 000,000 TND",
            "Avance versée : 30 000,000 TND",
            "Solde à financer par crédit bancaire : 150 000,000 TND",
            "Condition suspensive : Obtention d'un prêt bancaire auprès d'Attijari Bank Tunisia",
            "Fait le : 15/07/2026",
        ],
    )

    # ── 3. Contrat de Crédit ─────────────────────────────────────────
    contract_dir = os.path.join(base_dir, "contract_credit")

    create_pdf(
        os.path.join(contract_dir, "fake_credit_contract.pdf"),
        "CONVENTION DE CRÉDIT IMMOBILIER PARTICULIER",
        [
            "### CONDITIONS PARTICULIÈRES DU CONTRAT",
            "Prêteur : Attijari Bank Tunisia",
            "Emprunteur : M. Mohamed Ben Salem (CIN 12345678)",
            "Montant du prêt : 150 000,000 TND",
            "Durée : 240 mois (20 ans)",
            "Taux d'intérêt : 7.50% l'an (Fixe)",
            "Date de signature : 15/01/2019",
            "### CLAUSES CONTRACTUELLES ET DISPOSITIONS GÉNÉRALES",
            "Article 1 : Objet du crédit — Le prêt est consenti exclusivement pour l'acquisition du bien immobilier à La Marsa.",
            "Article 2 : Taux d'intérêt et Révision — Les intérêts sont calculés sur le capital restant dû au taux nominal de 7.50%.",
            "Article 3 : Remboursement anticipé — L'emprunteur peut rembourser par anticipation sans indemnité supérieure à 2 mois d'intérêts selon la Circulaire BCT N° 2016-01.",
            "Article 4 : Garantie et Hypothèque — Inscription d'hypothèque de 1er rang sur le titre foncier 15487/Tunis au profit de la banque.",
            "Article 5 : Résiliation et Déchéance du terme — En cas de défaut de paiement de 3 échéances consécutives, la banque exigera le remboursement intégral.",
            "Article 6 : Juridiction compétente — Tout litige relatif au présent contrat sera soumis aux tribunaux de Tunis.",
        ],
    )

    print("\n✅ All 3 synthetic banking dossiers successfully generated in:", base_dir)


if __name__ == "__main__":
    generate_all_dossiers()
