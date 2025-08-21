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

# テーブルを pandas に変換
df = table.to_pandas()

# 安全な文字列変換（NaN/Categorical 対応）
for col in ['体重', '身長', '年齢']:
    df[f'{col}_str'] = df[col].apply(lambda x: str(x) if pd.notnull(x) else '')

# 数値抽出関数（"未満" → 0、それ以外は数字抽出）
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

# 数値抽出
df['体重数値'] = df['体重_str'].apply(extract_numeric_or_zero)
df['身長数値'] = df['身長_str'].apply(extract_numeric_or_zero)
df['年齢数値'] = df['年齢_str'].apply(extract_numeric_or_zero)

# +5補正（体重・身長のみ）、年齢は補正なし
df['WEIGHT'] = pd.to_numeric(df['体重数値'], errors='coerce') + 5
df['HEIGHT'] = pd.to_numeric(df['身長数値'], errors='coerce') + 5
df['AGE'] = pd.to_numeric(df['年齢数値'], errors='coerce')

# BMIを計算する関数
def calculate_bmi(weight, height_cm):
    if pd.isna(weight) or pd.isna(height_cm) or height_cm == 0:
        return None
    height_m = height_cm / 100  # cm → m
    return round(weight / (height_m ** 2), 2)

# BMI列の追加
df['BMI'] = df.apply(lambda row: calculate_bmi(row['WEIGHT'], row['HEIGHT']), axis=1)

# MSI DataFrame に変換
df_converted = df.astype(object)
result = DataFrame(df_converted.to_dict(orient="list"))
