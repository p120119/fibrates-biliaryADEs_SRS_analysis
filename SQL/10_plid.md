# 10_plid.md — Patient-level integrated dataset (PLID)

Build a per-case table with demographics, history, drug counts, and outcomes.

## JADER PLID

```sql
-- node_001: DEMO numeric conversions and BMI
CREATE VIEW jader_demo_bmi AS
SELECT
  d."識別番号"           AS case_id,
  CAST(d."年齢" AS NUMERIC)   AS age_num,
  CAST(d."体重" AS NUMERIC)   AS weight_kg,
  CAST(d."身長" AS NUMERIC)   AS height_cm,
  CASE WHEN CAST(d."身長" AS NUMERIC) > 0
       THEN (CAST(d."体重" AS NUMERIC) / POWER(CAST(d."身長" AS NUMERIC)/100.0, 2))
       ELSE NULL END AS bmi
FROM table_DEMO d;

-- Merge DEMO + HIST on 識別番号 (left join)
CREATE VIEW jader_demo_hist AS
SELECT a.*, h.* EXCEPT("識別番号")
FROM jader_demo_bmi a
LEFT JOIN table_HIST h ON a.case_id = h."識別番号";

-- node_002: DRUG -> count per case_id (服薬数)
CREATE VIEW jader_drug_counts AS
SELECT
  "識別番号" AS case_id,
  COUNT(DISTINCT "医薬品連番") AS num_drugs
FROM table_DRUG
GROUP BY "識別番号";

-- Merge to make PLID
CREATE VIEW jader_plid AS
SELECT a.*, c.num_drugs
FROM jader_demo_hist a
LEFT JOIN jader_drug_counts c USING (case_id);
```

## FAERS PLID

```sql
-- Deduplicate DEMO: keep the record with max(caseversion) per caseid, carry primaryid
CREATE VIEW faers_demo_dedup AS
SELECT d.*
FROM (
  SELECT caseid, MAX(caseversion) AS max_ver
  FROM table_DEMO
  GROUP BY caseid
) x
JOIN table_DEMO d
  ON d.caseid = x.caseid AND d.caseversion = x.max_ver;

-- Base DEMO columns of interest
CREATE VIEW faers_demo_base AS
SELECT
  d.primaryid      AS case_id,
  d.age, d.age_cod,
  d.sex,
  d.wt, d.wt_cod,
  d.occr_country
FROM faers_demo_dedup d;

-- OUTC join (left)
CREATE VIEW faers_demo_outc AS
SELECT a.*, o.outc_cod
FROM faers_demo_base a
LEFT JOIN table_OUTC o ON a.case_id = o.primaryid;

-- number_of_drug per case_id
CREATE VIEW faers_drug_counts AS
SELECT primaryid AS case_id,
       COUNT(DISTINCT drug_seq) AS num_drugs
FROM table_DRUG
GROUP BY primaryid;

-- INDI join by (primaryid, drug_seq)
CREATE VIEW faers_demo_indi AS
SELECT a.*, i.indi_pt, i.indi_drug_seq
FROM faers_demo_outc a
LEFT JOIN table_INDI i
  ON a.case_id = i.primaryid
 AND i.indi_drug_seq = (
    -- preferable: align with role_cod/therapy; here use a direct join placeholder
    i.indi_drug_seq
 );

-- PLID
CREATE VIEW faers_plid AS
SELECT a.*, c.num_drugs
FROM faers_demo_indi a
LEFT JOIN faers_drug_counts c USING (case_id);
```
