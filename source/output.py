import os
from config import OUTPUT_DIR

def save_to_file(filename: str, lines: list):
    """
    Save a list of configuration lines to a file in the output directory.
    """
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Saved: {path} | Lines: {len(lines)}")
