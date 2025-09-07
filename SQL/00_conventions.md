# 00_conventions.md — Shared conventions and column aliases

This document defines common aliases so that the same pseudocode can operate on **JADER** and **FAERS** by switching a `:dataset` parameter.

## Dataset-specific column mapping

| Semantic | JADER column | FAERS column |
|---|---|---|
| case identifier | 識別番号 | primaryid |
| drug (ingredient) | 医薬品（一般名） | prod_ai |
| drug sequence per case | 医薬品連番 | drug_seq |
| adverse event term | 有害事象 | pt |
| drug start date | 投与開始日 | start_dt |
| event date | 有害事象発現日 | event_dt |
| number of drugs in case | 服薬数 | number_of_drug |

> We will alias these as: `primaryid`, `drug_of_interest`, `drug_seq`, `event_term`, `start_date`, `event_date`, `num_drugs`.

## Biliary ADE definition

- Use the HLT *“Cholecystitis and cholelithiasis”* and the **14 PTs** listed in Supplementary Table S1. Maintain the list as a table/view:
```sql
-- Logical placeholder: replace with actual 14 PTs from Supplementary Table S1
CREATE VIEW biliary_pt_list AS
SELECT 'PT_NAME_1' AS pt UNION ALL
SELECT 'PT_NAME_2' UNION ALL
...
SELECT 'PT_NAME_14';
```
(For FAERS, match on `pt`; for JADER, match on `有害事象`.)

## Fibrates of interest

Normalize the ingredient names to three canonical strings:
- Pemafibrate, Fenofibrate, Bezafibrate

Create a mapping table to coalesce spelling/locale variants:
```sql
CREATE TABLE fibrate_name_map(
  raw_name TEXT PRIMARY KEY,
  canonical TEXT CHECK (canonical IN ('Pemafibrate','Fenofibrate','Bezafibrate'))
);
```

## Subgroups (for stratified analysis)

- sex: raw sex values
- age bands: 20–50s vs 60s+ (exact cut rules as per study)
- BMI bands: < 25 vs ≥ 25

Nulls or non-numeric values should be **excluded** from subgroup denominators.
