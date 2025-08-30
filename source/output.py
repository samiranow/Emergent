# output.py
import os
import logging

def save_to_file(path: str, lines: list):
    if not lines:
        logging.warning(f"No lines to save in {path}")
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    logging.info(f"Saved: {path} | Lines: {len(lines)}")
