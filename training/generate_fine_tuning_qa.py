# training/generate_fine_tuning_qa.py
"""
Script to generate 500+ French regulatory Q&A training pairs from BCT circulars
using the DeepSeek V4 Flash API (OpenAI-compatible) or local teacher model fallback.
"""

import os
import json
import logging
from typing import List, Dict, Any

from openai import OpenAI

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OUTPUT_FILE = "training/data/synthetic_qa.jsonl"
SYSTEM_PROMPT = "Tu es un expert en droit bancaire tunisien et en réglementation de la Banque Centrale de Tunisie (BCT)."

PROMPT_TEMPLATE = """Tu es un expert en droit bancaire tunisien. À partir du texte de circulaire BCT ci-dessous, génère 3 paires question-réponse en français couvrant:
(1) une référence temporelle ou d'abrogation ("En quelle année/date...", "Quelle circulaire a été modifiée par..."),
(2) une obligation réglementaire classifiée (PROHIBITION/REQUIREMENT/THRESHOLD/DEADLINE),
(3) une question de conformité avec réponse JSON structurée.

Texte de la circulaire:
{chunk_text}

Format de réponse STRICT (retourne un tableau JSON valide contenant 3 objets):
[
  {{
    "messages": [
      {{"role": "system", "content": "Tu es KUSOR, l'expert en conformité BCT."}},
      {{"role": "user", "content": "..."}},
      {{"role": "assistant", "content": "..."}}
    ]
  }},
  ...
]
"""


def get_openai_client() -> OpenAI:
    if DEEPSEEK_API_KEY:
        logger.info("Using DeepSeek V4 Flash API (platform.deepseek.com)...")
        return OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
    else:
        logger.info("DEEPSEEK_API_KEY not set. Falling back to local Ollama (qwen2.5:7b)...")
        return OpenAI(api_key="ollama", base_url="http://localhost:11434/v1")


def load_circular_chunks() -> List[str]:
    chunks = []
    uploads_dir = "backend/data/uploads"
    if os.path.exists(uploads_dir):
        for f in os.listdir(uploads_dir):
            if f.endswith(".pdf") or f.endswith(".txt"):
                path = os.path.join(uploads_dir, f)
                try:
                    if f.endswith(".txt"):
                        with open(path, "r", encoding="utf-8", errors="ignore") as file:
                            txt = file.read()
                    else:
                        import fitz
                        doc = fitz.open(path)
                        txt = "\n".join([page.get_text() for page in doc])
                        doc.close()
                    
                    for i in range(0, len(txt), 3000):
                        chunk = txt[i:i+3000].strip()
                        if len(chunk) > 300:
                            chunks.append(chunk)
                except Exception as e:
                    logger.warning("Could not read %s: %s", f, e)

    logger.info("Loaded %d circular text chunks for Q&A generation.", len(chunks))
    return chunks


def main():
    os.makedirs("training/data", exist_ok=True)
    client = get_openai_client()
    chunks = load_circular_chunks()

    if not chunks:
        logger.error("No circular chunks found in backend/data/uploads/")
        return

    model_name = "deepseek-chat" if DEEPSEEK_API_KEY else "qwen2.5:7b"
    total_generated = 0

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out_f:
        for idx, chunk in enumerate(chunks, 1):
            logger.info("Processing chunk %d/%d...", idx, len(chunks))
            prompt = PROMPT_TEMPLATE.format(chunk_text=chunk[:3000])

            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                )

                content = response.choices[0].message.content
                data = json.loads(content)
                if isinstance(data, dict):
                    data = data.get("qa_pairs", data.get("pairs", data.get("messages", [data])))

                if isinstance(data, list):
                    for item in data:
                        out_f.write(json.dumps(item, ensure_ascii=False) + "\n")
                        total_generated += 1

            except Exception as e:
                logger.error("Error generating Q&A for chunk %d: %s", idx, e)

    logger.info("✓ Successfully generated %d synthetic Q&A training pairs in %s", total_generated, OUTPUT_FILE)


if __name__ == "__main__":
    main()
