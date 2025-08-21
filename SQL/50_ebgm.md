# 50_ebgm.md — EBGM (empirical Bayes geometric mean)

This file follows the flow you described in the Word spec:

1) **Stratified results consolidation** → export each subgroup result (a.k.a. `table_024'`) to CSV, add a `Subgroup` column, concatenate into *one* CSV, re-import as **`table_027`**.
2) **EBGM computation** in a **Python node (`node_005`)**: read **`table_027`**, compute **expected counts per Subgroup**, then compute **EBGM per Drug**, and write **`table_028`**.

> Note: For ASCII safety, we will refer to `table_024'` as **`table_024_prime`** when creating file/table names.

---

## A. Consolidate stratified outputs → `table_027`

**Inputs:** one CSV per subgroup level produced from `table_024_prime` (e.g., sex, age band, BMI band), for both datasets (JADER/FAERS).  
Before concatenation, add a `subgroup_name` and `subgroup_level` (and optionally `dataset`) column to each CSV.

**Recommended schema for the concatenated CSV (`table_027_subgroup_counts.csv`):**

- `dataset` : `jader|faers`
- `drug_of_interest` : canonical name (Pemafibrate|Fenofibrate|Bezafibrate)
- `subgroup_name` : `sex|age|bmi` (etc.)
- `subgroup_level` : e.g., `Male|Female`, `20-50s|60s+`, `<25|>=25`
- `n11, n12, n21, n22` : 2x2 counts
- *(optional)* `n_total` : `n11+n12+n21+n22`

**Import to SQL as `table_027`:**

```sql
-- Example DDL (adjust to your SQL dialect)
CREATE TABLE table_027 (
  dataset TEXT,
  drug_of_interest TEXT,
  subgroup_name TEXT,
  subgroup_level TEXT,
  n11 INTEGER,
  n12 INTEGER,
  n21 INTEGER,
  n22 INTEGER
);

-- Import step is dialect-specific (COPY/LOAD DATA). After import:
-- SELECT COUNT(*) FROM table_027;
```

---

## B. EBGM computation → `node_005` (Python) → `table_028`

**Input:** `table_027` (subgroup-level counts).  
**Outputs:**

- **`table_028_subgroup`**: EBGM (and bounds) **per (drug, subgroup_name, subgroup_level)**.
- **`table_028`**: EBGM **per drug** (pooled across subgroups).

> Your original note said “compute expected per Subgroup, EBGM per Drug.” We therefore produce both: the fine-grained *and* the pooled tables. If you want only per-drug output, skip `table_028_subgroup`.

### Expected counts per subgroup

For each row `(drug_of_interest, subgroup_name, subgroup_level)`, compute the expected cell count under independence:

```
expected = ((n11 + n12) * (n11 + n21)) / (n11 + n12 + n21 + n22)
```

This is the same expectation used for disproportionality (rearranged 2x2). Save as `expected` column.

### EBGM (MGPS-style) outline

EBGM is a shrinkage estimator derived from a gamma–Poisson mixture model (DuMouchel). Implement in Python as:

```python
# Pseudocode only
def mgps_ebgm(n11, n12, n21, n22):
    # Prepare observed and expected
    N = n11 + n12 + n21 + n22
    expected = ((n11 + n12) * (n11 + n21)) / max(N, 1)
    # Fit or use prior hyperparameters (alpha1, beta1, alpha2, beta2, p)
    # Compute posterior mixture and EBGM, EB05, EB95
    return EBGM, EB05, EB95
```

If you prefer a pragmatic route, compute EBGM via an existing implementation (e.g., an `openEBGM`-like routine).

### Node I/O and schemas

- **Input**: `table_027`
  - columns: as above
- **Output 1**: `table_028_subgroup`
  - columns: `dataset, drug_of_interest, subgroup_name, subgroup_level, n11, n12, n21, n22, expected, EBGM, EB05, EB95`
- **Output 2**: `table_028`
  - columns: `dataset, drug_of_interest, n11, n12, n21, n22, expected, EBGM, EB05, EB95`
  - created by pooling subgroup rows per `(dataset, drug_of_interest)` before EBGM

### Reproducibility notes

- Record `node_005` parameters, Python/OS versions, and git commit in your figure catalog.  
- Set a fixed `seed` for any resampling/bootstrapping; EBGM itself is deterministic given counts.

---

## Optional: SQL helpers (if you prefer to compute `expected` in SQL)

```sql
-- Per-subgroup expected count (helper view prior to Python)
CREATE VIEW v027_expected AS
SELECT
  dataset, drug_of_interest, subgroup_name, subgroup_level,
  n11, n12, n21, n22,
  ((n11 + n12)::FLOAT * (n11 + n21)::FLOAT) / NULLIF((n11 + n12 + n21 + n22), 0) AS expected
FROM table_027;
```
