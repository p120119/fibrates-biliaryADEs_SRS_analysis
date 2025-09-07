# -*- coding: utf-8 -*-
"""
node_001_demo_bmi.py
MSIP node_001: JADER DEMO numeric conversion and BMI calculation.

- Input:
    table: MSIP Table object (JADER DEMO-like) with columns ['体重', '身長', '年齢']
- Output:
    result: MSIP DataFrame object with added columns:
        - WEIGHT, HEIGHT, AGE (numeric; +5 adjustment for weight/height)
        - BMI (kg/m^2), rounded to 2 decimals
        - *_str and *数値 helper columns

Note:
- This script keeps the original Japanese column names for compatibility.
- Downstream nodes should alias column names to ASCII if needed.
"""

from msi.common.dataframe import DataFrame, cbind, rbind, merge, select, is_valid, format_str
from msi.common.dataframe.params import Axis, Merge, DType, Agg
from msi.common.dataframe.special_values import Na, Error, NegativeInf, PositiveInf

from msi.common.dataframe import DataFrame
import pandas as pd

# Convert the MSIP Table to a pandas DataFrame
df = table.to_pandas()

# Safe string conversion (handles NaN/Categorical)
for col in ['体重', '身長', '年齢']:
    df[f'{col}_str'] = df[col].apply(lambda x: str(x) if pd.notnull(x) else '')

# Numeric extraction helper ('未満' -> 0; otherwise extract digits)
def extract_numeric_or_zero(val):
    if pd.isna(val):
        return None
    val = str(val).strip()
    if val == '':
        return None
    if "未満" in val:
        return 0
    match = pd.Series([val]).str.extract(r'(\d+)')
    return int(match[0][0]) if pd.notnull(match[0][0]) else None

# Extract numeric values
df['体重数値'] = df['体重_str'].apply(extract_numeric_or_zero)
df['身長数値'] = df['身長_str'].apply(extract_numeric_or_zero)
df['年齢数値'] = df['年齢_str'].apply(extract_numeric_or_zero)

# Apply +5 adjustment to weight/height only (no adjustment to age)
df['WEIGHT'] = pd.to_numeric(df['体重数値'], errors='coerce') + 5
df['HEIGHT'] = pd.to_numeric(df['身長数値'], errors='coerce') + 5
df['AGE'] = pd.to_numeric(df['年齢数値'], errors='coerce')

# BMI calculation function
def calculate_bmi(weight, height_cm):
    if pd.isna(weight) or pd.isna(height_cm) or height_cm == 0:
        return None
    height_m = height_cm / 100  # cm → m
    return round(weight / (height_m ** 2), 2)

# Add BMI column
df['BMI'] = df.apply(lambda row: calculate_bmi(row['WEIGHT'], row['HEIGHT']), axis=1)

# Convert to an MSIP DataFrame
df_converted = df.astype(object)
result = DataFrame(df_converted.to_dict(orient="list"))
