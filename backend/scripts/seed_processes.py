# backend/scripts/seed_processes.py
"""
Seed script to populate standard Attijari Bank banking processes (:Process)
and contract templates (:ContractTemplate) into Neo4j.

Run once after Neo4j initialization:
    python -m backend.scripts.seed_processes
"""

import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.config import Config
from backend.graph.neo4j_manager import Neo4jManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Standard Attijari Bank Tunisia Internal Processes
PROCESSES = [
    {"id": "proc_octroi_credit", "name": "Octroi de crédit", "department": "Direction Crédit", "owner": "Comité de Crédit"},
    {"id": "proc_ouverture_compte", "name": "Ouverture de compte", "department": "Réseau d'agences", "owner": "Conformité Agence"},
    {"id": "proc_virement_international", "name": "Virements et opérations internationales", "department": "Direction International", "owner": "Service Change"},
    {"id": "proc_declaration_ctaf", "name": "Déclaration CTAF / LCB-FT", "department": "Direction Conformité", "owner": "Responsable LCB-FT"},
    {"id": "proc_calcul_ratio", "name": "Calcul et reporting des ratios prudentiels", "department": "Direction Financière", "owner": "Contrôle de Gestion"},
    {"id": "proc_gestion_reclamations", "name": "Traitement des réclamations clients", "department": "Service Client", "owner": "Responsable Qualité"},
]

# Standard Attijari Bank Contract Templates
CONTRACT_TEMPLATES = [
    {"id": "tmpl_convention_compte", "name": "Convention de compte courant", "template_type": "compte", "version": "2024.1"},
    {"id": "tmpl_contrat_pret_immob", "name": "Contrat de prêt immobilier", "template_type": "pret", "version": "2023.2"},
    {"id": "tmpl_contrat_pret_consommation", "name": "Contrat de prêt à la consommation", "template_type": "pret", "version": "2023.1"},
    {"id": "tmpl_convention_credit_equipement", "name": "Convention de crédit d'équipement", "template_type": "entreprise", "version": "2024.1"},
    {"id": "tmpl_accord_cadre_marche", "name": "Accord-cadre d'opérations de marché", "template_type": "salle_marche", "version": "2022.3"},
]


def seed_processes_and_templates():
    cfg = Config()
    neo4j = Neo4jManager(cfg.NEO4J_URI, cfg.NEO4J_USER, cfg.NEO4J_PASSWORD)

    logger.info("Seeding Process nodes into Neo4j...")
    for proc in PROCESSES:
        neo4j.run_query(
            """
            MERGE (p:Process {id: $id})
            SET p.name = $name,
                p.department = $department,
                p.owner = $owner,
                p.created_at = datetime()
            """,
            proc,
        )

    logger.info("Seeding ContractTemplate nodes into Neo4j...")
    for tmpl in CONTRACT_TEMPLATES:
        neo4j.run_query(
            """
            MERGE (ct:ContractTemplate {id: $id})
            SET ct.name = $name,
                ct.template_type = $template_type,
                ct.version = $version,
                ct.created_at = datetime()
            """,
            tmpl,
        )

    neo4j.close()
    logger.info("✓ Successfully seeded %d processes and %d contract templates.", len(PROCESSES), len(CONTRACT_TEMPLATES))


if __name__ == "__main__":
    seed_processes_and_templates()
