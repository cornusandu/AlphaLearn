# != DEVELOPER FILE =!

# download.py

import zlib
import shutil
from huggingface_hub import snapshot_download

def main():
    # 1. Download the model repository
    repo_dir = snapshot_download("meta-llama/Llama-3.2-3B-Instruct")
    print(f"Model downloaded to {repo_dir}")

    # 2. Pack it into a tar archive
    tar_path = shutil.make_archive("Llama-3.2-3B-Instruct", format="tar", root_dir=repo_dir)
    print(f"Created tar archive at {tar_path}")

    # 3. Compress with zlib (max compression)
    data = open(tar_path, "rb").read()
    compressed = zlib.compress(data, level=9)
    with open("Llama-3.2-3B-Instruct.tar.zlib", "wb") as f:
        f.write(compressed)
    print("Compressed archive saved as Llama-3.2-3B-Instruct.tar.zlib")

if __name__ == "__main__":
    main()
