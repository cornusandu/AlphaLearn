import os
import shutil
import zipfile
from ntpath import isfile
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

    # Colectăm informații pentru afișare
    for model_name in os.listdir(get_local_file("models")):
        model_dir = get_local_file("models", model_name)
        if os.path.isfile(model_dir):
            continue
        for content in os.listdir(model_dir):
            if not content.endswith(".zip"):
                continue
            zip_path = get_local_file("models", model_name, content)
            if not os.path.isfile(zip_path):
                continue
            size = os.path.getsize(zip_path)
            est_unz = size * ((1 / RATIO) + 0.05) + 8
            files += 1
            total_uncompressed_size += est_unz
            data.add_row(model_name, to_readable(size), to_readable(est_unz))

    c.print("Extracting models from compressed archive. Please wait, this may take a while.\n")
    c.print(data)
    c.print("\n", end="")

    # Verificăm spațiul pe disc
    available_disk_space = shutil.disk_usage(get_local_file("models")).free
    if available_disk_space < total_uncompressed_size:
        c.print(f"[bold red]Not enough disk space to extract models. Please free up {to_readable(total_uncompressed_size - available_disk_space)}[/bold red]")
        return False

    if not Confirm.ask(f"[bold]This will use ~{to_readable(total_uncompressed_size)} of your disk space. Continue?[/bold]", default=True):
        return False

    # Începem extragerea cu progres
    p = Progress()
    p.start()
    t = p.add_task("Extracting", total=files)

    for model_name in os.listdir(get_local_file("models")):
        model_dir = get_local_file("models", model_name)
        if os.path.isfile(model_dir):
            continue

        # Identificăm toate fragmentele și le sortăm
        fragments = sorted(
            f for f in os.listdir(model_dir)
            if f.startswith(model_name) and (f.endswith(".z01") or f.endswith(".z02") or f.endswith(".zip"))
        )
        if not fragments:
            continue

        # Creăm calea fișierului temporar combinat
        combined_path = os.path.join(model_dir, f"{model_name}-combined.zip")
        with open(combined_path, "wb") as wfd:
            for frag in fragments:
                frag_path = os.path.join(model_dir, frag)
                with open(frag_path, "rb") as rfd:
                    shutil.copyfileobj(rfd, wfd)

        # Extragem din combined.zip și apoi îl ștergem
        with zipfile.ZipFile(combined_path, "r") as zip_ref:
            zip_ref.extractall(model_dir)
        os.remove(combined_path)

        p.advance(t, 1)

    p.stop()
    c.print("\n[bold green]Finished![/bold green]")
    return True
