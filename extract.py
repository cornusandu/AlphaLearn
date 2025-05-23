from ntpath import isfile
import zipfile
import os
import shutil
from rich.console import Console
from rich.progress import Progress
from rich.table import Table
from rich.prompt import Confirm
from utils import get_local_file, to_readable

c: Console | None = None

RATIO = 0.44  # COMPRESSION RATIO (COMPRESSED_SIZE/ORIGINAL_SIZE)

def provide_console(console: Console):
    global c
    c = console

def extract_models():
    global c
    if not c:
        c = Console()
    data = Table()
    data.add_column("Model Name")
    data.add_column("Size")
    data.add_column("Estimated Uncompressed Size")
    files: int = 0
    total_uncompressed_size: int = 0
    # QUICKLY GATHER DATA ABOUT THE FILES
    for model_name in os.listdir(get_local_file("models")):
        if os.path.isfile(get_local_file("models", model_name)): continue
        for content in os.listdir(get_local_file("models", model_name)):
            if not content.endswith(".zip"): continue
            if not os.path.isfile(get_local_file("models", model_name, content)): continue
            files += 1
            total_uncompressed_size += os.path.getsize(get_local_file("models", model_name, content)) * ((1 / RATIO)+0.05)  +  8  # ADD 0.1 TO ACCOUNT FOR MARGIN OF ERROR  ||  ADD 8 BYTES TO ACCOUNT FOR POTENTIAL INDEXING
            data.add_row(model_name, to_readable(os.path.getsize(get_local_file("models", model_name, content))), to_readable(os.path.getsize(get_local_file("models", model_name, content)) * ((1 / RATIO)+0.05)))

    c.print("Extracting models from compressed archive. Please wait, this may take a while.\n")
    c.print(data)
    c.print("\n", end="")

    available_disk_space = shutil.disk_usage(get_local_file("models")).free
    if available_disk_space < total_uncompressed_size:
        c.print(f"[bold red]Not enough disk space to extract models. Please free up {to_readable(total_uncompressed_size - available_disk_space)}[/bold red]")
        return False

    confirm = Confirm.ask(f"[bold][ ]This will use ~{to_readable(total_uncompressed_size)} of your disk space. Continue?[/bold]", default=True)
    if not confirm:
        return False

    # EXTRACT FILES
    p = Progress()
    p.start()
    t = p.add_task("Extracting", total=files)
    for model_name in os.listdir(get_local_file("models")):
        if os.path.isfile(get_local_file("models", model_name)): continue
        for content in os.listdir(get_local_file("models", model_name)):
            if not content.endswith(".zip"): continue
            if not isfile(get_local_file("models", model_name, content)): continue
            with zipfile.ZipFile(get_local_file("models", model_name, content), "r") as zip_ref:
                zip_ref.extractall(get_local_file("models", model_name))
                p.advance(t, 1)

    p.stop()
    c.print("\n[bold green]Finished![/bold green]")
    return True
