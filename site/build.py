"""Assemble the static GitHub Pages site: HTML/CSS/JS plus one data.json built from data/processed/*.csv."""
import csv
import json
import math
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "_site"


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

out.mkdir(parents=True, exist_ok=True)
for name in ("index.html", "styles.css", "app.js"):
    shutil.copy(ROOT / "site" / name, out / name)
(out / "data.json").write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
(out / ".nojekyll").touch()
print(f"{len(data)} tables -> {out / 'data.json'} ({(out / 'data.json').stat().st_size / 1024:.0f} KB)")
