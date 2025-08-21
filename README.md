# Fibrates-Biliary ADEs SRS Reproducible Code (MSIP + Python)

This repository provides Python scripts and SQL pseudocode to reproduce the analysis of **biliary adverse drug events (ADEs) potentially associated with fibrates** using spontaneous reporting systems (SRS) such as FAERS and JADER.  
**Status:** WIP – interfaces are stable; internals may evolve.

## Quickstart

```bash
# Python 3.13 is recommended
python -V

# Create and activate a virtual environment
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# (If using cmd.exe: .\.venv\Scripts\activate.bat)

# Install dependencies
pip install -r requirements.txt

# Run the end-to-end pipeline (example)
python scripts/run_pipeline.py --input data/raw --output outputs
```

## Repository Structure

```
├─ scripts/             # runnable Python scripts (ETL, metrics, figures)
│  ├─ run_pipeline.py   # entry point CLI
│  ├─ etl.py            # parsing / harmonization helpers (TBD)
│  ├─ metrics.py        # counts -> ROR/PRR/IC (TBD)
│  ├─ km_raw.py         # Kaplan-Meier inputs per drug/event (TBD)
│  └─ km_bootstrap.py   # KM bootstrap + IQR (TBD)
├─ sql/
│  └─ pseudocode.md     # SQL pseudocode describing DB operations
├─ data/
│  └─ README.md         # how to obtain/place data (no raw data in repo)
├─ outputs/             # generated tables/figures (created at runtime)
├─ requirements.txt
├─ .gitignore
├─ LICENSE              # <TBD: MIT/Apache-2.0/etc.>
└─ README.md
```

## Data Layout (not distributed)

This project **does not** distribute FAERS/JADER source files. Please obtain them according to the respective licenses/institutional policies.

Place files as:
- `data/raw/`   : original SRS tables (FAERS/JADER), untouched  
- `data/parsed/`: intermediate normalized tables (created)  
- `outputs/`    : final results (created)

See `data/README.md` for exact filenames and expected columns (<TBD>).

## Reproducibility

- **Python:** 3.13  
- **OS (tested):** Windows 11  
- **Packages:** pinned in `requirements.txt`  
- **Randomness:** set seeds where applicable (`--seed`, default 42)

> Repository policy: **English/ASCII only** for file names and text.

## Analysis Policies

- **Signal metrics:** ROR, PRR, and IC computed from 2x2 counts.  
- **Time-to-onset (TTO):** Kaplan-Meier methods for descriptive TTO; optional bootstrap for IQR.  
- **Censoring/Windows:** <TBD>

## Command-Line Interface

```text
python scripts/run_pipeline.py --input <PATH> --output <PATH> [options]

Options:
  --input PATH        Path to source data directory (default: data/raw)
  --output PATH       Path to output directory (default: outputs)
  --n-jobs INT        Parallel workers for heavy steps (default: 1)
  --seed INT          Random seed for reproducible sampling/bootstrap (default: 42)
  --log-level STR     DEBUG|INFO|WARNING|ERROR (default: INFO)
```

## Expected Outputs

- `outputs/counts.csv` — 2x2 counts per (drug, event, strata)  
- `outputs/metrics.csv` — ROR/PRR/IC with CIs and p-values (specs <TBD>)  
- `outputs/km_raw/<drug>__<event>.csv` — KM-ready TTO records (specs <TBD>)  
- `outputs/km_bootstrap/<drug>__<event>.csv` — bootstrap summaries (optional)  
- `outputs/figs/` — key figures (e.g., volcano/scatter, KM curves) (<TBD>)

## Figures/Tables ↔ Code Mapping (MSIP)

If you are executing in **MSIP**, map nodes to scripts as follows (adjust as needed):

- **node_006** = counts -> metrics (`scripts/metrics.py`)  
- **node_014** = KM (raw) per drug with FAERS+JADER (`scripts/km_raw.py`)  
- **node_015** = KM (bootstrap + IQR) (`scripts/km_bootstrap.py`)

## SQL Pseudocode

High-level steps are provided in `sql/pseudocode.md`:
1) input sources and unique case identifier harmonization,  
2) deduplication and drug mapping (ATC/ingredients),  
3) filtering rules/date windows,  
4) counts -> metrics,  
5) outputs.  
Fill in `<TBD>` assumptions inline as you finalize.

## How to Cite

If you use this code, please cite:

```
Satoko Watanabe, Fibrates-Biliary ADEs SRS Reproducible Code (MSIP + Python), <YEAR>, <URL/DOI>.
```

A machine-readable citation file (`CITATION.cff`) is recommended once the metadata is ready.

## License

<TBD: MIT/Apache-2.0/BSD-3>. See `LICENSE`. If unsure, MIT is a simple default.

## Contact

- **Corresponding:** Satoko Watanabe  
- **Affiliation:** Sagara Laboratory  
- **Email:** hsagara.laboratory@gmail.com

## Roadmap / TODO

- [ ] Finalize data schema in `data/README.md` (file list and required columns)
- [ ] Lock analysis policies (e.g., TTO windows, filters) and document them
- [ ] Complete `metrics.py`, `km_raw.py`, and `km_bootstrap.py`
- [ ] Add figure scripts and save under `outputs/figs/`
- [ ] Add `CITATION.cff` with authors, title, version, date
- [ ] Add tested Windows 11 build numbers and Python 3.13.x patch versions
