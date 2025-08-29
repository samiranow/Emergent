import os
from config import OUTPUT_DIR

def save_to_file(filename: str, lines: list):
    path = os.path.join(OUTPUT_DIR, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Saved: {path} | Lines: {len(lines)}")
