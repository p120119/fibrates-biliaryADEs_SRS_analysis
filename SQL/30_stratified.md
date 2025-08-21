# 30_stratified.md — Subgroup (sex, age band, BMI band) analysis

## Cleaning subgroup columns (JADER example)

```sql
CREATE VIEW jader_subgroup_base AS
SELECT
  p.case_id, p.bmi, p.age_num,
  CASE WHEN sex IN ('男性','Male','M') THEN 'Male'
       WHEN sex IN ('女性','Female','F') THEN 'Female'
       ELSE NULL END AS sex_norm
FROM jader_plid p;
```

> Exclude NULL/NA/ERROR values for subgroup variables.

## Define groupers

```sql
CREATE VIEW jader_subgroups AS
SELECT
  case_id,
  sex_norm AS sex_group,
  CASE WHEN age_num BETWEEN 20 AND 59 THEN '20-50s'
       WHEN age_num >= 60 THEN '60s+'
       ELSE NULL END AS age_group,
  CASE WHEN bmi < 25 THEN '<25'
       WHEN bmi >= 25 THEN '>=25'
       ELSE NULL END AS bmi_group
FROM jader_subgroup_base;
```

Create analogous `faers_subgroups` with FAERS-specific fields.

## 2x2 per subgroup

Repeat the extraction in **20_disproportionality.md** but join through the subgroup view and group by `(drug_of_interest, subgroup_name, subgroup_level)`.

Skeleton:

```sql
CREATE VIEW {ds}_twobytwo_subgroup AS
SELECT
  g.sex_group AS subgroup_level, 'sex' AS subgroup_name,
  t.drug_of_interest, SUM(...) AS n11, SUM(...) AS n12, SUM(...) AS n21, SUM(...) AS n22
FROM {ds}_twobytwo_inputs t
JOIN {ds}_subgroups g USING (case_id)
GROUP BY 1,2,3
UNION ALL
SELECT
  g.age_group, 'age', ...
UNION ALL
SELECT
  g.bmi_group, 'bmi', ...
;
```

Compute metrics with the same formulas per `(drug_of_interest, subgroup_name, subgroup_level)` and export to CSV as needed.
