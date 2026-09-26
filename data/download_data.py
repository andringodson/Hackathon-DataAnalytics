"""Download the eight hackathon CSVs from the organiser's Google Drive folder into data/raw/."""
import sys
from pathlib import Path

import gdown

DRIVE_FOLDER = "https://drive.google.com/drive/folders/1qsjGWrgmEvOaf2Is2fh7RgVEkKd1V3df"
EXPECTED = [
    "swap_events", "station_hourly_status", "riders", "batteries",
    "support_tickets", "stations", "city_daily_context", "fleet_partners",
]


def main(out_dir: str = "data/raw") -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    gdown.download_folder(DRIVE_FOLDER, output=str(out), quiet=False, remaining_ok=True)
    present = {p.name.split(".")[0] for p in out.rglob("*.csv*")}
    missing = [t for t in EXPECTED if t not in present]
    if missing:
        sys.exit(f"Missing tables after download: {missing}")
    print(f"All {len(EXPECTED)} tables downloaded to {out.resolve()}")


if __name__ == "__main__":
    main(*sys.argv[1:])
