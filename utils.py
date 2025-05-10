import json
import os
# import transformers

def get_local_file(path: str, *paths) -> str:
    return os.path.join(os.path.dirname(__file__), path, *paths)

def setup_passed() -> bool:
    with open(get_local_file("state.json"), "r") as f:
        return json.load(f)["passed_setup"]
