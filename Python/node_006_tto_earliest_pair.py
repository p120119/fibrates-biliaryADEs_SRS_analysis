# -*- coding: utf-8 -*-
"""
node_006_tto_earliest_pair.py
MSIP node_006: Keep only the earliest valid (start_date, event_date) pair per group.

Assumptions:
- Input `table` has at least 5 columns.
- Column index 2 = start_date-like column
- Column index 4 = event_date-like column
- Grouping key = all columns except indices 2 and 4 (so "earliest" is defined within those groups).

Behavior:
- Cast the two date columns to datetime (invalid -> NaT).
- Keep rows where both dates are valid (non-NaT).
- Within each group, keep the row(s) where both dates are the minimum (earliest).
- Optionally enforce start <= event by uncommenting the indicated line.
- Drop full-duplicate rows.

Output:
- `result`: MSIP DataFrame with only earliest (start,event) pairs.
"""

from msi.common.dataframe import DataFrame, cbind, rbind, merge, select, is_valid, format_str
from msi.common.dataframe.params import Axis, Merge, DType, Agg
from msi.common.dataframe.special_values import Na, Error, NegativeInf, PositiveInf

import pandas as pd
from msi.common.dataframe import pandas_to_dataframe

# MSI DataFrame -> pandas
df = table.to_pandas()

# Target columns (0-based indices 2 and 4)
col2 = df.columns[2]
col4 = df.columns[4]

# Cast to datetime (invalid -> NaT)
df[col2] = pd.to_datetime(df[col2], errors='coerce')
df[col4] = pd.to_datetime(df[col4], errors='coerce')

# Keep rows where both dates are valid
df_valid = df[df[col2].notna() & df[col4].notna()].copy()

# Optional: enforce non-negative TTO (start <= event)
# df_valid = df_valid[df_valid[col2] <= df_valid[col4]]

# Grouping keys = all columns except the two date columns
group_keys = [c for i, c in enumerate(df_valid.columns) if i not in (2, 4)]

if len(group_keys) > 0:
    # Compute groupwise min of both dates
    gmin = df_valid.groupby(group_keys)[[col2, col4]].transform('min')
    # Keep rows that match both minima (earliest pair)
    df_earliest = df_valid[(df_valid[col2] == gmin[col2]) & (df_valid[col4] == gmin[col4])]
else:
    # No grouping columns: keep the single global earliest pair
    min_c2 = df_valid[col2].min()
    min_c4 = df_valid[col4].min()
    df_earliest = df_valid[(df_valid[col2] == min_c2) & (df_valid[col4] == min_c4)]

# Reset index and drop full duplicates
df_earliest = df_earliest.drop_duplicates().reset_index(drop=True)

# Back to MSIP DataFrame
result = pandas_to_dataframe(df_earliest)
