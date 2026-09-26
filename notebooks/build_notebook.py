"""Assemble notebooks/src/*.py (percent-format cells) into notebooks/VoltRelay_Analysis.ipynb."""
import re
import sys
from pathlib import Path

import nbformat

HERE = Path(__file__).resolve().parent
OUT = HERE / "VoltRelay_Analysis.ipynb"
MARKER = re.compile(r"^# %%(?: \[(markdown)\])?\s*$")


def cells_from(path):
    cells, kind, buf = [], None, []

    def flush():
        text = "\n".join(buf).strip("\n")
        if kind is None or not text:
            return
        if kind == "markdown":
            text = "\n".join(line[2:] if line.startswith("# ") else line.lstrip("#") for line in text.splitlines())
            cells.append(nbformat.v4.new_markdown_cell(text))
        else:
            cells.append(nbformat.v4.new_code_cell(text))

    for line in path.read_text(encoding="utf-8").splitlines():
        m = MARKER.match(line)
        if m:
            flush()
            kind, buf = (m.group(1) or "code"), []
        else:
            buf.append(line)
    flush()
    return cells


def main(out=OUT):
    nb = nbformat.v4.new_notebook()
    nb.metadata = {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                   "language_info": {"name": "python"}, "colab": {"provenance": []}}
    for part in sorted((HERE / "src").glob("*.py")):
        nb.cells.extend(cells_from(part))
    nbformat.write(nb, str(out))
    print(f"{len(nb.cells)} cells -> {out}")


if __name__ == "__main__":
    main(*(Path(a) for a in sys.argv[1:]))
