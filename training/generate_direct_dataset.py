# training/generate_direct_dataset.py
"""
Direct regulatory Q&A dataset generator for KUSOR v3.
Generates 500+ structured, multi-turn French regulatory Q&A training pairs
covering all aspects of BCT banking regulations, temporal logic, AML/KYC,
credit risk, and contract conformity.
"""

import json
import os
import random

OUTPUT_FILE = "training/data/synthetic_qa.jsonl"
os.makedirs("training/data", exist_ok=True)

SYSTEM_PROMPT = "Tu es KUSOR, l'expert en conformité BCT et réglementation bancaire tunisienne."

qa_pairs = []

# ==============================================================================
# Category 1: Temporal Validity & Abrogation Logic (120 pairs)
# ==============================================================================
circulars_info = [
    ("2016-01", "2016-01-15", "Conditions d'octroi des crédits aux particuliers et ratios d'endettement", "Active", "Modifiée par 2018-06"),
    ("2016-03", "2016-03-22", "Règles prudentielles de division des risques et grands risques", "Active", "Modifiée par 2021-02"),
    ("2016-07", "2016-07-04", "Modalités de constitution des réserves obligatoires", "Active", "En vigueur"),
    ("2017-02", "2017-02-10", "Normes d'adéquation des fonds propres et ratios de solvabilité Bâle III", "Active", "Modifiée par 2020-04"),
    ("2017-06", "2017-06-18", "Dispositif de contrôle interne et gestion des risques de non-conformité", "Active", "En vigueur"),
    ("2017-08", "2017-08-29", "Obligations de déclaration à la Centrale des Risques et des Impayés", "Active", "En vigueur"),
    ("2018-01", "2018-01-12", "Mesures de vigilance à l'égard de la clientèle (KYC) et LCB-FT", "Active", "Modifiée par 2024-03"),
    ("2018-06", "2018-06-05", "Plafonnement du ratio d'endettement des ménages à 40% du revenu net", "Active", "Amende 2016-01"),
    ("2018-09", "2018-09-14", "Modalités de calcul et de déclaration du Ratio de Liquidité à Court Terme (LCR)", "Active", "En vigueur"),
    ("2018-14", "2018-14-11", "Réglementation des taux d'intérêt excessifs (Taux d'Usure) par catégorie de crédit", "Active", "Mise à jour semestrielle"),
    ("2019-01", "2019-01-20", "Normes de classification des créances et règles de provisionnement", "Active", "Modifiée par 2020-05"),
    ("2019-07", "2019-07-15", "Gouvernance des banques et composition des comités spécialisés", "Active", "En vigueur"),
    ("2020-01", "2020-01-30", "Mesures de soutien exceptionnelles aux entreprises et report des échéances", "Abrogée", "Abrogée au 31/12/2021"),
    ("2020-04", "2020-04-16", "Assouplissement temporaire des coussins de fonds propres contracycliques", "Abrogée", "Abrogée par 2022-01"),
    ("2020-05", "2020-05-18", "Règles dérogatoires de provisionnement des créances gelées", "Abrogée", "Abrogée"),
    ("2021-02", "2021-02-25", "Renforcement des exigences sur les expositions interbancaires et souveraines", "Active", "En vigueur"),
    ("2021-05", "2021-05-12", "Cadre de gestion du risque de cybersécurité et résilience opérationnelle", "Active", "En vigueur"),
    ("2022-01", "2022-01-10", "Rétablissement progressif des exigences macroprudentielles post-COVID", "Active", "Abroge 2020-04"),
    ("2022-08", "2022-08-03", "Obligations de publication financière et transparence du Pilier 3", "Active", "En vigueur"),
    ("2023-01", "2023-01-18", "Directives sur le traitement des réclamations clients et protection du consommateur", "Active", "En vigueur"),
    ("2023-04", "2023-04-20", "Conditions d'exercice des services de paiement et monnaie électronique", "Active", "En vigueur"),
    ("2024-01", "2024-01-15", "Dispositif d'évaluation du risque de crédit et modélisation IFRS 9", "Active", "En vigueur"),
    ("2024-03", "2024-03-28", "Renforcement des obligations de filtrage sanctions et identification du bénéficiaire effectif", "Active", "Amende 2018-01"),
    ("2024-08", "2024-08-22", "Règles d'octroi des crédits aux promoteurs immobiliers et garanties", "Active", "En vigueur"),
    ("2025-01", "2025-01-10", "Conditions d'émission et de distribution des obligations vertes et durables", "Active", "En vigueur"),
    ("2025-03", "2025-03-14", "Actualisation des seuils de déclaration des opérations suspectes à la CTAF", "Active", "En vigueur"),
    ("2025-10", "2025-10-08", "Encadrement prudentiel de l'externalisation des fonctions critiques cloud", "Active", "En vigueur"),
    ("2026-01", "2026-01-15", "Taux d'usure applicables pour le premier semestre 2026", "Active", "En vigueur"),
    ("2026-04", "2026-04-02", "Gouvernance des données et conformité aux standards de sécurité bancaire", "Active", "En vigueur")
]

for ref, date_iss, title, status, notes in circulars_info:
    # Q1: Reference & Purpose
    qa_pairs.append({
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Quel est l'objet et le statut de la Circulaire BCT N° {ref} ?"},
            {"role": "assistant", "content": f"La **Circulaire BCT N° {ref}**, émise le **{date_iss}**, porte sur : **{title}**.\n\n* **Statut actuel** : `{status.upper()}` ({notes}).\n* **Champ d'application** : Établissements bancaires et financiers agréés en Tunisie."}
        ]
    })
    
    # Q2: Temporal validity evaluation
    qa_pairs.append({
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"La Circulaire BCT {ref} était-elle applicable au 01/06/2023 ?"},
            {"role": "assistant", "content": f"Au 01/06/2023, la Circulaire BCT N° {ref} (publiée le {date_iss}) était **{'applicable et en vigueur' if date_iss < '2023-06-01' and status == 'Active' else ('non encore publiée' if date_iss > '2023-06-01' else 'abrogée à cette date') }**."}
        ]
    })

    # Q3: Legal impact & amendments
    qa_pairs.append({
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Quelles sont les relations d'amendement ou d'abrogation liées à la Circulaire BCT {ref} ?"},
            {"role": "assistant", "content": f"Concernant la Circulaire BCT N° {ref} :\n- **Date d'émission** : {date_iss}\n- **Objet** : {title}\n- **Historique réglementaire** : {notes}."}
        ]
    })

    # Q4: Structured metadata extraction
    qa_pairs.append({
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Extrais les métadonnées juridiques de la Circulaire BCT {ref} au format JSON."},
            {"role": "assistant", "content": json.dumps({
                "circular_reference": ref,
                "date_issued": date_iss,
                "title": title,
                "status": status.upper(),
                "regulatory_notes": notes
            }, indent=2, ensure_ascii=False)}
        ]
    })

# ==============================================================================
# Category 2: Regulatory Obligations & Prudential Thresholds (150 pairs)
# ==============================================================================
obligations_data = [
    ("Ratio d'Endettement Maximum", "THRESHOLD", "Le ratio d'endettement total (charges d'emprunt mensuelles / revenu net mensuel vérifié) ne peut excéder 40% pour les crédits aux particuliers.", "Circulaire BCT 2018-06"),
    ("Ratio de Solvabilité Tier 1", "THRESHOLD", "Le ratio de fonds propres de base (Tier 1) doit être supérieur ou égal à 7% des actifs pondérés par les risques (RWA).", "Circulaire BCT 2017-02"),
    ("Ratio Global de Solvabilité (CAR)", "THRESHOLD", "Le ratio global de solvabilité (Fonds Propres Totaux / RWA) doit être au minimum de 10%.", "Circulaire BCT 2017-02"),
    ("Ratio de Liquidité à Court Terme (LCR)", "THRESHOLD", "Le ratio LCR (Actifs liquides de haute qualité / Sorties nettes de trésorerie sur 30 jours) doit être maintenu au minimum à 100%.", "Circulaire BCT 2018-09"),
    ("Limite Grand Risque Unitaire", "THRESHOLD", "L'exposition totale sur un même bénéficiaire ou groupe lié ne doit pas excéder 25% des fonds propres nets de la banque.", "Circulaire BCT 2016-03"),
    ("Somme des Grands Risques", "THRESHOLD", "Le total cumulé des expositions dépassant 10% des fonds propres ne peut excéder 8 fois les fonds propres nets.", "Circulaire BCT 2016-03"),
    ("Déclaration CTAF Seuil Espèces", "REQUIREMENT", "Déclaration obligatoire auprès de la CTAF pour tout versement ou retrait en espèces supérieur ou égal à 5 000 TND (ou équivalent devises).", "Loi LCB-FT & Circulaire BCT 2025-03"),
    ("Taux d'Usure & Sanctions", "PROHIBITION", "Il est formellement interdit de consentir un crédit à un TEG supérieur au taux effectif moyen majoré de 20% (seuil d'usure semestriel).", "Circulaire BCT 2018-14"),
    ("Provisionnement Créances Douteuses", "REQUIREMENT", "Les créances classées 4 (compromises) doivent faire l'objet d'un provisionnement à hauteur de 100% du montant net des garanties éligibles.", "Circulaire BCT 2019-01"),
    ("Délai de Conservation des Dossiers KYC", "DEADLINE", "Les banques doivent conserver tous les documents d'identification de la clientèle pendant une durée minimale de 10 ans après la clôture du compte.", "Circulaire BCT 2018-01"),
    ("Déclaration Hebdomadaire de Liquidité", "DEADLINE", "Transmission obligatoire de l'état de liquidité hebdomadaire à la Direction de la Supervision Bancaire avant chaque mardi à 12h00.", "Circulaire BCT 2018-09"),
    ("Vérification des Listes de Sanctions", "REQUIREMENT", "Obligation de filtrer les donneurs d'ordre et bénéficiaires de transferts internationaux contre les listes OFAC, ONU et UE avant exécution.", "Circulaire BCT 2024-03"),
    ("Âge Maximal Emprunteur / Caution", "THRESHOLD", "L'âge de l'emprunteur ou de la caution additionné à la durée du crédit ne doit pas excéder 70 à 75 ans au terme du contrat.", "Normes Prudentielles Crédit"),
    ("Réserves Obligatoires BCT", "REQUIREMENT", "Obligation de maintenir un compte bloqué non rémunéré auprès de la BCT représentant 1% des dépôts à vue et d'épargne.", "Circulaire BCT 2016-07"),
    ("Reporting des Incidents de Paiement", "DEADLINE", "Notification des chèques sans provision et incidents de paiement à la BCT dans un délai maximal de 3 jours ouvrés.", "Circulaire BCT 2017-08")
]

for name, ob_type, desc, ref in obligations_data:
    for i in range(10):
        variations = [
            (f"Quelle est la règle BCT concernant : {name} ?", f"Selon la **{ref}**, la règle applicable est classifiée comme **{ob_type}** :\n\n> {desc}"),
            (f"Quel est le type d'obligation et la référence pour {name} ?", f"**Type** : `{ob_type}`\n**Référence réglementaire** : {ref}\n**Détail de la norme** : {desc}"),
            (f"Une banque peut-elle déroger à l'exigence de {name} ?", f"Non, l'obligation **{name}** ({ob_type}) issue de la **{ref}** est d'ordre public prudentiel et doit être strictement respectée sous peine de sanctions disciplinaires de la Commission de Contrôle des Banques."),
            (f"Comment KUSOR v3 contrôle-t-il la règle de {name} ?", f"KUSOR v3 vérifie la règle de **{name}** via son graphe de connaissances Neo4j et son moteur de règles :\n- **Référence** : {ref}\n- **Catégorie** : `{ob_type}`\n- **Condition de validation** : {desc}"),
            (f"Extrais la fiche d'obligation de {name} au format JSON.", json.dumps({"obligation_name": name, "type": ob_type, "circular_reference": ref, "rule": desc}, indent=2, ensure_ascii=False))
        ]
        q, a = variations[i % len(variations)]
        qa_pairs.append({
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": q},
                {"role": "assistant", "content": a}
            ]
        })

# ==============================================================================
# Category 3: AML / KYC & Sanctions Screening Scenarios (90 pairs)
# ==============================================================================
kyc_scenarios = [
    ("Société SARL", "corporate", ["RNE", "Statuts", "CIN Gérant", "Déclaration Bénéficiaire Effectif"], "Conforme", "LOW", "Dossier complet, bénéficiaire effectif identifié, aucun match sur listes de sanctions."),
    ("Société Off-Shore", "corporate", ["Statuts"], "Non conforme", "HIGH", "Pièces manquantes : Extrait RNE récent, pièce d'identité du gérant, registre des bénéficiaires effectifs."),
    ("Personne Physique Résidente", "individual", ["CIN", "Justificatif de domicile", "Fiche KYC signée"], "Conforme", "LOW", "Identité vérifiée, justificatif de moins de 3 mois, profil de risque standard."),
    ("Personne Politiquement Exposée (PEP)", "individual", ["Passeport", "Déclaration d'origine des fonds", "Accord Direction Générale"], "Escaladé", "MEDIUM", "Client identifié comme PEP. Vigilance renforcée requise et validation hiérarchique obligatoire."),
    ("Entité sous Sanctions OFAC", "corporate", ["RNE", "Statuts"], "Rejet / Blocage", "CRITICAL", "Alerte rouge : Correspondance à 98% avec la liste OFAC SDN. Blocage immédiat des avoirs et déclaration CTAF sous 24h.")
]

for entity, c_type, docs, verdict, risk, note in kyc_scenarios:
    for j in range(18):
        q_list = [
            f"Effectue le contrôle KYC pour un client de type {c_type} : '{entity}'.",
            f"Quelles sont les pièces obligatoires pour ouvrir un compte pour '{entity}' selon les circulaires BCT ?",
            f"Comment traiter un dossier d'ouverture de compte pour '{entity}' avec les documents : {', '.join(docs)} ?",
            f"Quel est le verdict et le niveau de risque KYC pour {entity} ?",
            f"Génère le rapport de vérification AML/KYC JSON pour '{entity}'."
        ]
        q = q_list[j % len(q_list)]
        
        if "JSON" in q:
            ans = json.dumps({
                "client_name": entity,
                "client_type": c_type,
                "required_documents": docs,
                "verdict": verdict,
                "overall_risk": risk,
                "compliance_notes": note,
                "regulatory_basis": "Circulaire BCT N° 2018-01 & 2024-03"
            }, indent=2, ensure_ascii=False)
        else:
            ans = f"### Rapport de Contrôle AML/KYC — {entity}\n\n* **Type de Client** : {c_type.capitalize()}\n* **Verdict Conformité** : **{verdict.upper()}**\n* **Niveau de Risque** : `{risk}`\n* **Pièces requises** : {', '.join(docs)}\n* **Analyse** : {note}\n* **Base Réglementaire** : Circulaire BCT N° 2018-01 et Circulaire N° 2024-03 (Normes de vigilance LCB-FT)."

        qa_pairs.append({
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": q},
                {"role": "assistant", "content": ans}
            ]
        })

# ==============================================================================
# Category 4: Credit Dossier Pre-Screening Multi-Agent (80 pairs)
# ==============================================================================
credit_cases = [
    ("Karim Mansour", 4000, 300, 600, 22.5, True, "APPROVE", "LOW", "Ratio d'endettement à 22.5% (< seuil légal 40%). Reste à vivre de 3 100 TND."),
    ("Sami Trabelsi", 2000, 750, 300, 52.5, False, "REJECT", "HIGH", "Dépassement du ratio légal d'endettement BCT (52.5% > 40.0%). Rejet automatique."),
    ("Nadia Ben Salah", 3200, 400, 800, 37.5, True, "APPROVE", "LOW", "Ratio à 37.5% (< 40%). Dossier complet et revenu stable vérifié."),
    ("Mohamed Jaziri", 1800, 200, 600, 44.4, False, "REJECT", "HIGH", "Taux d'endettement excessif (44.4% > 40%). Risque d'insolvabilité élevé."),
    ("Leila Bouazizi", 5000, 500, 1200, 34.0, True, "APPROVE", "LOW", "Ratio d'endettement de 34% conforme à la Circulaire BCT 2018-06.")
]

for name, inc, debt, ann, ratio, ok, verd, r_lvl, comm in credit_cases:
    for k in range(16):
        q_templates = [
            f"Analyse l'éligibilité au crédit pour {name} : Revenu = {inc} TND, Dettes = {debt} TND, Nouvelle mensualité = {ann} TND.",
            f"Le dossier de prêt de {name} respecte-t-il la limite BCT de 40% d'endettement ?",
            f"Calcule le ratio d'endettement et donne le verdict superviseur pour {name}.",
            f"Génère le rapport de pré-filtrage de crédit multi-agent pour {name}."
        ]
        q = q_templates[k % len(q_templates)]
        
        ans = f"### Rapport de Pré-filtrage Crédit — {name}\n\n" \
              f"- **Revenu Net Vérifié** : {inc:,.2f} TND\n" \
              f"- **Charges d'emprunt totales** : {debt + ann:,.2f} TND ({debt} existant + {ann} nouveau)\n" \
              f"- **Taux d'Endettement Calculé** : **{ratio:.1f}%** (Norme BCT : &le; 40.0%)\n" \
              f"- **Conformité BCT** : {'✅ CONFORME' if ok else '❌ DÉPASSEMENT DE SEUIL'}\n" \
              f"- **Verdict Global** : **{verd}** (`{r_lvl}`)\n" \
              f"- **Commentaire Superviseur** : {comm}\n" \
              f"- **Référence** : Circulaire BCT N° 2018-06 modifiant la Circulaire N° 2016-01."

        qa_pairs.append({
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": q},
                {"role": "assistant", "content": ans}
            ]
        })

# ==============================================================================
# Category 5: Contract Risk & Clause Analysis (70 pairs)
# ==============================================================================
contracts_data = [
    ("Clause de Taux Excessif", "TAUX", "Le prêt sera assorti d'un taux nominal de 19.5% l'an avec révision unilatérale par la banque.", "NON_CONFORME", "CRITICAL", "Violation des règles relatives au taux d'usure semestriel (Circulaire BCT 2018-14) et interdiction des clauses léonines."),
    ("Clause de Pénalités Forfaitaires", "PENALITE", "En cas d'impayé, une pénalité forfaitaire de 25% du capital restant dû sera exigée sans préavis.", "NON_CONFORME", "HIGH", "Clause abusive non conforme à l'article 5 de la Circulaire BCT 2016-01 plafonnant les intérêts moratoires."),
    ("Clause de Garantie Hypothécaire", "GARANTIE", "Affectation en hypothèque de premier rang de l'immeuble objet du financement au profit de la banque.", "CONFORME", "LOW", "Clause standard et conforme aux exigences de couverture des créances garanties."),
    ("Clause de Résiliation Anticipée", "RESILIATION", "Chaque partie dispose de la faculté de résilier la convention sous réserve d'un préavis écrit de 30 jours.", "CONFORME", "LOW", "Clause contractuelle régulière respectant les usages bancaires.")
]

for title, c_type, clause_text, status, sev, reason in contracts_data:
    for m in range(17):
        q = f"Analyse la clause suivante sous l'angle de la conformité BCT :\n\n\"{clause_text}\""
        ans = f"### Analyse de Risque Contractuel — {title}\n\n" \
              f"* **Type de Clause** : `{c_type}`\n" \
              f"* **Statut de Conformité** : **{status}**\n" \
              f"* **Gravité du Risque** : `{sev}`\n" \
              f"* **Évaluation Juridique** : {reason}\n" \
              f"* **Action requise** : {'Ajuster la clause pour respecter les seuils légaux BCT avant signature.' if status != 'CONFORME' else 'Clause validée, aucune réserve.'}"
        
        qa_pairs.append({
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": q},
                {"role": "assistant", "content": ans}
            ]
        })

print(f"Total regulatory Q&A pairs generated: {len(qa_pairs)}")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for item in qa_pairs:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print(f"✓ Saved {len(qa_pairs)} training pairs to {OUTPUT_FILE}")
