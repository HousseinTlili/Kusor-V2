# training/export_gguf.py
"""
Script to merge QLoRA weights into base model and export GGUF quantized binary (q4_k_m)
for registration in Ollama as `kusor-qwen:v1`.
"""

import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

LORA_DIR = "training/output/kusor-qwen-lora"
OUTPUT_GGUF_DIR = "training/output"
GGUF_FILE = "training/output/kusor-qwen-v1.gguf"


def export():
    logger.info("Starting GGUF export pipeline...")
    os.makedirs(OUTPUT_GGUF_DIR, exist_ok=True)

    try:
        from unsloth import FastLanguageModel
        logger.info("Loading fine-tuned model from %s...", LORA_DIR)
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=LORA_DIR,
            max_seq_length=2048,
            load_in_4bit=True,
        )

        logger.info("Exporting model to GGUF format (q4_k_m)...")
        model.save_pretrained_gguf(
            OUTPUT_GGUF_DIR,
            tokenizer,
            quantization_method="q4_k_m"
        )
        logger.info("✓ Exported GGUF model successfully to %s", GGUF_FILE)

    except Exception as e:
        logger.warning("Unsloth GGUF export failed or unsloth not installed: %s", e)
        print("\nTo export GGUF using llama.cpp manually, run:")
        print(f"python llama.cpp/convert_hf_to_gguf.py {LORA_DIR} --outfile {GGUF_FILE} --outtype q4_k_m")
        print(f"ollama create kusor-qwen:v1 -f training/Modelfile")


if __name__ == "__main__":
    export()
