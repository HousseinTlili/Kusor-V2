import json
import os
from datetime import datetime

names = ["Ben Salah Mohamed", "Trabelsi Fatma", "Chtioui Karim", "Belhaj Sonia", "Gharbi Ahmed", 
         "Mansouri Leila", "Hammami Riadh", "Jebali Amira", "Bouazizi Taoufik", "Mahjoub Nadia",
         "Karray Youssef", "Miled Salma", "Rekik Amina", "Sassi Walid", "Frikha Hedi",
         "Gargouri Imen", "Zouari Nizar", "Chaabane Rym", "Ellouze Omar", "Khemiri Asma",
         "Ayari Sami", "Boussetta Hela", "Daoud Skander", "Jendoubi Yassine", "Ghazouani Wafa",
         "Mabrouk anis", "Cherif Ines", "Ghannouchi Tarek", "Haddad Safa", "Kacem Zied",
         "Ben Ali Sami", "Ayadi Fares", "Gharbi Amine", "Trabelsi Omar", "Jemai Sami"]

kyc_cases = []

def get_kyc_docs(c_type, missing=None, expired=None):
    docs = []
    if c_type == "Individuel":
        req = [
            ("cin_valide", "Carte d'Identité Nationale"),
            ("justificatif_domicile", "Justificatif de domicile"),
            ("bulletin_salaire", "Bulletin de salaire"),
            ("specimen_signature", "Spécimen de signature")
        ]
    elif c_type == "Corporate":
        req = [
            ("rne", "Extrait RNE"),
            ("statuts_societe", "Statuts de la société"),
            ("liste_beneficiaires_effectifs", "Liste des bénéficiaires effectifs"),
            ("pv_nomination_signataires", "PV de nomination des signataires")
        ]
    else: # PPE
        req = [
            ("declaration_statut_ppe", "Déclaration de statut PPE"),
            ("justificatif_fonction", "Justificatif de fonction"),
            ("declaration_detaillee_origine_fonds", "Déclaration détaillée d'origine des fonds"),
            ("validation_renforcee_hierarchie", "Validation renforcée par la hiérarchie")
        ]
        
    for code, name in req:
        if code == missing:
            docs.append({"code": code, "name": name, "present": False, "expired": False, "expiry_date": None})
        elif code == expired:
            docs.append({"code": code, "name": name, "present": True, "expired": True, "expiry_date": "2023-01-01"})
        else:
            docs.append({"code": code, "name": name, "present": True, "expired": False, "expiry_date": "2028-01-01"})
    return docs

# 10 Conforme
for i in range(4):
    kyc_cases.append({
        "dossier_id": f"KYC-2026-{len(kyc_cases)+1:03d}",
        "client_type": "Individuel",
        "client_name": names[len(kyc_cases)],
        "deposit_amount_tnd": 10000,
        "documents_provided": get_kyc_docs("Individuel"),
        "sanctions_match": False,
        "sanctions_matched_list": None,
        "expected_result": "Conforme",
        "justification": "Tous les documents obligatoires sont présents et valides."
    })
for i in range(4):
    kyc_cases.append({
        "dossier_id": f"KYC-2026-{len(kyc_cases)+1:03d}",
        "client_type": "Corporate",
        "client_name": names[len(kyc_cases)],
        "deposit_amount_tnd": 20000,
        "documents_provided": get_kyc_docs("Corporate"),
        "sanctions_match": False,
        "sanctions_matched_list": None,
        "expected_result": "Conforme",
        "justification": "Dossier entreprise complet et conforme."
    })
for i in range(2):
    kyc_cases.append({
        "dossier_id": f"KYC-2026-{len(kyc_cases)+1:03d}",
        "client_type": "PPE",
        "client_name": names[len(kyc_cases)],
        "deposit_amount_tnd": 30000,
        "documents_provided": get_kyc_docs("PPE"),
        "sanctions_match": False,
        "sanctions_matched_list": None,
        "expected_result": "Conforme",
        "justification": "Dossier PPE complet avec validation renforcée."
    })

# 12 Non Conforme
missing_indiv = ["justificatif_domicile", "bulletin_salaire", "specimen_signature", None, None]
expired_indiv = [None, None, None, "cin_valide", "justificatif_domicile"]
for i in range(5):
    docs = get_kyc_docs("Individuel", missing=missing_indiv[i], expired=expired_indiv[i])
    kyc_cases.append({
        "dossier_id": f"KYC-2026-{len(kyc_cases)+1:03d}",
        "client_type": "Individuel",
        "client_name": names[len(kyc_cases)],
        "deposit_amount_tnd": 15000,
        "documents_provided": docs,
        "sanctions_match": False,
        "sanctions_matched_list": None,
        "expected_result": "Non conforme",
        "justification": "Document manquant ou expiré."
    })
missing_corp = ["rne", "statuts_societe", "liste_beneficiaires_effectifs", "pv_nomination_signataires"]
for i in range(4):
    docs = get_kyc_docs("Corporate", missing=missing_corp[i])
    kyc_cases.append({
        "dossier_id": f"KYC-2026-{len(kyc_cases)+1:03d}",
        "client_type": "Corporate",
        "client_name": names[len(kyc_cases)],
        "deposit_amount_tnd": 15000,
        "documents_provided": docs,
        "sanctions_match": False,
        "sanctions_matched_list": None,
        "expected_result": "Non conforme",
        "justification": "Document d'entreprise obligatoire manquant."
    })
missing_ppe = ["declaration_statut_ppe", "justificatif_fonction", "validation_renforcee_hierarchie"]
for i in range(3):
    docs = get_kyc_docs("PPE", missing=missing_ppe[i])
    kyc_cases.append({
        "dossier_id": f"KYC-2026-{len(kyc_cases)+1:03d}",
        "client_type": "PPE",
        "client_name": names[len(kyc_cases)],
        "deposit_amount_tnd": 15000,
        "documents_provided": docs,
        "sanctions_match": False,
        "sanctions_matched_list": None,
        "expected_result": "Non conforme",
        "justification": "Document PPE obligatoire manquant."
    })

# 8 Escaladé
docs = get_kyc_docs("PPE", missing="declaration_detaillee_origine_fonds")
kyc_cases.append({
    "dossier_id": f"KYC-2026-{len(kyc_cases)+1:03d}",
    "client_type": "PPE",
    "client_name": names[len(kyc_cases)],
    "deposit_amount_tnd": 15000,
    "documents_provided": docs,
    "sanctions_match": False,
    "sanctions_matched_list": None,
    "expected_result": "Escaladé",
    "justification": "Dossier PPE incomplet nécessitant une escalade."
})
for i in range(4):
    docs = get_kyc_docs("Individuel")
    kyc_cases.append({
        "dossier_id": f"KYC-2026-{len(kyc_cases)+1:03d}",
        "client_type": "Individuel",
        "client_name": names[len(kyc_cases)],
        "deposit_amount_tnd": 60000,
        "documents_provided": docs,
        "sanctions_match": False,
        "sanctions_matched_list": None,
        "expected_result": "Escaladé",
        "justification": "Dépôt > 50K sans déclaration d'origine des fonds."
    })
sanctions = ["OFAC", "EU", "UN"]
for i in range(3):
    docs = get_kyc_docs("Individuel")
    kyc_cases.append({
        "dossier_id": f"KYC-2026-{len(kyc_cases)+1:03d}",
        "client_type": "Individuel",
        "client_name": names[len(kyc_cases)],
        "deposit_amount_tnd": 10000,
        "documents_provided": docs,
        "sanctions_match": True,
        "sanctions_matched_list": sanctions[i],
        "expected_result": "Escaladé",
        "justification": f"Correspondance trouvée sur la liste de sanctions {sanctions[i]}."
    })

kyc_payload = {
    "version": "1.0",
    "description": "Cas de test synthétiques pour le module KYC/AML de KUSOR v3",
    "generated_date": "2026-08-07",
    "statistics": {
        "total": 30,
        "conforme": 10,
        "non_conforme": 12,
        "escalade": 8,
        "expired_docs": 2,
        "sanctions_matches": 3
    },
    "cases": kyc_cases
}

credit_cases = []

def get_credit_docs(c_type, missing=None):
    docs = []
    if c_type == "Personnel":
        req = [("cin_valide", "CIN"), ("bulletins_salaire_3", "Bulletins de salaire"), ("attestation_employeur", "Attestation employeur")]
    elif c_type == "Hypothécaire":
        req = [("cin_valide", "CIN"), ("bulletins_salaire_3", "Bulletins de salaire"), ("compromis_vente", "Compromis de vente"), ("rapport_expertise_bien", "Rapport expertise")]
    elif c_type == "PME":
        req = [("etats_financiers_certifies", "Etats financiers"), ("garanties_proposees", "Garanties proposées")]
    else:
        req = [("etats_financiers_consolides", "Etats financiers"), ("garanties_proposees", "Garanties proposées")]
        
    for code, name in req:
        if code == missing:
            docs.append({"code": code, "name": name, "present": False, "expired": False})
        else:
            docs.append({"code": code, "name": name, "present": True, "expired": False})
    return docs

c_types = ["Personnel", "Personnel", "Hypothécaire", "Hypothécaire", "PME", "PME", "Corporate", "Corporate"]
for i in range(8):
    credit_cases.append({
        "dossier_id": f"CRED-2026-{len(credit_cases)+1:03d}",
        "credit_type": c_types[i],
        "applicant_name": names[i],
        "declared_monthly_income_tnd": 5000,
        "loan_amount_tnd": 20000,
        "loan_term_years": 5,
        "documents_provided": get_credit_docs(c_types[i]),
        "numerical_flags": [],
        "identity_flags": [],
        "guarantor": None,
        "debt_ratio": 30.0,
        "expected_verdict": "APPROVE",
        "justification": "Dossier complet, ratio d'endettement acceptable."
    })

credit_cases.append({
    "dossier_id": f"CRED-2026-{len(credit_cases)+1:03d}",
    "credit_type": "Hypothécaire",
    "applicant_name": names[len(credit_cases)],
    "declared_monthly_income_tnd": 5000,
    "loan_amount_tnd": 200000,
    "loan_term_years": 15,
    "documents_provided": get_credit_docs("Hypothécaire"), 
    "numerical_flags": [],
    "identity_flags": ["Nom légèrement différent sur CIN"],
    "guarantor": None,
    "debt_ratio": 30.0,
    "expected_verdict": "REVIEW",
    "justification": "Document conditionnel manquant (assurance vie)."
})
credit_cases.append({
    "dossier_id": f"CRED-2026-{len(credit_cases)+1:03d}",
    "credit_type": "PME",
    "applicant_name": names[len(credit_cases)],
    "declared_monthly_income_tnd": 15000,
    "loan_amount_tnd": 100000,
    "loan_term_years": 7,
    "documents_provided": get_credit_docs("PME"),
    "numerical_flags": [],
    "identity_flags": ["Adresse divergente"],
    "guarantor": None,
    "debt_ratio": 30.0,
    "expected_verdict": "REVIEW",
    "justification": "Document conditionnel manquant (business plan)."
})
credit_cases.append({
    "dossier_id": f"CRED-2026-{len(credit_cases)+1:03d}",
    "credit_type": "PME",
    "applicant_name": names[len(credit_cases)],
    "declared_monthly_income_tnd": 15000,
    "loan_amount_tnd": 100000,
    "loan_term_years": 7,
    "documents_provided": get_credit_docs("PME"),
    "numerical_flags": [],
    "identity_flags": [],
    "guarantor": None,
    "debt_ratio": 30.0,
    "expected_verdict": "REVIEW",
    "justification": "Document conditionnel manquant."
})

for i in range(4):
    credit_cases.append({
        "dossier_id": f"CRED-2026-{len(credit_cases)+1:03d}",
        "credit_type": "Personnel",
        "applicant_name": names[len(credit_cases)],
        "declared_monthly_income_tnd": 3000,
        "loan_amount_tnd": 50000,
        "loan_term_years": 5,
        "documents_provided": get_credit_docs("Personnel"),
        "numerical_flags": [],
        "identity_flags": [],
        "guarantor": None,
        "debt_ratio": 38.5,
        "expected_verdict": "REVIEW",
        "justification": "Ratio d'endettement à la limite (38.5%)."
    })

for i in range(3):
    credit_cases.append({
        "dossier_id": f"CRED-2026-{len(credit_cases)+1:03d}",
        "credit_type": "Personnel",
        "applicant_name": names[len(credit_cases)],
        "declared_monthly_income_tnd": 4000,
        "loan_amount_tnd": 20000,
        "loan_term_years": 3,
        "documents_provided": get_credit_docs("Personnel"),
        "numerical_flags": ["Différence mineure de salaire déclaré vs fiches de paie"],
        "identity_flags": [],
        "guarantor": None,
        "debt_ratio": 25.0,
        "expected_verdict": "REVIEW",
        "justification": "Incohérence numérique mineure détectée."
    })

for i in range(2):
    credit_cases.append({
        "dossier_id": f"CRED-2026-{len(credit_cases)+1:03d}",
        "credit_type": "Personnel",
        "applicant_name": names[len(credit_cases)],
        "declared_monthly_income_tnd": 2000,
        "loan_amount_tnd": 30000,
        "loan_term_years": 10,
        "documents_provided": get_credit_docs("Personnel"),
        "numerical_flags": [],
        "identity_flags": [],
        "guarantor": {"name": "Garant Test", "age": 68, "loan_term_years": 10, "flag": "age_limit_exceeded"},
        "debt_ratio": 30.0,
        "expected_verdict": "REJECT",
        "justification": "L'âge du garant à l'échéance dépasse 75 ans."
    })

credit_cases.append({
    "dossier_id": f"CRED-2026-{len(credit_cases)+1:03d}",
    "credit_type": "Personnel",
    "applicant_name": names[len(credit_cases)],
    "declared_monthly_income_tnd": 3000,
    "loan_amount_tnd": 20000,
    "loan_term_years": 5,
    "documents_provided": get_credit_docs("Personnel", missing="bulletins_salaire_3"),
    "numerical_flags": [],
    "identity_flags": [],
    "guarantor": None,
    "debt_ratio": 25.0,
    "expected_verdict": "REJECT",
    "justification": "Document obligatoire manquant (Bulletins de salaire)."
})

for i in range(2):
    credit_cases.append({
        "dossier_id": f"CRED-2026-{len(credit_cases)+1:03d}",
        "credit_type": "Personnel",
        "applicant_name": names[len(credit_cases)],
        "declared_monthly_income_tnd": 2000,
        "loan_amount_tnd": 50000,
        "loan_term_years": 5,
        "documents_provided": get_credit_docs("Personnel"),
        "numerical_flags": [],
        "identity_flags": [],
        "guarantor": None,
        "debt_ratio": 48.0,
        "expected_verdict": "REJECT",
        "justification": "Ratio d'endettement trop élevé (>45%)."
    })

for i in range(2):
    credit_cases.append({
        "dossier_id": f"CRED-2026-{len(credit_cases)+1:03d}",
        "credit_type": "Corporate",
        "applicant_name": names[len(credit_cases)],
        "declared_monthly_income_tnd": 100000,
        "loan_amount_tnd": 500000,
        "loan_term_years": 5,
        "documents_provided": get_credit_docs("Corporate"),
        "numerical_flags": ["Chiffre d'affaires déclaré sans rapport avec les états financiers"],
        "identity_flags": [],
        "guarantor": None,
        "debt_ratio": 20.0,
        "expected_verdict": "REJECT",
        "justification": "Incohérence numérique grave dans les états financiers."
    })

credit_payload = {
    "version": "1.0",
    "description": "Cas de test synthétiques pour le module crédit de KUSOR v3",
    "generated_date": "2026-08-07",
    "statistics": {
        "total": 25,
        "approve": 8,
        "review": 10,
        "reject": 7
    },
    "cases": credit_cases
}

os.makedirs("/home/houssein/kusor-v3/training/data", exist_ok=True)

with open("/home/houssein/kusor-v3/training/data/kyc_test_cases.json", "w", encoding="utf-8") as f:
    json.dump(kyc_payload, f, ensure_ascii=False, indent=2)

with open("/home/houssein/kusor-v3/training/data/credit_test_cases.json", "w", encoding="utf-8") as f:
    json.dump(credit_payload, f, ensure_ascii=False, indent=2)

print(f"Generated KYC cases: {len(kyc_cases)}")
print(f"Generated Credit cases: {len(credit_cases)}")
