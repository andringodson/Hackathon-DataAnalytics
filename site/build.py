"""Assemble the static GitHub Pages site: stlite loader + dashboard source + aggregated CSVs."""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "_site"
if out.exists():
    shutil.rmtree(out)
out.mkdir(parents=True)
shutil.copy(ROOT / "site" / "index.html", out / "index.html")
files = [ROOT / "dashboard" / "app.py", *sorted((ROOT / "data" / "processed").glob("*.csv"))]
for f in files:
    dest = out / f.relative_to(ROOT)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(f, dest)
(out / "manifest.json").write_text(json.dumps([f.relative_to(ROOT).as_posix() for f in files], indent=1))
(out / ".nojekyll").touch()
print(f"{len(files)} files -> {out}")
