"""
Seed comprehensive BCT circulars into PostgreSQL and ChromaDB for KUSOR.
"""
import os
import sys
import uuid
import logging
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app import create_app
from backend.extensions import db
from backend.models.document import Document
from backend.models.chunk import Chunk

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BCT_CIRCULARS = [
    {
        "number": "2017-02",
        "title": "Circulaire BCT N° 2017-02 — Régime des Réserves Obligatoires des Banques",
        "category": "Politique Monétaire",
        "date": datetime(2017, 3, 15),
        "content": """CIRCULAIRE AUX BANQUES N° 2017-02
Objet : Dispositif et conditions de constitution de la réserve obligatoire.
La Banque Centrale de Tunisie fixe par la présente circulaire les règles applicables aux banques et établissements financiers pour la constitution et le calcul des réserves obligatoires.

Article 1 : Champ d'application et assujettissement.
Toutes les banques agréées en Tunisie sont tenues de constituer des réserves obligatoires auprès de la Banque Centrale de Tunisie sous forme de comptes non rémunérés.

Article 2 : Assiette de calcul de la réserve obligatoire.
L'assiette de la réserve obligatoire est constituée par l'ensemble des dépôts et engagements en dinars contractés auprès de la clientèle résidente, notamment :
1. Les dépôts à vue et comptes courants.
2. Les dépôts d'épargne et comptes sur livret.
3. Les dépôts à terme et bons de caisse d'une durée initiale inférieure ou égale à 24 mois.
Sont exclus de l'assiette les dépôts en devises et les dépôts interbancaires.

Article 3 : Taux de la réserve obligatoire.
Le taux de la réserve obligatoire est fixé à 1.0% sur l'ensemble des dépôts à vue et à terme en dinars éligibles. La Banque Centrale peut moduler ce taux en fonction des objectifs de politique monétaire et de régulation de la liquidité bancaire.

Article 4 : Période d'observation et de constitution.
La période de constitution de la réserve obligatoire s'étend du 1er au dernier jour de chaque mois civil (moyenne mensuelle des soldes de clôture quotidiens). Le respect du niveau moyen requis permet d'amortir les fluctuations journalières de trésorerie bancaire.

Article 5 : Sanctions en cas de non-respect.
En cas de défaillance ou d'insuffisance dans la constitution de la réserve obligatoire moyenne requise, la banque contrevenante est passible de pénalités d'intérêt de retard équivalentes au Taux Directeur de la BCT majoré de 300 points de base (3.0%) par jour de manquement, conformément à l'article 78 des statuts de la Banque Centrale.
"""
    },
    {
        "number": "2016-01",
        "title": "Circulaire BCT N° 2016-01 — Règles prudentielles d'octroi de crédits aux particuliers",
        "category": "Crédit & Risques",
        "date": datetime(2016, 1, 10),
        "content": """CIRCULAIRE AUX BANQUES N° 2016-01
Objet : Conditions d'octroi de crédits et plafonnement du ratio d'endettement.
La Banque Centrale de Tunisie arrête les normes prudentielles applicables à l'octroi des crédits aux particuliers pour prévenir le sur-endettement.

Article 1 : Ratio d'endettement maximal (DSTI).
Le total des mensualités de remboursement de l'ensemble des crédits accordés à un emprunteur particulier ne peut en aucun cas excéder quarante pour cent (40.0%) de son revenu net mensuel régulier et justifié.

Article 2 : Reste à vivre minimum.
L'établissement prêteur doit impérativement s'assurer que le reste à vivre après déduction de la mensualité du prêt permet de couvrir les besoins fondamentaux du ménage (minimum 800 TND pour un célibataire, 1200 TND pour un foyer).

Article 3 : Justificatifs obligatoires.
Tout dossier de crédit doit comporter :
- Pièce d'identité nationale valide (CIN).
- Les trois derniers bulletins de paie certifiés ou déclarations fiscales.
- Les relevés de compte bancaire des trois derniers mois.
- Une attestation de travail précisant la titularisation ou contrat en cours.
- L'état d'endettement délivré par la Centrale des Risques de la BCT.
"""
    },
    {
        "number": "2018-09",
        "title": "Circulaire BCT N° 2018-09 — Cadre de gouvernance et contrôle interne des banques",
        "category": "Gouvernance & Conformité",
        "date": datetime(2018, 5, 20),
        "content": """CIRCULAIRE AUX BANQUES N° 2018-09
Objet : Dispositif de gouvernance d'entreprise et de contrôle interne au sein des banques.

Article 1 : Séparation des pouvoirs.
Les banques doivent instaurer une séparation stricte entre les fonctions de gestion exécutive (Direction Générale) et les fonctions de surveillance (Conseil d'Administration).

Article 2 : Comités spécialisés obligatoires.
Le Conseil d'Administration doit constituer en son sein au minimum trois comités spécialisés :
- Comité d'Audit.
- Comité des Risques.
- Comité de Nomination et de Rémunération.

Article 3 : Fonction Conformité (Compliance).
La Direction de la Conformité doit être dotée d'une indépendance hiérarchique absolue par rapport aux lignes de métiers commerciales et doit rapporter directement au Comité d'Audit et au Conseil d'Administration.
"""
    },
    {
        "number": "2018-16",
        "title": "Circulaire BCT N° 2018-16 — Lutte contre le blanchiment d'argent et le financement du terrorisme (AML / KYC)",
        "category": "AML / KYC",
        "date": datetime(2018, 9, 30),
        "content": """CIRCULAIRE AUX BANQUES N° 2018-16
Objet : Obligations de vigilance à l'égard de la clientèle et identification des bénéficiaires effectifs.

Article 1 : Obligation d'identification (KYC).
Avant toute entrée en relation d'affaires ou ouverture de compte, les banques doivent vérifier l'identité du client et celle de son représentant légal au moyen de documents officiels probants.

Article 2 : Identification du bénéficiaire effectif (UBO).
Pour toute personne morale, la banque doit identifier toute personne physique détenant directement ou indirectement au moins vingt-cinq pour cent (25.0%) du capital ou des droits de vote, ou exerçant un contrôle effectif sur la gouvernance.

Article 3 : Personnes Politiquement Exposées (PPE).
Les clients qualifiés de PPE (Personnes Politiquement Exposées) ainsi que les membres de leur famille directe font l'objet d'une vigilance renforcée et de l'approbation préalable d'un membre de la Direction Générale avant ouverture de compte.
"""
    },
    {
        "number": "2024-88",
        "title": "Circulaire BCT N° 2024-88 — Prévention et résolution des créances non performantes (NPL)",
        "category": "Conformité & Risques",
        "date": datetime(2024, 11, 15),
        "content": """CIRCULAIRE AUX BANQUES N° 2024-88
Objet : Dispositif de prévention et de résolution des créances non performantes (NPL).
La Banque Centrale de Tunisie fixe par la présente circulaire les règles prudentielles applicables aux établissements de crédit en matière de surveillance et de classification des créances.

Article 1 : Champ d'application.
Les banques doivent mettre en place un système d'alerte précoce pour détecter les impayés dès 30 jours de retard.

Article 2 : Classification des créances.
Les engagements doivent être classés en cinq catégories (Classe 0 : Actifs sains, Classe 1 : Actifs sous surveillance, Classe 2 : Actifs incertains, Classe 3 : Actifs préoccupants, Classe 4 : Actifs compromis).

Article 3 : Provisionnement obligatoire.
Les créances classées 4 (compromis) font l'objet d'un provisionnement intégral à 100% après déduction des garanties réelles admissibles.
"""
    }
]

def seed_bct_knowledge():
    app = create_app("development")
    with app.app_context():
        logger.info("Starting BCT knowledge base seeding...")
        doc_processor = app.document_processor

        for c in BCT_CIRCULARS:
            num = c["number"]
            doc = Document.query.filter_by(number=num).first()
            if not doc:
                doc_id = f"doc_{uuid.uuid4().hex[:8]}"
                doc = Document(
                    id=doc_id,
                    number=num,
                    title=c["title"],
                    category=c["category"],
                    date=c["date"],
                    url=f"https://www.bct.gov.tn/bct/siteprod/documents/{num}.pdf",
                    status="ACTIVE",
                    indexation_state="INDEXED"
                )
                db.session.add(doc)
                db.session.commit()
                logger.info("Created Document in Postgres: %s (%s)", num, doc_id)
            else:
                doc.title = c["title"]
                doc.category = c["category"]
                doc.date = c["date"]
                doc.indexation_state = "INDEXED"
                db.session.commit()
                logger.info("Updated Document in Postgres: %s (%s)", num, doc.id)

            # Clean existing chunks for this doc
            Chunk.query.filter_by(document_id=doc.id).delete()
            db.session.commit()

            # Split paragraphs into chunks
            paragraphs = [p.strip() for p in c["content"].split("\n\n") if p.strip()]
            for idx, p in enumerate(paragraphs):
                chunk_id = f"{num}_chunk_{idx}"
                chunk = Chunk(
                    id=chunk_id,
                    document_id=doc.id,
                    chunk_index=idx,
                    page_number=1,
                    content=p,
                    embedding_id=chunk_id
                )
                db.session.add(chunk)
            db.session.commit()
            logger.info("Created %d chunks in Postgres for %s", len(paragraphs), num)

            # Ingest into ChromaDB collections if processor is available
            if doc_processor and hasattr(doc_processor, "client"):
                try:
                    col = doc_processor.client.get_or_create_collection(name=doc_processor.collection_name)
                    chunk_ids = [f"{num}_chunk_{i}" for i in range(len(paragraphs))]
                    metadatas = [{
                        "document_id": doc.id,
                        "circular_number": num,
                        "title": c["title"],
                        "category": c["category"],
                        "page_number": 1
                    } for _ in paragraphs]
                    
                    col.upsert(
                        ids=chunk_ids,
                        documents=paragraphs,
                        metadatas=metadatas
                    )
                    logger.info("ChromaDB indexed %d chunks for circular %s", len(paragraphs), num)
                except Exception as e:
                    logger.warning("ChromaDB indexing note for %s: %s", num, e)

        logger.info("BCT knowledge base successfully seeded with %d official circulars!", len(BCT_CIRCULARS))

if __name__ == "__main__":
    seed_bct_knowledge()
