# Fibrates-Biliary ADEs SRS Reproducible Code (MSIP + Python)

This repository publishes **SQL-like pseudocode** and **MSIP Python node scripts** used in an English-language paper on **biliary adverse events potentially associated with fibrates**.  
It is designed for **code transparency and review** — **datasets and outputs are *not* included**.

> The Python scripts are intended to run **inside MSIP** (ALKANO/MSI pipeline). They consume MSIP tables (e.g., `table`, `table1`) and must return `result` (MSIP DataFrame). No standalone CLI is provided.

## Quickstart (environment only)

```bash
# Python 3.13
python -V

# (Optional) virtual environment
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

## Repository Structure (minimal, code-only)

```
├─ scripts/                          # MSIP Python nodes
│  ├─ node_001_demo_bmi.py
│  ├─ node_002_drug_counts_unified.py
│  ├─ node_003_normalize_drug_names_simple.py
│  ├─ node_004_metrics.py
│  ├─ node_005_ebgm.py
│  ├─ node_006_tto_earliest_pair.py
│  └─ node_007_faers_demo_dedup.py
│
├─ sql/                              # SQL-like pseudocode
│  ├─ 00_conventions.md
│  ├─ 10_plid.md
│  ├─ 20_disproportionality.md
│  ├─ 30_stratified.md
│  ├─ 40_time_to_onset.md
│  ├─ 50_ebgm.md
│  └─ 90_figures.md
│
├─ data/
│  └─ README.md                      # data expectations (placement & columns only)
│
├─ requirements.txt
├─ .gitignore
├─ LICENSE                           # MIT
└─ README.md                         # (this file)
```

> **Note**: Folders like `outputs/`, `data/raw/`, `data/parsed/` are **not included** in this repository to keep it code-only.  
> At runtime in your environment, create them as needed. See `data/README.md` for expected layouts.

## Reproducibility & Policies (summary)

- **Python:** 3.13 / **OS (tested):** Windows 11  
- **Packages:** see `requirements.txt` (SciPy required)  
- **Randomness:** fixed seeds where applicable  
  - `node_005_ebgm.py` uses **BASE_SEED = 12345** (NumPy RNG) for deterministic sampling.

**Analysis policies** (aligned with the Word spec and SQL docs):

- **Signal metrics:** ROR, PRR, IC (WHO-style closed-form) from 2×2 counts (`node_004`).
- **TTO:** default focus **Pemafibrate only**; earliest valid `(start, event)` pair; `(event - start) + 1` days; negative TTO excluded (`node_006`).
- **Join policy (TTO):** use **FULL OUTER JOIN** for `DRUG`↔`REAC` at case level, then filter to valid pairs (see `sql/40_time_to_onset.md`).
- **IDs:** JADER = `識別番号`; FAERS = `primaryid` → normalize upstream to **`case_id`** (`node_002`).

## Node Map & I/O (MSIP)

- **node_001** — DEMO numeric conversion (+5 to weight/height) & BMI  
  *Input:* `体重`, `身長`, `年齢` → *Output:* `WEIGHT`, `HEIGHT`, `AGE`, `BMI` (+ helpers)

- **node_002** — Count drugs per case (auto-detect JADER/FAERS)  
  *Output:* standardized **`case_id`**, **`num_drugs`** (+ compatibility columns: `服薬数` / `number_of_drug`)

- **node_003** — Normalize **`drug_of_interest`** via substring mapping (`yure_dict`)  
  *Assumption:* the column name is already `drug_of_interest` for both datasets.

- **node_004** — 2×2 metrics (ROR/PRR/IC, Fisher p, χ²)  
  *Inputs:* totals (`table`), per-drug counts (`table1`) — see comments in the file for column expectations.

- **node_005** — EBGM (MGPS-like; deterministic)  
  *Input:* `table_027`-like table with `drug_of_interest, Subgroup, n11, n12, n21, n22` (Overall + subgroup rows)  
  *Output:* per-drug `E0, O, n1+, n+1, n++, EBGM, EBGM05, EBGM95, MGPS_Signal` (`table_028`).

- **node_006** — Keep earliest valid `(start, event)` pair per group  
  *Assumption:* date columns are at indices **2 (start)** and **4 (event)**.

- **node_007** — FAERS DEMO de-duplication  
  *Logic:* for each `caseid`, keep row with max(`caseversion`) → use `primaryid` downstream.

## Figures/Tables ↔ Code Mapping

- **node_004** → 2×2 metrics (optionally export as CSV in your environment)  
- **node_005** → EBGM (`table_027` → `table_028`)  
- **node_006** → TTO earliest-pair (KM-ready)

For naming and provenance conventions, see `sql/90_figures.md`.

## SQL Pseudocode Flow

1) conventions/aliases → 2) PLID → 3) disproportionality → 4) stratified & export `table_024′` → concat → **import `table_027`** → 5) EBGM in Python (**node_005**) → **`table_028`** → 6) figures.

## Data (non-distributed)

Data are **not included**. See **`data/README.md`** for: how to obtain/place FAERS/JADER, expected columns, subgroup definitions, and known pitfalls.

## How to Cite

```
Satoko Watanabe, Fibrates-Biliary ADEs SRS Reproducible Code (MSIP + Python), <YEAR>, <URL/DOI>.
```

## License

**MIT** — see `LICENSE`.

## Contact

- **Corresponding:** Satoko Watanabe  
- **Affiliation:** Sagara Laboratory  
- **Email:** hsagara.laboratory@gmail.com
