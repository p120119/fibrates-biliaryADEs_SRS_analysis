# -*- coding: utf-8 -*-
"""
node_002_drug_counts_unified.py
MSIP node_002 (Unified): Count number of drugs per case for JADER *or* FAERS by auto-detecting columns.

- JADER columns:   識別番号 (ID), 医薬品連番 (sequence) -> output 服薬数
- FAERS columns:   primaryid (ID), drug_seq (sequence) -> output number_of_drug

Common aliases added for downstream unification:
- case_id    : ID column (both datasets)
- num_drugs  : count of distinct sequences per case

Behavior:
- Drop rows with NULL ID
- Count sequences per ID
- Merge count back
- Preserve dataset-specific count column for backward compatibility

If you prefer to override auto-detection, set DATASET_OVERRIDE to 'jader' or 'faers'.
"""

from msi.common.dataframe import DataFrame, cbind, rbind, merge, select, is_valid, format_str
from msi.common.dataframe.params import Axis, Merge, DType, Agg
from msi.common.dataframe.special_values import Na, Error, NegativeInf, PositiveInf

import pandas as pd
from msi.common.dataframe import pandas_to_dataframe

# Optional override: 'jader' | 'faers' | None
DATASET_OVERRIDE = None

# MSIP -> pandas
df = table.to_pandas()

cols = set(df.columns.astype(str))

# Auto-detect dataset based on column presence
dataset = None
if DATASET_OVERRIDE in ('jader', 'faers'):
    dataset = DATASET_OVERRIDE
elif {'識別番号', '医薬品連番'}.issubset(cols):
    dataset = 'jader'
elif {'primaryid', 'drug_seq'}.issubset(cols):
    dataset = 'faers'
else:
    raise ValueError("Unable to detect dataset: expected JADER ['識別番号','医薬品連番'] or FAERS ['primaryid','drug_seq'].")

# Map columns
if dataset == 'jader':
    id_col = '識別番号'
    seq_col = '医薬品連番'
    out_specific = '服薬数'
elif dataset == 'faers':
    id_col = 'primaryid'
    seq_col = 'drug_seq'
    out_specific = 'number_of_drug'

# Keep non-null IDs
df = df[df[id_col].notna()].copy()

# Count sequences per ID
counts = df.groupby(id_col)[seq_col].count().reset_index(name='num_drugs')

# Merge back
df = df.merge(counts, on=id_col, how='left')

# Add specific output column for compatibility
df[out_specific] = df['num_drugs']

# Add common alias for downstream joins/unions
df['case_id'] = df[id_col]

# Back to MSIP DataFrame
result = pandas_to_dataframe(df)
