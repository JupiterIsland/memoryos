"""
4-bit QLoRA Fine-Tuning Script for Jupiter-Advisor-1.5B (RTX 3070 8GB / AMD MI300X).

Requirements (install in a CUDA/ROCm venv):
    pip install torch transformers peft bitsandbytes datasets accelerate trl
"""

from __future__ import annotations

import inspect
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
        import trl
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
    print(f"[+] Loaded {len(dataset)} training examples from {DATASET_PATH}")

    use_bf16 = bool(torch.cuda.is_available() and torch.cuda.is_bf16_supported())
    use_fp16 = bool(torch.cuda.is_available() and not use_bf16)

    sft_config_cls = getattr(trl, "SFTConfig", None)
    trainer_params = inspect.signature(SFTTrainer.__init__).parameters
    config_cls = sft_config_cls if sft_config_cls is not None else TrainingArguments
    config_params = inspect.signature(config_cls.__init__).parameters

    train_arg_kwargs = {
        "output_dir": str(OUTPUT_DIR),
        "per_device_train_batch_size": 2,
        "gradient_accumulation_steps": 4,
        "num_train_epochs": 3,
        "learning_rate": 2e-4,
        "fp16": use_fp16,
        "bf16": use_bf16,
        "logging_steps": 5,
        "save_strategy": "epoch",
        "report_to": "none",
    }
    if "max_length" in config_params:
        train_arg_kwargs["max_length"] = 1024
    elif "max_seq_length" in config_params:
        train_arg_kwargs["max_seq_length"] = 1024

    args = config_cls(**train_arg_kwargs)

    trainer_kwargs = {
        "model": model,
        "train_dataset": dataset,
        "args": args,
    }
    if "processing_class" in trainer_params:
        trainer_kwargs["processing_class"] = tokenizer
    elif "tokenizer" in trainer_params:
        trainer_kwargs["tokenizer"] = tokenizer
    if "max_seq_length" in trainer_params and "max_length" not in train_arg_kwargs and "max_seq_length" not in train_arg_kwargs:
        trainer_kwargs["max_seq_length"] = 1024

    trainer = SFTTrainer(**trainer_kwargs)
    trainer.train()
    model.save_pretrained(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))
    print(f"[+] Saved Jupiter-Advisor-1.5B QLoRA adapter to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
