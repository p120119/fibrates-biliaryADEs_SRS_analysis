# data/README

This folder describes **how external data should be prepared and placed** so that the analysis can be reproduced.  
**No datasets are distributed** in this repository (please obtain FAERS/JADER according to their licenses and policies).

## Scope & Goal
- **Datasets:** FAERS and JADER (spontaneous reporting systems)
- **Goal:** Reproduce disproportionality, subgroup, TTO, and EBGM analyses for **biliary adverse events** (PT14) associated with **fibrates** (pema-/feno-/bezafibrate).

## Directory Layout (when you run locally)
```
data/
├─ raw/        # as-downloaded originals (unmodified; not tracked)
└─ parsed/     # normalized CSVs after basic preprocessing (trackable)
```
Tracking policy follows `.gitignore`. In this public repo we **do not** ship `raw/` or outputs.

## Acquisition (overview)
- **FAERS:** Download quarterly DEMO/DRUG/REAC/OUTC/INDI/THER from FDA (ZIP/TSV/fixed-width).
- **JADER:** Download CSVs from PMDA.

> Normalize to **UTF-8 (no BOM), comma-separated CSV** and place them under `data/parsed/` in your local environment.

## Format & Encoding Normalization
- Encoding: **UTF-8** (JADER is often Shift_JIS — convert to UTF-8).
- Newlines: LF (`\n`).
- Delimiter: comma; **wide** CSV with a single header row.
- Dates: `YYYY-MM-DD` (leave unknowns blank).

## File Naming (recommended)
```
data/parsed/
  faers_DEMO.csv
  faers_DRUG.csv
  faers_REAC.csv
  faers_OUTC.csv      # optional
  faers_INDI.csv      # optional
  jader_DEMO.csv
  jader_DRUG.csv
  jader_REAC.csv
  jader_HIST.csv      # optional
```
Optional tables are not strictly required for this pipeline but may help with PLID or auxiliary steps.

## Minimum Required Columns (referenced by this pipeline)

### JADER
- **DEMO**: `識別番号` (case identifier), `年齢`, `体重`, `身長`, `性別`
- **DRUG**: `識別番号`, `医薬品（一般名）`, `医薬品連番`, `投与開始日`
- **REAC**: `識別番号`, `有害事象`, `有害事象発現日`

### FAERS
- **DEMO**: `caseid`, `caseversion`, `primaryid`, `age`, `age_cod`, `sex`, `wt`, `wt_cod`
- **DRUG**: `primaryid`, `drug_seq`, `prod_ai`, `start_dt`
- **REAC**: `primaryid`, `pt`, `event_dt`

> **ID normalization:** upstream, create a common **`case_id`** (JADER: `識別番号` / FAERS: `primaryid`).  
> **Drug-name normalization:** ensure a **`drug_of_interest`** column (handled by `node_003`).

## Subgroup Definitions (stratification)
- **Sex**: normalize to `Male` / `Female` (e.g., JADER `'男性' → 'Male'`).
- **Age bands**: use **only** JADER values that contain “`○○歳代`”. Extract the **two-digit decade** via the regex `([0-9]{2})\s*歳代`; then map  
  - `20–50s` for decades `20/30/40/50`; `60s+` for decades `>=60`.  
  - Records **without** the `歳代` pattern (e.g., `55歳`, `不明`, `10歳未満`) are **excluded** from stratification (treated as missing).
- **BMI**: computed as `kg / m^2` **after** the +5 adjustments to weight/height in `node_001`; round to 2 decimals.  
  - BMI cut points: `<25` vs `>=25`.

## Event Definition (biliary)
- **PT list (14 terms):** replace the placeholder list `biliary_pt_list` in `sql/00_conventions.md` with the **actual list** used in the study.  
- Matching columns: JADER = `有害事象`, FAERS = `pt`. Normalize case/width (full/half-width) as needed.

## Recommended Preprocessing
1. Convert encodings (Shift_JIS → UTF-8).
2. Unify column names and add **ASCII aliases** when helpful (e.g., `case_id`, `drug_of_interest`).  
3. Normalize date columns to `YYYY-MM-DD` and blank out invalids.
4. **FAERS DEMO de-dup:** keep the row with **max(`caseversion`) per `caseid`**, then use `primaryid` as the key downstream.
5. Clarify missing/non-numeric values (e.g., extract decades for age; extract numbers for weight/height and apply +5).

## Consistency Checks (quick list)
- **Key integrity:** `case_id` joins across DEMO/DRUG/REAC; no NULLs.  
- **Uniqueness:** FAERS DEMO is one row per `caseid` after de-duplication.  
- **Counts sanity:** distribution of `drug_seq` looks reasonable.  
- **TTO readiness:** both `start_dt/投与開始日` and `event_dt/有害事象発現日` are sufficiently populated.  
- **Subgroup completeness:** exclude NULLs before adding to denominators.

## Known Pitfalls
- **Wrong ID column:** FAERS uses `primaryid`; JADER uses `識別番号`. Normalize to `case_id` early.  
- **Joining FAERS on `caseid`:** mixes versions and double-counts — use **`primaryid`** for joins.  
- **Encoding / full-width vs half-width issues:** fix via UTF-8 normalization and mapping dictionaries.  
- **Negative TTO:** rows with `event < start` must be excluded (`node_006` can enforce this).

## Example: Minimal CSV (dummy)
```
data/parsed/jader_DRUG.csv
識別番号,医薬品（一般名）,医薬品連番,投与開始日
J001,ペマフィブラート,1,2021-04-01
J001,ベザフィブラート,2,2021-04-10

data/parsed/jader_REAC.csv
識別番号,有害事象,有害事象発現日
J001,胆嚢炎,2021-04-12
```
These two small files are enough to test `node_006` (earliest valid pair) and TTO conversion.

## Nodes Used from This Repo
- `scripts/node_002_drug_counts_unified.py` — create `num_drugs` and `case_id` (JADER/FAERS)  
- `scripts/node_003_normalize_drug_names_simple.py` — normalize `drug_of_interest`  
- `scripts/node_004_metrics.py` — compute 2×2 metrics  
- `scripts/node_005_ebgm.py` — EBGM (deterministic)  
- `scripts/node_006_tto_earliest_pair.py` — earliest valid `(start,event)` pair  
- `scripts/node_007_faers_demo_dedup.py` — FAERS DEMO de-dup

## Disclaimer & Distribution
- This repository **does not distribute data**. Follow FAERS/JADER licenses and policies.  
- Do not include personal or sensitive identifiers; ensure privacy protection when preparing data.
