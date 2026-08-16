# training/train_qlora.py
"""
QLoRA Fine-Tuning Script for Qwen2.5-Instruct on RTX 4060 GPU.
Configured with native bfloat16 for Ada Lovelace RTX 4060 architecture.
"""

import os
import gc
import sys
import torch
import logging

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct"
TRAIN_DATA = "training/data/train_dataset.jsonl"
VAL_DATA = "training/data/val_dataset.jsonl"
OUTPUT_DIR = "training/output/kusor-qwen-lora"


def train():
    logger.info("=" * 60)
    logger.info("🚀 Starting KUSOR v3 QLoRA Fine-Tuning on RTX 4060 GPU...")
    logger.info("=" * 60)

    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs("training/output", exist_ok=True)

    # 1. 4-bit Quantization Config with bfloat16
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    logger.info("Loading cached base model: %s in bfloat16...", MODEL_NAME)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
    )

    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    model.config.use_cache = False

    # 2. LoRA Config
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # 3. Load Dataset
    logger.info("Loading dataset: %s and %s...", TRAIN_DATA, VAL_DATA)
    dataset = load_dataset("json", data_files={"train": TRAIN_DATA, "validation": VAL_DATA})

    def formatting_prompts_func(examples):
        texts = []
        for messages in examples["messages"]:
            text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
            texts.append(text)
        return {"text": texts}

    dataset = dataset.map(formatting_prompts_func, batched=True)

    # 4. TRL SFT Training Configuration with BF16
    sft_config = SFTConfig(
        output_dir=OUTPUT_DIR,
        dataset_text_field="text",
        max_length=1536,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        warmup_steps=10,
        num_train_epochs=3,
        learning_rate=2e-4,
        fp16=False,
        bf16=True,
        logging_steps=5,
        eval_strategy="steps",
        eval_steps=25,
        save_strategy="steps",
        save_steps=25,
        save_total_limit=2,
        optim="paged_adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        seed=42,
        report_to="none",
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
    )

    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        args=sft_config,
    )

    logger.info("Starting training loop across %d samples...", len(dataset["train"]))
    trainer.train()

    logger.info("Saving fine-tuned LoRA adapters to %s...", OUTPUT_DIR)
    trainer.model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    logger.info("=" * 60)
    logger.info("✓ KUSOR v3 Fine-Tuning Completed Successfully!")
    logger.info("=" * 60)


if __name__ == "__main__":
    train()
