import os
import math
from pathlib import Path

import psutil
import torch
import torch.quantization
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

def get_workers(percent: int = 100) -> int:
    cores = psutil.cpu_count(logical=True)
    return min(cores, math.ceil(cores * percent / 100))

def configure_cpu_threads(percent: int = 100):
    workers = get_workers(percent)
    os.environ["OMP_NUM_THREADS"] = str(workers)
    os.environ["MKL_NUM_THREADS"] = str(workers)
    torch.set_num_threads(workers)
    return workers

def get_model(
    model_name: str,
    quantize: bool = True,
    compile_model: bool = True,
    cpu_thread_pct: int = 100,
    cache_dir: str = "./quantized_cache"
) -> transformers.Pipeline:
    # 1) Thread config
    workers = configure_cpu_threads(cpu_thread_pct)
    print(f"[INFO] Using {workers} CPU threads")

    # 2) Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)

    # 3) Decide where to load from (cache vs. fresh)
    quant_dir = Path(cache_dir) / model_name.replace("/", "_")
    if quantize and quant_dir.exists():
        print(f"[INFO] Loading quantized model from {quant_dir}")
        model = AutoModelForCausalLM.from_pretrained(quant_dir, device_map="cpu")
    else:
        print("[INFO] Loading full-precision model")
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,
            device_map="cpu"
        )

        # 4) Quantize once and save
        if quantize:
            print("[INFO] Running dynamic quantization (this may take a minute)…")
            model = torch.quantization.quantize_dynamic(
                model,
                {torch.nn.Linear},
                dtype=torch.qint8
            )
            quant_dir.mkdir(parents=True, exist_ok=True)
            model.save_pretrained(quant_dir)
            tokenizer.save_pretrained(quant_dir)
            print(f"[INFO] Quantized model cached to {quant_dir}")

    # 5) Optional compile
    if compile_model and hasattr(torch, "compile"):
        model = torch.compile(model)
        print("[INFO] Model wrapped with torch.compile()")

    # 6) Build a CPU-only pipeline (no `device` arg!)
    text_gen = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        # device must be omitted when using accelerate-backed model
        torch_dtype=torch.float32,
    )

    return text_gen

def generate_response(
    prompt: str,
    model: transformers.Pipeline,
    workers: int = 1,
    temperature: float = 0.9,
    top_p: float = 0.95,
    top_k: int = 40,
    repetition_penalty: float = 1.18,
    num_return_sequences: int = 1,
    max_new_tokens: int = 256,
    eos_token_id: int = None
) -> str:
    num_workers = workers if not torch.cuda.is_available() else 1

    out = model(
        prompt,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        repetition_penalty=repetition_penalty,
        num_return_sequences=num_return_sequences,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        pad_token_id=model.tokenizer.pad_token_id,
        eos_token_id=eos_token_id or model.tokenizer.eos_token_id,
        num_workers=num_workers,
    )
    return out[0]["generated_text"]


if __name__ == "__main__":
    MODEL_ID = "meta-llama/Llama-3.2-3B-Instruct"
    llm = get_model(
        MODEL_ID,
        quantize=True,          # run quantization (once) and cache
        compile_model=True,     # use torch.compile if available
        cpu_thread_pct=50,      # use 50% of your CPU threads
        cache_dir="./quantized_cache"
    )

    prompt = "Explain the principle of reinforcement learning in simple terms."
    resp = generate_response(prompt, llm, workers=get_workers(50))
    print(resp)