import os
import math
from pathlib import Path

import psutil
import torch
import torch.quantization
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["OPENVINO_VERBOSE"] = "0"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TQDM_DISABLE"] = "true"            # disable tqdm bars

import warnings
import logging

# 2. Silence all Python warnings (including TracerWarning, DeprecationWarning, etc.)
warnings.filterwarnings("ignore", category=Warning)

from optimum.intel.openvino import OVModelForCausalLM

# 3. Push loggers to ERROR level
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("optimum").setLevel(logging.ERROR)
logging.getLogger("nncf").setLevel(logging.ERROR)
logging.getLogger("openvino").setLevel(logging.ERROR)
logging.getLogger("torch.jit").setLevel(logging.ERROR)

import logging
from transformers import logging as _tlogging

# set Python loggers to ERROR
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("optimum").setLevel(logging.ERROR)
_tlogging.set_verbosity_error()

def get_workers(percent: int = 100) -> int:
    cores = psutil.cpu_count(logical=True)
    return min(cores, math.ceil(cores * percent / 100))

def get_model(
    model_name: str, tokenizer_name: str | None = None
) -> transformers.Pipeline:
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name or model_name)
    model = OVModelForCausalLM.from_pretrained(
        model_name,
        device="CPU",
        compile=False,
        framework="pt",           # OpenVINO adapter under the hood
        library="transformers",   # OpenVINO adapter under the hood
    )
    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        device="cpu",            # ensures CPU execution
    )
    return pipe

def generate_response(
    prompt: str,
    model: transformers.Pipeline,
    workers: int = 1,
    temperature: float = 0.9,
    top_p: float = 0.95,
    top_k: int = 40,
    repetition_penalty: float = 1.18,
    num_return_sequences: int = 1,
    max_new_tokens: int = 1028,
    eos_token_id: int = None
) -> tuple[list[dict], str]:
    num_workers = workers

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
    return out[0]["generated_text"], out[0]["generated_text"][-1]['content']


if __name__ == "__main__":
    MODEL_ID = "meta-llama/Llama-3.2-3B-Instruct"
    llm = get_model(
        MODEL_ID,
    )

    prompt = "Explain the principle of reinforcement learning in simple terms."
    resp = generate_response(prompt, llm, workers=get_workers(50))
    print(resp)