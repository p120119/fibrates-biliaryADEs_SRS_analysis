# 20_disproportionality.md — Case extraction and 2x2 metrics (ROR/PRR/IC)

## Common helpers

```sql
-- Canonical drug_of_interest view per dataset
CREATE VIEW {ds}_drug_of_interest AS
SELECT
  {id_col}   AS case_id,
  m.canonical AS drug_of_interest,
  {drug_seq} AS drug_seq
FROM {drug_table} d
JOIN fibrate_name_map m
  ON UPPER(TRIM(d.{drug_col})) = UPPER(TRIM(m.raw_name));
-- {ds} in {jader, faers}; columns set via mapping.
```

```sql
-- Biliary events per dataset
CREATE VIEW {ds}_biliary_events AS
SELECT
  {id_col} AS case_id,
  {event_col} AS event_term
FROM {reac_table} r
JOIN biliary_pt_list b
  ON UPPER(TRIM(r.{event_col})) = UPPER(TRIM(b.pt));
```

## JADER: extract and join

```sql
-- Rename for clarity (MSIP column rename step)
-- table_DRUG."医薬品（一般名）" -> drug_of_interest handled via view above.

-- Inner joins to enforce both drug exposure and biliary event
CREATE VIEW jader_fibrate_biliary AS
SELECT DISTINCT a.case_id, a.drug_of_interest
FROM jader_drug_of_interest a
JOIN jader_biliary_events b USING (case_id);

-- Totals for 2x2
CREATE VIEW jader_all_cases AS
SELECT COUNT(DISTINCT case_id) AS n_all FROM table_DRUG;  -- or PLID base
```

## FAERS: extract and join

```sql
CREATE VIEW faers_fibrate_biliary AS
SELECT DISTINCT a.case_id, a.drug_of_interest
FROM faers_drug_of_interest a
JOIN faers_biliary_events b USING (case_id);

CREATE VIEW faers_all_cases AS
SELECT COUNT(DISTINCT case_id) AS n_all FROM table_DRUG;  -- or PLID base
```

## 2x2 counts per drug_of_interest

> Compute n11, n12, n21, n22 where rows = exposure (fibrate yes/no), columns = event (biliary yes/no).

```sql
-- Exposed with event (n11)
CREATE VIEW {ds}_n11 AS
SELECT drug_of_interest, COUNT(DISTINCT case_id) AS n11
FROM {ds}_fibrate_biliary
GROUP BY drug_of_interest;

-- Exposed total
CREATE VIEW {ds}_n1_ AS
SELECT drug_of_interest, COUNT(DISTINCT case_id) AS n1dot
FROM {ds}_drug_of_interest
GROUP BY drug_of_interest;

-- Event total (any drug)
CREATE VIEW {ds}_ _1 AS
SELECT 'Overall' AS drug_of_interest, COUNT(DISTINCT case_id) AS ndot1
FROM {ds}_biliary_events;

-- All cases count (scalar)
-- {ds}_all_cases provides n_all
```

```sql
-- Assemble 2x2 per drug
CREATE VIEW {ds}_twobytwo AS
SELECT
  a.drug_of_interest,
  COALESCE(n11.n11, 0)                              AS n11,
  GREATEST(a.n1dot - COALESCE(n11.n11, 0), 0)       AS n12,
  GREATEST(e.ndot1 - COALESCE(n11.n11, 0), 0)       AS n21,
  GREATEST(allc.n_all - a.n1dot - e.ndot1 + COALESCE(n11.n11, 0), 0) AS n22
FROM {ds}_n1_ a
LEFT JOIN {ds}_n11 n11 USING (drug_of_interest)
CROSS JOIN {ds}_ _1 e
CROSS JOIN {ds}_all_cases allc;
```

## Metrics (ROR, PRR, IC)

```sql
-- Pseudocode for metrics (exact formulas implemented in Python if preferred)
CREATE VIEW {ds}_metrics AS
SELECT
  drug_of_interest,
  n11, n12, n21, n22,
  -- ROR and Wald 95% CI on log scale
  (n11::FLOAT / n12) / NULLIF(n21::FLOAT / n22, 0)          AS ROR,
  EXP(LN((n11+0.5)/(n12+0.5)) - LN((n21+0.5)/(n22+0.5)) - 1.96*SQRT(1/(n11+0.5)+1/(n12+0.5)+1/(n21+0.5)+1/(n22+0.5))) AS ROR025,
  EXP(LN((n11+0.5)/(n12+0.5)) - LN((n21+0.5)/(n22+0.5)) + 1.96*SQRT(1/(n11+0.5)+1/(n12+0.5)+1/(n21+0.5)+1/(n22+0.5))) AS ROR975,
  -- PRR
  (n11::FLOAT / (n11+n12)) / NULLIF((n11+n21)::FLOAT / (n11+n12+n21+n22), 0)  AS PRR,
  -- IC (simple log2 disproportionality)
  LOG(2, NULLIF(n11::FLOAT / ((n11+n12)*(n11+n21)/(n11+n12+n21+n22)),0)) AS IC
FROM {ds}_twobytwo;
```
