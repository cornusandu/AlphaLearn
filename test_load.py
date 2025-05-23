#!/usr/bin/env python3
import os
from transformers import AutoTokenizer, pipeline
from optimum.intel.openvino import OVModelForCausalLM
import time

import pandas

def main(num_workers: int = 18, max_new_tokens: int = 2048):
    # 1. Tokenizer (you can cache this anywhere; here we re-use the HF repo)
    tokenizer = AutoTokenizer.from_pretrained(
        "meta-llama/Llama-3.2-3B-Instruct",
        use_fast=True
    )

    # 2. Load the pre-compiled OpenVINO model from disk
    #    (assumes you ran model.save_pretrained("./ov_llama32") previously)
    model_dir = os.path.abspath("./models/llama/Llama-3.2-3B-Instruct")
    model = OVModelForCausalLM.from_pretrained(model_dir, device="CPU")

    # 3. Build your HF pipeline around it
    text_gen = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        device="cpu",            # ensures CPU execution
        framework="pt"           # OpenVINO adapter under the hood
    )

    start = time.time()

    # 4. Inference
    prompt = [{'role': 'user', 'content': "Summarize the significance of the Michelson–Morley experiment."}]
    outputs = text_gen(
        prompt,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        temperature=0.7,
        pad_token_id=tokenizer.eos_token_id,
        num_workers=num_workers,
    )

    print(outputs[0]["generated_text"])

    print(f"\n\nTIME: {time.time() - start}")

    return time.time() - start

if __name__ == "__main__":
    data = pandas.DataFrame(columns=['num_workers', 'max_new_tokens', 'time'])
    num_tests = 7 * 4
    test = 0
    for i in (4, 8, 10, 12, 14, 16, 18):
        for x in (256, 512, 1024, 2048):
            test += 1
            if i == 4 and x == 2048:
                continue
            t = main(num_workers=i, max_new_tokens=x)
            data.loc[len(data.index)] = [i, x, t]
            print(f"Test {test}/{num_tests} completed.")

    print(data)

    data.to_parquet("results.parquet", engine="pyarrow", compression="brotli")        
