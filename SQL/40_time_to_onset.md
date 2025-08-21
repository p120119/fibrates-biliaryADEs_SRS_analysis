# 40_time_to_onset.md — TTO preparation for KM analysis

## JADER

### Scope and Join Policy (Aligned with Word flow)

- **Default drug scope:** *Pemafibrate only*. (Fenofibrate/Bezafibrate can be enabled via a parameter.)
- **Joins:** Use **FULL OUTER JOIN** between DRUG and REAC at the case level, then later filter to valid date pairs and apply earliest-pair selection.
- **Earliest pair:** Keep only the earliest valid `(start_date, event_date)` per `(case_id, drug_of_interest, event_term)`.
- **TTO:** `DATEDIFF(event_date, start_date) + 1`; exclude negative TTO.

> Implementation detail: In SQL-like pseudocode below, replace `JOIN` between DRUG and REAC with `FULL OUTER JOIN` if your engine supports it; otherwise emulate via `UNION` + grouping.
> Filter to Pemafibrate by adding `WHERE m.canonical = 'Pemafibrate'` after the fibrate-name mapping join.


```sql
-- Merge DRUG + REAC on case_id; filter to Pemafibrate and biliary PTs
CREATE VIEW jader_tto_candidates AS
SELECT
  r."識別番号" AS case_id,
  d."医薬品（一般名）" AS drug_name,
  r."有害事象" AS event_term,
  d."投与開始日" AS start_date,
  r."有害事象発現日" AS event_date
FROM table_DRUG d
JOIN table_REAC r ON d."識別番号" = r."識別番号"
JOIN fibrate_name_map m ON UPPER(TRIM(d."医薬品（一般名）")) = UPPER(TRIM(m.raw_name))
JOIN biliary_pt_list b ON UPPER(TRIM(r."有害事象")) = UPPER(TRIM(b.pt));

-- Keep the earliest valid (start_date, event_date) pair per case/drug/event
CREATE VIEW jader_tto_first AS
SELECT *
FROM (
  SELECT
    case_id, m.canonical AS drug_of_interest, event_term, start_date, event_date,
    ROW_NUMBER() OVER (PARTITION BY case_id, m.canonical, event_term ORDER BY start_date, event_date) AS rn
  FROM jader_tto_candidates c
  JOIN fibrate_name_map m ON UPPER(TRIM(c.drug_name)) = UPPER(TRIM(m.raw_name))
) x
WHERE rn = 1;

-- TTO = DATEDIFF(event_date, start_date) + 1; exclude negatives
CREATE VIEW jader_tto AS
SELECT
  case_id, drug_of_interest, event_term,
  CAST(DATEDIFF(day, start_date, event_date) AS INT) + 1 AS TTO
FROM jader_tto_first
WHERE event_date >= start_date
  AND DATEDIFF(day, start_date, event_date) >= 0;
```

## FAERS

```sql
CREATE VIEW faers_tto_candidates AS
SELECT
  r.primaryid AS case_id,
  d.prod_ai    AS drug_name,
  r.pt         AS event_term,
  d.start_dt   AS start_date,
  r.event_dt   AS event_date
FROM table_DRUG d
JOIN table_REAC r ON d.primaryid = r.primaryid
JOIN fibrate_name_map m ON UPPER(TRIM(d.prod_ai)) = UPPER(TRIM(m.raw_name))
JOIN biliary_pt_list b ON UPPER(TRIM(r.pt)) = UPPER(TRIM(b.pt));

-- Earliest pair per case/drug/event
CREATE VIEW faers_tto_first AS
SELECT *
FROM (
  SELECT
    case_id, m.canonical AS drug_of_interest, event_term, start_date, event_date,
    ROW_NUMBER() OVER (PARTITION BY case_id, m.canonical, event_term ORDER BY start_date, event_date) AS rn
  FROM faers_tto_candidates c
  JOIN fibrate_name_map m ON UPPER(TRIM(c.drug_name)) = UPPER(TRIM(m.raw_name))
) x
WHERE rn = 1;

CREATE VIEW faers_tto AS
SELECT
  case_id, drug_of_interest, event_term,
  CAST(DATEDIFF(day, start_date, event_date) AS INT) + 1 AS TTO
FROM faers_tto_first
WHERE event_date >= start_date
  AND DATEDIFF(day, start_date, event_date) >= 0;
```
