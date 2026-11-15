"""
4-bit QLoRA Fine-Tuning Script for Jupiter-Advisor-1.5B (RTX 3070 8GB / AMD MI300X).

Requirements (install in a CUDA/ROCm venv):
    pip install torch transformers peft bitsandbytes datasets accelerate trl
"""

from __future__ import annotations

import os
from pathlib import Path

BASE_MODEL = os.getenv("JUPITER_BASE_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")
DATASET_PATH = Path(__file__).resolve().parents[1] / "memory" / "datasets" / "jupiter_advisor_train.jsonl"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "memory" / "models" / "jupiter-advisor-1.5b-qlora"


def main() -> None:
    try:
        import torch
        from datasets import load_dataset
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
        from trl import SFTTrainer
    except ImportError as exc:
        raise SystemExit(
            f"Missing ML dependencies ({exc}). Install with:\n"
            "  pip install torch transformers peft bitsandbytes datasets accelerate trl"
        )

    if not DATASET_PATH.exists():
        raise SystemExit(f"Dataset not found at {DATASET_PATH}. Run: python3 scripts/export_advisor_dataset.py")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
    )
    model = prepare_model_for_kbit_training(model)

    lora_cfg = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_cfg)

    dataset = load_dataset("json", data_files=str(DATASET_PATH), split="train")
    args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        num_train_epochs=3,
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=5,
        save_strategy="epoch",
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        tokenizer=tokenizer,
        args=args,
        max_seq_length=1024,
    )
    trainer.train()
    model.save_pretrained(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))
    print(f"[+] Saved Jupiter-Advisor-1.5B QLoRA adapter to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
