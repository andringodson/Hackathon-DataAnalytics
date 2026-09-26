# VoltRelay Energy — Battery-Swap Network Analysis

Submission for the **Gradient Learnings Data Analytics Hackathon**.

VoltRelay Energy runs a battery-swapping network for electric two- and three-wheelers across six Indian
cities. Between January 2024 and June 2025 swaps and revenue grew, but service failures rose faster,
new-rider retention fell and per-swap profitability eroded. This project investigates why.

> Work in progress — analysis, report and dashboard are being added.

## Repository layout

| Path | Contents |
|---|---|
| `data/download_data.py` | Pulls the eight raw CSVs (~1 GB) from the organiser's Google Drive into `data/raw/` |

## Reproducing

```bash
pip install gdown pandas numpy
python data/download_data.py
```
