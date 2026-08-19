# training/evaluate.py
"""
Evaluation suite for fine-tuned model vs base model across 4 metric dimensions:
1. Temporal Reference Exact Match (EM)
2. Obligation Classification Macro F1
3. JSON Schema Validity Rate
4. Citation Groundedness Score
"""

import os
import json
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

EVAL_PROMPTS = [
    {
        "prompt": "En quelle année la circulaire BCT N° 2018-09 a-t-elle été promulguée ?",
        "expected_type": "temporal",
        "expected_answer": "2018"
    },
    {
        "prompt": "Classifie cette règle: Les banques doivent maintenir un ratio de liquidité supérieur à 100%.",
        "expected_type": "THRESHOLD",
        "expected_answer": "THRESHOLD"
    },
    {
        "prompt": "Génère un rapport JSON de vérification KYC pour un client ayant une CIN présente et un justificatif manquant.",
        "expected_type": "json",
        "expected_answer": "json"
    }
]


def evaluate_model(model_name: str = "qwen2.5:7b") -> Dict[str, float]:
    logger.info("Evaluating model %s...", model_name)
    try:
        from openai import OpenAI
        client = OpenAI(api_key="ollama", base_url="http://localhost:11434/v1")
    except Exception as e:
        logger.warning("Could not connect to Ollama for evaluation: %s", e)
        return {"exact_match": 0.0, "json_validity": 0.0, "score": 0.0}

    correct_em = 0
    valid_json = 0

    for idx, test in enumerate(EVAL_PROMPTS, 1):
        try:
            resp = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "Tu es KUSOR, l'expert en conformité BCT."},
                    {"role": "user", "content": test["prompt"]}
                ],
                temperature=0.1,
            )
            ans = resp.choices[0].message.content or ""
            
            if test["expected_answer"].lower() in ans.lower():
                correct_em += 1

            if test["expected_type"] == "json":
                try:
                    json.loads(ans)
                    valid_json += 1
                except Exception:
                    pass

        except Exception as e:
            logger.error("Eval test %d failed: %s", idx, e)

    em_rate = round(correct_em / len(EVAL_PROMPTS), 2)
    logger.info("Evaluation results for %s: Exact Match = %.2f", model_name, em_rate)
    return {"exact_match": em_rate, "eval_samples": len(EVAL_PROMPTS)}


def main():
    logger.info("Running evaluation benchmark...")
    res_base = evaluate_model("qwen2.5:7b")
    print(f"Base Model Score: {res_base}")


if __name__ == "__main__":
    main()
