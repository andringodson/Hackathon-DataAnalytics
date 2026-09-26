"""Assemble the static GitHub Pages site: HTML/CSS/JS plus one data.json built from data/processed/*.csv.

Every asset URL gets a content hash (?v=...) so browsers and the service worker can cache aggressively
and still pick up each new deploy immediately.
"""
import csv
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "_site"
TEXT = ("index.html", "styles.css", "app.js", "sw.js", "manifest.webmanifest")
BINARY = ("og.png", "icon-180.png", "icon-192.png", "icon-512.png")


def parse(v):
    if v == "":
        return None
    for cast in (int, float):
        try:
            x = cast(v)
            return None if isinstance(x, float) and not math.isfinite(x) else x
        except ValueError:
            pass
    return v


data = {}
for f in sorted((ROOT / "data" / "processed").glob("*.csv")):
    with f.open(encoding="utf-8", newline="") as fh:
        data[f.stem] = [{k: parse(v) for k, v in row.items()} for row in csv.DictReader(fh)]
payload = json.dumps(data, separators=(",", ":"), ensure_ascii=False)

digest = hashlib.sha256(payload.encode())
for name in TEXT:
    digest.update((SITE / name).read_bytes())
version = digest.hexdigest()[:10]

out.mkdir(parents=True, exist_ok=True)
for name in TEXT:
    (out / name).write_text((SITE / name).read_text(encoding="utf-8").replace("__V__", version), encoding="utf-8")
for name in BINARY:
    if (SITE / name).exists():
        shutil.copy(SITE / name, out / name)
(out / "data.json").write_text(payload, encoding="utf-8")
(out / ".nojekyll").touch()
print(f"version {version}: {len(data)} tables, data.json {len(payload) / 1024:.0f} KB -> {out}")
