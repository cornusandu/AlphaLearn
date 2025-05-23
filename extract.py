from __future__ import annotations

import glob
import os
import re
import shutil
import subprocess
import zipfile
from ntpath import isfile
from typing import List

from rich.console import Console
from rich.progress import Progress
from rich.table import Table
from rich.prompt import Confirm

from utils import get_local_file, to_readable

__all__ = [
    "provide_console",
    "extract_models",
]

#: compression ratio of the archives (compressed / original)
RATIO: float = 0.44
#: chunk size (bytes) used when concatenating split volumes
CHUNK_SIZE: int = 64 * 1024 * 1024  # 64 MiB
#: regex matching split-volume extensions (".z01", ".z02" …)
_SPLIT_RE = re.compile(r"\.z\d{2}$", re.IGNORECASE)

c: Console | None = None

def provide_console(console: Console) -> None:
    """Injectează un :py:class:`rich.console.Console` de către apelant."""
    global c
    c = console


def _combine_split_zip(parts: List[str], combined_path: str, *, chunk_size: int = CHUNK_SIZE) -> None:
    """Concatenează secvențial *parts* într-un fișier *combined_path*."""
    with open(combined_path, "wb") as w:
        for p in parts:
            with open(p, "rb") as r:
                shutil.copyfileobj(r, w, length=chunk_size)


def _extract_one_archive(zip_path: str, destination: str) -> None:
    """Extrage arhiva de la *zip_path* în *destination*.
       Detectează volume spanate, le unește și apoi extrage tot cu zipfile.
    """
    dir_name = os.path.dirname(zip_path)
    base_name = os.path.splitext(os.path.basename(zip_path))[0]

    # Găsește fragmentele .zNN în același folder și prefix
    parts = []
    for fn in os.listdir(dir_name):
        if fn.startswith(base_name) and _SPLIT_RE.search(fn):
            parts.append(os.path.join(dir_name, fn))
    parts_sorted = sorted(parts, key=lambda p: int(re.search(r"(\d{2})$", p).group(1))) if parts else []

    if parts_sorted:
        # Include fișierul .zip la sfârșit
        parts_sorted.append(zip_path)
        combined = os.path.join(dir_name, f"{base_name}.combined.zip")
        if not os.path.exists(combined):
            _combine_split_zip(parts_sorted, combined)
        to_open = combined
    else:
        to_open = zip_path

    # Încearcă extragerea cu zipfile
    try:
        with zipfile.ZipFile(to_open, "r") as zf:
            zf.extractall(destination)
    except zipfile.BadZipFile:
        # Dacă zipfile eșuează și avem split-uri, fallback la 7z
        if parts_sorted and shutil.which("7z"):
            subprocess.run(["7z", "x", zip_path, f"-o{destination}"], check=True)
        else:
            raise
    finally:
        if parts_sorted and os.path.exists(combined):
            os.remove(combined)


def extract_models() -> bool:
    """Extrage toate arhivele (split sau nu) din subfolderul models/"""
    global c
    if not c:
        c = Console()

    data = Table()
    data.add_column("Model Name")
    data.add_column("Compressed Size")
    data.add_column("Estimated Uncompressed Size")

    archives: List[tuple[str, str]] = []
    total_uncompressed = 0
    models_root = get_local_file("models")

    for model in os.listdir(models_root):
        model_dir = os.path.join(models_root, model)
        if not os.path.isdir(model_dir):
            continue

        size_parts = 0
        for fn in os.listdir(model_dir):
            if fn.lower().endswith(tuple([".zip"] + [f".z{str(i).zfill(2)}" for i in range(1, 100)])):
                path = os.path.join(model_dir, fn)
                if os.path.isfile(path):
                    size_parts += os.path.getsize(path)

        if size_parts == 0:
            continue

        primary_zip = os.path.join(model_dir, f"{model}.zip")
        if not os.path.exists(primary_zip):
            for fn in os.listdir(model_dir):
                if fn.lower().endswith(".zip"):
                    primary_zip = os.path.join(model_dir, fn)
                    break

        archives.append((model_dir, primary_zip))
        est = size_parts * ((1 / RATIO) + 0.05) + 8
        total_uncompressed += est
        data.add_row(model, to_readable(size_parts), to_readable(est))

    c.print("Extracting models from compressed archive. Please wait, this may take a while.\n")
    c.print(data)
    c.print("\n", end="")

    free = shutil.disk_usage(models_root).free
    if free < total_uncompressed:
        c.print(f"[bold red]Not enough disk space. Free up {to_readable(total_uncompressed - free)}[/bold red]")
        return False

    if not Confirm.ask(f"[bold][ ]This will use ~{to_readable(total_uncompressed)} disk. Continue?[/bold]", default=True):
        return False

    p = Progress()
    p.start()
    task = p.add_task("Extracting", total=len(archives))

    for model_dir, zip_path in archives:
        if not isfile(zip_path):
            p.advance(task)
            continue
        _extract_one_archive(zip_path, model_dir)
        p.advance(task)

    p.stop()
    c.print("\n[bold green]Finished![/bold green]")
    return True
