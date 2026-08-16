# training/prepare_dataset.py
"""
Script to prepare and split fine-tuning dataset:
Mixes 85% BCT domain Q&A with 15% general instruction data (to prevent catastrophic forgetting)
and exports 85% train / 15% val split JSONL files.
"""

import os
import json
import random
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

INPUT_QA_FILE = "training/data/synthetic_qa.jsonl"
TRAIN_OUTPUT = "training/data/train_dataset.jsonl"
VAL_OUTPUT = "training/data/val_dataset.jsonl"

# 15% General instruction data to preserve general reasoning & French language fluency
GENERAL_INSTRUCTION_SAMPLE = [
    {
        "messages": [
            {"role": "system", "content": "Tu es KUSOR, un assistant IA généraliste et spécialisé en conformité."},
            {"role": "user", "content": "Rédige une note explicative courte sur la différence entre le taux d'intérêt nominal et le Taux Effectif Global (TEG)."},
            {"role": "assistant", "content": "Le **taux nominal** est le taux d'intérêt brut convenu dans le contrat de prêt sans inclure les frais annexes. Le **TEG (Taux Effectif Global)** englobe la totalité des coûts obligatoires liés au crédit (frais de dossier, commissions, assurances exigées)."}
        ]
    },
    {
        "messages": [
            {"role": "system", "content": "Tu es KUSOR, un assistant IA réglementaire."},
            {"role": "user", "content": "Quels sont les principes fondamentaux de la lutte contre le blanchiment d'argent (LCB-FT) ?"},
            {"role": "assistant", "content": "Les principes clés de la LCB-FT reposent sur: (1) L'obligation de vigilance (KYC - Know Your Customer), (2) La détection et le filtrage contre les listes de sanctions, (3) L'évaluation de l'approche basée sur les risques, (4) La déclaration de soupçon auprès de l'autorité financière compétente (CTAF en Tunisie)."}
        ]
    }
]


def main():
    if not os.path.exists(INPUT_QA_FILE):
        logger.error("Input file %s not found. Run generate_fine_tuning_qa.py first.", INPUT_QA_FILE)
        return

    domain_data = []
    with open(INPUT_QA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    domain_data.append(json.loads(line.strip()))
                except Exception:
                    pass

    logger.info("Loaded %d domain Q&A samples from %s", len(domain_data), INPUT_QA_FILE)

    # Mix 85% domain data with 15% general data
    num_general_needed = int(len(domain_data) * 0.15 / 0.85) if domain_data else 10
    general_data = (GENERAL_INSTRUCTION_SAMPLE * ((num_general_needed // len(GENERAL_INSTRUCTION_SAMPLE)) + 1))[:num_general_needed]

    combined = domain_data + general_data
    random.seed(42)
    random.shuffle(combined)

    # 85% train / 15% validation split
    split_idx = int(len(combined) * 0.85)
    train_set = combined[:split_idx]
    val_set = combined[split_idx:]

    with open(TRAIN_OUTPUT, "w", encoding="utf-8") as f:
        for item in train_set:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    with open(VAL_OUTPUT, "w", encoding="utf-8") as f:
        for item in val_set:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    logger.info("✓ Prepared dataset split: %d train samples (%s), %d val samples (%s)", len(train_set), TRAIN_OUTPUT, len(val_set), VAL_OUTPUT)


if __name__ == "__main__":
    main()
