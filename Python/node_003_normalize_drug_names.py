# -*- coding: utf-8 -*-
"""
node_003_normalize_drug_names_simple.py
Assumes both JADER and FAERS provide a column named 'drug_of_interest'.

Behavior:
- Convert MSIP table -> pandas
- Case-insensitive substring normalization using `yure_dict`
- Write back to MSIP DataFrame

Customize:
- Edit `yure_dict` to add your mappings.
"""

from msi.common.dataframe import DataFrame, cbind, rbind, merge, select, is_valid, format_str
from msi.common.dataframe.params import Axis, Merge, DType, Agg
from msi.common.dataframe.special_values import Na, Error, NegativeInf, PositiveInf

import pandas as pd
from msi.common.dataframe import pandas_to_dataframe

# MSIP -> pandas
df = table.to_pandas()

if 'drug_of_interest' not in df.columns:
    raise ValueError("Expected column 'drug_of_interest' not found. Please ensure upstream nodes create it.")

# ---- User-editable normalization dictionary (case-insensitive keys; substring match) ----
yure_dict = {
    # Example mapping(s):
    "FENO": "FENOFIBRATE",
    # "BEZA": "BEZAFIBRATE",
    # "PEMA": "PEMAFIBRATE",
}

def normalize_text(val: object) -> str:
    s = "" if pd.isna(val) else str(val)
    s_cmp = s.casefold()
    for key, canonical in yure_dict.items():
        if str(key).casefold() in s_cmp:
            return canonical
    return s

# Normalize
df['drug_of_interest'] = df['drug_of_interest'].astype(str).map(normalize_text)

# Back to MSIP DataFrame
result = pandas_to_dataframe(df)
