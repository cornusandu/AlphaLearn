# != DEVELOPER FILE =!

import os
import transformers
import tempfile
from rich.console import Console
import zlib
import shutil

c = Console()

c.print("[bold green]Starting...[/bold green]")

pipe = transformers.pipeline("text-generation", "meta-llama/Llama-3.2-3B-Instruct") # Load Llama

c.print("[bold green]Saving Llama...[/bold green]")

temp_file = tempfile.TemporaryDirectory(dir=os.path.curdir, delete=True)

pipe.save_pretrained(temp_file.name) # Save Llama to a temporary directory

c.print("[bold green]Compressing...[/bold green]")

# Create models directory if it doesn't exist
os.makedirs(os.path.join(os.path.curdir, "models"), exist_ok=True)

# Create a zip archive of the temporary directory
output_path = os.path.join(os.path.curdir, "models", "llama.bin")

# Read all files and compress with zlib
with open(output_path, 'wb') as f:
    # Walk through the directory and compress all files
    for root, dirs, files in os.walk(temp_file.name):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, 'rb') as source_file:
                data = source_file.read()
                compressed_data = zlib.compress(data, level=9)  # Maximum compression
                f.write(compressed_data)

c.print("[bold green]Finished![/bold green]")

temp_file.close() # Delete the temporary directory

c.print("[bold green]Cleanup finished.[/bold green]")
