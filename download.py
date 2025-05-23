#!/usr/bin/env python3
import os
import shutil
import zlib
import tempfile

from rich.console import Console
import transformers
from optimum.intel.openvino import OVModelForCausalLM

c = Console()

c.print("[bold green]Starting...[/bold green]")

# 1. Load & compile the model to OpenVINO IR (one-time compile)
c.print("[bold green]Compiling Llama to OpenVINO IR...[/bold green]")
# This will download the HF weights, convert to IR + weight-only INT8, and cache in-memory
ov_model = OVModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.2-3B-Instruct",
    compile=True,
    device="CPU"
)

# 2. Prepare a temporary dir and save the compiled IR there
c.print("[bold green]Saving compiled IR to temp dir...[/bold green]")
temp_dir = tempfile.TemporaryDirectory(dir=os.getcwd())
ov_model.save_pretrained(temp_dir.name)

# 3. Compress everything in temp_dir into a single .bin with zlib
c.print("[bold green]Compressing compiled IR files...[/bold green]")
os.makedirs(os.path.join(os.getcwd(), "models"), exist_ok=True)
output_path = os.path.join(os.getcwd(), "models", "llama", "Llama-3.2-3B-Instruct")

try:
    raise NotImplementedError("Compression feature removed")
    with open(output_path, "wb") as out_f:
        for root, _, files in os.walk(temp_dir.name):
            for fname in files:
                full_path = os.path.join(root, fname)
                # preserve relative paths if you like, here we just concatenate
                with open(full_path, "rb") as src_f:
                    data = src_f.read()
                    out_f.write(zlib.compress(data, level=9))
except NotImplementedError:
    print("Compression feature removed")
    # Copy the files instead
    shutil.copytree(temp_dir.name, output_path)

c.print(f"[bold green]Finished: compressed IR -> {output_path}[/bold green]")

# 4. Cleanup
temp_dir.cleanup()
c.print("[bold green]Cleanup finished.[/bold green]")
