import json
import os
# import transformers

def get_local_file(path: str, *paths, no_dot: bool = False) -> str:
    return os.path.join(os.path.curdir if not no_dot else '', path, *paths)

def setup_passed() -> bool:
    with open(get_local_file("state.json"), "r") as f:
        return json.load(f)["passed_setup"]

def to_readable(size_bytes: int) -> str:
    if size_bytes <= 1:
        return f"{size_bytes*8}b"
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.2f}KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes/(1024*1024):.2f}MB"
    elif size_bytes < 1024 * 1024 * 1024 * 1024:
        return f"{size_bytes/(1024*1024*1024):.2f}GB"
    elif size_bytes < 1024 * 1024 * 1024 * 1024 * 1024:
        return f"{size_bytes/(1024*1024*1024*1024):.2f}TB"
    elif size_bytes < 1024 * 1024 * 1024 * 1024 * 1024 * 1024:
        return f"{size_bytes/(1024*1024*1024*1024*1024):.2f}PB"
    else:
        return f"{size_bytes/(1024*1024*1024*1024*1024*1024):.2f}EB"
    
