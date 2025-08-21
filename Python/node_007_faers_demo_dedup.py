# -*- coding: utf-8 -*-
"""
node_007_faers_demo_dedup.py
MSIP node_007: FAERS DEMO deduplication — keep the record with the maximum `caseversion` per `caseid`.

Input:
    table: MSIP Table object (FAERS DEMO-like) with columns ['caseid', 'caseversion', ...]

Output:
    result: MSIP DataFrame filtered to one row per caseid, with the highest caseversion.
"""

from msi.common.dataframe import DataFrame, cbind, rbind, merge, select, is_valid, format_str
from msi.common.dataframe.params import Axis, Merge, DType, Agg
from msi.common.dataframe.special_values import Na, Error, NegativeInf, PositiveInf

import pandas as pd
from msi.common.dataframe import pandas_to_dataframe

# MSIP -> pandas
table_pd = table.to_pandas()

# Ensure caseversion is numeric (coerce if necessary)
if not pd.api.types.is_numeric_dtype(table_pd['caseversion']):
    table_pd['caseversion'] = pd.to_numeric(table_pd['caseversion'], errors='coerce')

# Drop rows with missing identifiers
table_pd = table_pd.dropna(subset=['caseid', 'caseversion'])

# For each caseid, pick the row index with the max caseversion
idx = table_pd.groupby('caseid')['caseversion'].idxmax()

# Slice to those rows and reset index
demo_df_cleaned = table_pd.loc[idx].reset_index(drop=True)

# Back to MSIP DataFrame
result = pandas_to_dataframe(demo_df_cleaned)
