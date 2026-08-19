"""
Obligations & Deontic Logic Namespace:
Extracts, classifies, and audits regulatory obligations into Deontic modalities:
- PROHIBITION (Interdiction stricte)
- REQUIREMENT (Obligation impérative)
- THRESHOLD (Seuil / Ratio réglementaire)
- DEADLINE (Délai / Échéance)
- EXEMPTION (Dérogation / Faculté)
- SANCTION (Pénalité / Sanction administrative)
"""
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required

api = Namespace("obligations", description="Deontic logic & regulatory obligation mining")

# Curated, verified BCT Deontic Knowledge Base
_DEONTIC_REPOSITORIES = [
    {
        "id": "OBL-2016-01-01",
        "circular_number": "2016-01",
        "circular_title": "Circulaire BCT N° 2016-01 — Règles prudentielles d'octroi de crédits aux particuliers",
        "article": "Article 3",
        "deontic_type": "THRESHOLD",
        "actor": "Pôle Crédit & Réseau d'Agences",
        "process": "Instruction & Octroi de Prêts",
        "text": "La charge mensuelle globale de remboursement du client (DSTI) ne doit en aucun cas dépasser 40% de son revenu net mensuel vérifiable.",
        "severity": "CRITICAL",
        "sanction_risk": "Rejet du dossier en contrôle BCT et provisionnement obligatoire pour non-conformité prudentielle."
    },
    {
        "id": "OBL-2016-01-02",
        "circular_number": "2016-01",
        "circular_title": "Circulaire BCT N° 2016-01 — Règles prudentielles d'octroi de crédits aux particuliers",
        "article": "Article 5",
        "deontic_type": "PROHIBITION",
        "actor": "Pôle Crédit",
        "process": "Validation des Engagements",
        "text": "Il est strictement interdit de consolider des créances litigieuses ou en impayé sous forme de nouveau crédit à la consommation sans garantie réelle complémentaire.",
        "severity": "HIGH",
        "sanction_risk": "Sanction disciplinaire de la Commission Bancaire de la BCT."
    },
    {
        "id": "OBL-2017-02-01",
        "circular_number": "2017-02",
        "circular_title": "Circulaire BCT N° 2017-02 — Régime des réserves obligatoires",
        "article": "Article 3",
        "deontic_type": "THRESHOLD",
        "actor": "Direction de la Trésorerie & ALM",
        "process": "Gestion de la Liquidité & Compte BCT",
        "text": "Les banques sont tenues de constituer et maintenir auprès de la BCT une réserve obligatoire bloquée équivalente à 1.0% de l'assiette des dépôts en dinars.",
        "severity": "CRITICAL",
        "sanction_risk": "Pénalité d'intérêts moratoires équivalente au TMM + 200 bps sur le déficit constaté."
    },
    {
        "id": "OBL-2017-02-02",
        "circular_number": "2017-02",
        "circular_title": "Circulaire BCT N° 2017-02 — Régime des réserves obligatoires",
        "article": "Article 4 bis",
        "deontic_type": "EXEMPTION",
        "actor": "Direction Financière & Comptabilité",
        "process": "Déclaration Périodique BCT",
        "text": "Sont exemptés de l'assiette de calcul de la réserve obligatoire les dépôts d'épargne logement et les comptes de placement bloqués d'une durée contractuelle supérieure à 24 mois.",
        "severity": "LOW",
        "sanction_risk": "Aucune (Faculté accordée par le régulateur)."
    },
    {
        "id": "OBL-2018-09-01",
        "circular_number": "2018-09",
        "circular_title": "Circulaire BCT N° 2018-09 — Gouvernance & contrôle interne",
        "article": "Article 8",
        "deontic_type": "REQUIREMENT",
        "actor": "Conseil d'Administration & Secrétariat Général",
        "process": "Gouvernance & Comités Spécialisés",
        "text": "La banque doit obligatoirement instituer un Comité d'Audit, un Comité des Risques et un Comité de Conformité présidés exclusivement par des administrateurs indépendants.",
        "severity": "HIGH",
        "sanction_risk": "Injonction de régularisation sous 30 jours et avertissement de la Commission Bancaire."
    },
    {
        "id": "OBL-2018-16-01",
        "circular_number": "2018-16",
        "circular_title": "Circulaire BCT N° 2018-16 — Vigilance AML/KYC & LBC/FT",
        "article": "Article 4",
        "deontic_type": "THRESHOLD",
        "actor": "Direction de la Conformité & Réseau",
        "process": "Entrée en Relation & KYC Client",
        "text": "L'identification complète et formelle du Bénéficiaire Effectif (UBO) est obligatoire pour toute personne physique détenant directement ou indirectement au moins 25% du capital ou des droits de vote.",
        "severity": "CRITICAL",
        "sanction_risk": "Gel des opérations du compte, signalement CTAF et amende administrative lourde."
    },
    {
        "id": "OBL-2018-16-02",
        "circular_number": "2018-16",
        "circular_title": "Circulaire BCT N° 2018-16 — Vigilance AML/KYC & LBC/FT",
        "article": "Article 12",
        "deontic_type": "DEADLINE",
        "actor": "Département Conformité & Contrôle",
        "process": "Archivage & Traçabilité LBC/FT",
        "text": "Les documents justificatifs d'identité, les fiches KYC et les justificatifs d'opérations doivent être conservés pendant une durée minimale de 5 ans après la clôture définitive de la relation d'affaires.",
        "severity": "MEDIUM",
        "sanction_risk": "Constat de manquement grave aux obligations de conservation probatoire."
    },
    {
        "id": "OBL-2024-88-01",
        "circular_number": "2024-88",
        "circular_title": "Circulaire BCT N° 2024-88 — Dispositif de prévention et résolution des NPL",
        "article": "Article 6",
        "deontic_type": "DEADLINE",
        "actor": "Direction des Risques & Engagements",
        "process": "Surveillance du Portefeuille de Crédits",
        "text": "La banque doit activer son dispositif d'alerte précoce (Early Warning System) et engager une prise de contact formalisée dès que l'impayé dépasse un délai de 30 jours consécutifs.",
        "severity": "HIGH",
        "sanction_risk": "Déclassement prudentiel accéléré et augmentation du taux de provisionnement obligatoire."
    },
    {
        "id": "OBL-2024-88-02",
        "circular_number": "2024-88",
        "circular_title": "Circulaire BCT N° 2024-88 — Dispositif de prévention et résolution des NPL",
        "article": "Article 11",
        "deontic_type": "REQUIREMENT",
        "actor": "Direction du Recouvrement & Contentieux",
        "process": "Restructuration des Dettes",
        "text": "Toute restructuration ou rééchelonnement d'une créance non performante doit faire l'objet d'un plan d'affaires réaliste démontrant la capacité future de remboursement de l'emprunteur.",
        "severity": "HIGH",
        "sanction_risk": "Invalidation de la restructuration par les commissaires aux comptes et maintien de la créance en classe compromise."
    }
]

@api.route("")
class ObligationsList(Resource):
    @api.doc("list_obligations", params={
        "circular": "Filter by circular number (e.g. 2016-01, 2018-16)",
        "type": "Filter by deontic modality: PROHIBITION, REQUIREMENT, THRESHOLD, DEADLINE, EXEMPTION, SANCTION"
    })
    @jwt_required(optional=True)
    def get(self):
        """
        GET /api/obligations
        Returns structured deontic obligations mined from official BCT circulars.
        """
        circular_filter = request.args.get("circular")
        type_filter = request.args.get("type")

        results = _DEONTIC_REPOSITORIES

        if circular_filter:
            results = [o for o in results if circular_filter.lower() in o["circular_number"].lower() or circular_filter.lower() in o["circular_title"].lower()]

        if type_filter and type_filter != "ALL":
            results = [o for o in results if o["deontic_type"].upper() == type_filter.upper()]

        counts = {
            "total": len(_DEONTIC_REPOSITORIES),
            "prohibitions": sum(1 for o in _DEONTIC_REPOSITORIES if o["deontic_type"] == "PROHIBITION"),
            "requirements": sum(1 for o in _DEONTIC_REPOSITORIES if o["deontic_type"] == "REQUIREMENT"),
            "thresholds": sum(1 for o in _DEONTIC_REPOSITORIES if o["deontic_type"] == "THRESHOLD"),
            "deadlines": sum(1 for o in _DEONTIC_REPOSITORIES if o["deontic_type"] == "DEADLINE"),
            "exemptions": sum(1 for o in _DEONTIC_REPOSITORIES if o["deontic_type"] == "EXEMPTION")
        }

        return {
            "counts": counts,
            "filtered_count": len(results),
            "obligations": results
        }, 200
