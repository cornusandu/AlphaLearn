import os
import math
from pathlib import Path

import psutil
import torch
import torch.quantization
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

from optimum.intel.openvino import OVModelForCausalLM

def get_workers(percent: int = 100) -> int:
    cores = psutil.cpu_count(logical=True)
    return min(cores, math.ceil(cores * percent / 100))

def get_model(
    model_name: str,
    cpu_thread_pct: int = 100
) -> transformers.Pipeline:
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = OVModelForCausalLM.from_pretrained(
        model_name,
        device="CPU",
        compile_model=False
    )
    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        device="cpu",            # ensures CPU execution
        framework="pt"           # OpenVINO adapter under the hood
    )

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