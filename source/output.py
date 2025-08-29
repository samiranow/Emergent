import os

def save_to_file(path: str, lines: list):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Saved: {path} | Lines: {len(lines)}")
