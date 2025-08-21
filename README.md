# Fibrates-Biliary ADEs SRS Reproducible Code (MSIP + Python)

This repository provides **MSIP node scripts (Python)** and **SQL-like pseudocode** to reproduce analysis of **biliary adverse drug events (ADEs) potentially associated with fibrates** using spontaneous reporting systems (SRS) such as FAERS and JADER.

> This code is intended to run **inside MSIP** (ALKANO/MSI pipeline). CLI wrappers are not included; node scripts consume MSIP tables (`table`, `table1`, …) and return `result` MSIP DataFrames.

## Quickstart

```bash
# Python 3.13 is recommended
python -V

# Create and activate a virtual environment
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# (If using cmd.exe: .\.venv\Scriptsctivate.bat)

# Install dependencies
pip install -r requirements.txt
```

**MSIP usage (conceptual):**
- Import scripts from `scripts/` into your MSIP nodes.
- Provide the expected input tables (see “Node map & I/O” below).
- Results are written to MSIP outputs and, when relevant, CSVs under `outputs/`.

## Repository Structure

```
├─ scripts/                          # MSIP Python nodes
│  ├─ node_001_demo_bmi.py           # DEMO numeric conversion (+5 adjust) & BMI
│  ├─ node_002_drug_counts_unified.py# JADER/FAERS auto-detect → num_drugs & case_id
│  ├─ node_003_normalize_drug_names_simple.py  # normalize 'drug_of_interest' (both DS)
│  ├─ node_004_metrics.py            # 2x2 → ROR/PRR/IC, Fisher p, χ²
│  ├─ node_005_ebgm.py               # EBGM (MGPS-like; deterministic seed=12345)
│  ├─ node_006_tto_earliest_pair.py  # earliest valid (start,event) pair per group
│  └─ node_007_faers_demo_dedup.py   # FAERS DEMO: caseid→max(caseversion)
│
├─ sql/                              # SQL-like pseudocode (dataset-agnostic)
│  ├─ 00_conventions.md
│  ├─ 10_plid.md
│  ├─ 20_disproportionality.md
│  ├─ 30_stratified.md
│  ├─ 40_time_to_onset.md
│  ├─ 50_ebgm.md
│  └─ 90_figures.md
│
├─ data/
│  └─ README.md                      # how to obtain/place data (no raw data in repo)
├─ outputs/                          # generated tables/figures (created at runtime)
├─ requirements.txt
├─ .gitignore
├─ LICENSE                           # MIT License
└─ README.md
```

## Data Layout (not distributed)

This project **does not** distribute FAERS/JADER source files. Please obtain them according to the respective licenses/institutional policies.

Place files as:
- `data/raw/`   : original SRS tables (FAERS/JADER), untouched  
- `data/parsed/`: intermediate normalized tables (created)  
- `outputs/`    : final results (created)

See `data/README.md` for exact filenames and expected columns.

## Reproducibility

- **Python:** 3.13  
- **OS (tested):** Windows 11  
- **Packages:** pinned in `requirements.txt` (SciPy required for metrics/EBGM)  
- **Randomness:** fixed seeds where applicable
  - `node_005_ebgm.py`: **BASE_SEED = 12345** (NumPy RNG; deterministic sampling)
  - elsewhere: settable by MSIP node parameters if needed

> Repository policy: **English/ASCII only** for file names and text.

## Analysis Policies (summary)

- **Signal metrics:** ROR, PRR, IC computed from **2×2** counts. IC uses a WHO-style closed-form (see `node_004_metrics.py`).  
- **Time-to-onset (TTO):** default scope is **Pemafibrate only**; earliest valid `(start_date, event_date)` pair; negative TTO excluded; `(event - start) + 1` days.  
- **Join policy (TTO):** prefer **FULL OUTER JOIN** for `DRUG`↔`REAC` at case level, then filter to valid date pairs (see `sql/40_time_to_onset.md`).  
- **Dataset IDs:** JADER = `識別番号`, FAERS = `primaryid` → both normalized to **`case_id`** upstream (`node_002_*`).

## Node map & I/O (MSIP)

- **node_001 (`scripts/node_001_demo_bmi.py`)**  
  Input: DEMO-like table (`体重`, `身長`, `年齢`) → Output: adds `WEIGHT`, `HEIGHT`, `AGE`, `BMI` (+ helpers).

- **node_002 (`scripts/node_002_drug_counts_unified.py`)**  
  Auto-detects JADER/FAERS, outputs **`num_drugs`** and **`case_id`** (plus `服薬数`/`number_of_drug` for compatibility).

- **node_003 (`scripts/node_003_normalize_drug_names_simple.py`)**  
  Normalizes **`drug_of_interest`** via substring mappings (`yure_dict`).

- **node_004 (`scripts/node_004_metrics.py`)**  
  Inputs: totals table (`n++`, `n+1`) as `table`; per-drug table (`drug`, `n1+`, `n11`) as `table1`.  
  Outputs: per-drug **`n11, n12, n21, n22, ROR, PRR, IC, Fisher p, χ²`**.

- **node_005 (`scripts/node_005_ebgm.py`)**  
  Input: `table_027`-like wide table with **`drug_of_interest, Subgroup, n11, n12, n21, n22`** (Overall + subgroup rows).  
  Output: per-drug **`E0, O, n1+, n+1, n++, EBGM, EBGM05, EBGM95, MGPS_Signal`** (`table_028`).  
  Notes: Subgroup rows are aggregated to compute E0; **deterministic sampling** (seed=12345).

- **node_006 (`scripts/node_006_tto_earliest_pair.py`)**  
  Input: table with date columns at **indices 2 (start) and 4 (event)**; groups = other columns.  
  Output: retains **earliest pair** per group; optionally enforce `start <= event`.

- **node_007 (`scripts/node_007_faers_demo_dedup.py`)**  
  Input: FAERS DEMO (`caseid`, `caseversion`); Output: **max(caseversion)** per `caseid` (use `primaryid` downstream).

## Figures/Tables ↔ Code Mapping (MSIP)

- **node_004** = 2×2 metrics → (optional) export `outputs/metrics.csv`  
- **node_005** = EBGM (`table_027` → `table_028`) → (optional) export under `outputs/tables/`  
- **node_006** = TTO earliest-pair → KM-ready CSV under `outputs/km_raw/`

For naming/versioning of figures/tables and metadata cataloging, see `sql/90_figures.md`.

## SQL Pseudocode

See `sql/*.md` for dataset-agnostic pseudocode. The flow aligns with the Word spec:  
1) conventions/aliases, 2) PLID, 3) disproportionality, 4) stratified & export `table_024′` → concat → **import `table_027`**, 5) EBGM in Python (**node_005**) → **`table_028`**, 6) figures.

## How to Cite

If you use this code, please cite:

```
Satoko Watanabe, Fibrates-Biliary ADEs SRS Reproducible Code (MSIP + Python), <YEAR>, <URL/DOI>.
```

A machine-readable citation file (`CITATION.cff`) is recommended once the metadata is ready.

## License

**MIT** — see `LICENSE`.

## Contact

- **Corresponding:** Satoko Watanabe  
- **Affiliation:** Sagara Laboratory  
- **Email:** hsagara.laboratory@gmail.com

## Roadmap / TODO

- [ ] Add `examples/` with minimal CSVs and run notes
- [ ] Add `outputs/_catalog.json` for figure/table provenance
- [ ] Add CI (GitHub Actions) smoke test on Python 3.13
- [ ] Add `CITATION.cff` with authors, title, version, date
