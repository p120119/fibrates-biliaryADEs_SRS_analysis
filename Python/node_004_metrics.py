# -*- coding: utf-8 -*-
"""
node_004_metrics.py
MSIP node_004: Build 2x2 counts and compute ROR/PRR/IC, Fisher's exact test p-value, and chi-square.

Inputs:
    - table:     totals table (expects n++ and n+1 as first row/cols as per your pipeline)
    - table1:    per-drug table with n11 and n1+ columns (first three columns used: [drug, n1+, n11])

Output:
    - result: MSIP DataFrame with columns:
        [drug, n11, n12, n21, n22, ROR, ROR025, ROR975, p-value,
         PRR, PRR025, PRR975, χ^2, IC, IC025, IC975]

Note:
- This script mirrors the logic you shared, including WHO-style IC (closed-form) and Fisher's exact p-values via SciPy.
- Be sure SciPy is available (see requirements.txt).
"""

from msi.common.dataframe import DataFrame, cbind, rbind, merge, select, is_valid, format_str
from msi.common.dataframe.params import Axis, Merge, DType, Agg
import scipy.stats as stats
from msi.common.dataframe.special_values import Na, Error, NegativeInf, PositiveInf

import pandas as pd
import numpy as np
from msi.common.dataframe import pandas_to_dataframe

# --- MSI DataFrame を pandas に変換 ---
table_pd = table.to_pandas()
table1_pd = table1.to_pandas()

# --- 必要な値を抽出 ---
n11 = table1_pd.iloc[:, 2]
nplusplus = table_pd.iat[0, 0]
n1plus = table1_pd.iloc[:, 1]
n2plus = nplusplus - n1plus
nplus1 = table_pd.iat[0, 1]
nplus2 = nplusplus - nplus1
n12 = n1plus - n11
n21 = nplus1 - n11
n22 = nplus2 - n12

# --- フィッシャー検定とp値の計算 ---
p_values = []
for i in range(len(table1_pd)):
    contingency_table = [[n11[i], n12[i]], [n21[i], n22[i]]]
    try:
        _, p_val = stats.fisher_exact(contingency_table)
        p_values.append(p_val)
    except Exception:
        p_values.append(np.nan)

# --- オッズ比とその95% CI ---
odds_ratio = (n11 * n22) / (n12 * n21)
CI_min = np.exp(np.log(odds_ratio) - 1.96 * np.sqrt(1/n11 + 1/n12 + 1/n21 + 1/n22))
CI_max = np.exp(np.log(odds_ratio) + 1.96 * np.sqrt(1/n11 + 1/n12 + 1/n21 + 1/n22))

# --- PRR とその95% CI ---
PRR = (n11 * n2plus) / (n1plus * n21)
with np.errstate(divide='ignore', invalid='ignore'):
    logPRR = np.log(PRR)
    se_logPRR = np.sqrt((1/n11) - (1/n1plus) + (1/n21) - (1/n2plus))
    PRR025 = np.exp(logPRR - 1.96 * se_logPRR)
    PRR975 = np.exp(logPRR + 1.96 * se_logPRR)

# NaNやinfの処理
PRR = np.nan_to_num(PRR, nan=0, posinf=np.inf, neginf=0)
PRR025 = np.nan_to_num(PRR025, nan=0, posinf=np.inf, neginf=0)
PRR975 = np.nan_to_num(PRR975, nan=0, posinf=np.inf, neginf=0)

# --- カイ二乗値 ---
n11EXP = (n1plus * nplus1) / nplusplus
n12EXP = (n1plus * nplus2) / nplusplus
n21EXP = (n2plus * nplus1) / nplusplus
n22EXP = (n2plus * nplus2) / nplusplus
kai2 = ((n11 - n11EXP)**2 / n11EXP) + ((n12 - n12EXP)**2 / n12EXP) + ((n21 - n21EXP)**2 / n21EXP) + ((n22 - n22EXP)**2 / n22EXP)

# --- IC（解析解：WHO方式に準拠）に差し替え ---
# 参考コードのパラメータ
α = β = 2
α1 = β1 = 1
γ11 = 1
ln2_sq = 1 / (np.log(2))**2

IC, IC025, IC975 = [], [], []
# nplus1, nplusplus はスカラー（全行共通）なので、ループ内ではそのまま利用
for i in range(len(n11)):
    a = n11[i]
    a1 = n1plus[i]
    a2 = nplus1
    N  = nplusplus

    # 期待値補正項 γ
    numerator = (N + α) * (N + β)
    denominator = (a1 + α1) * (a2 + β1)
    γ = γ11 * numerator / denominator

    # eIC 計算
    num_eic = (a + γ11) * (N + α) * (N + β)
    den_eic = (N + γ)   * (a1 + α1) * (a2 + β1)
    e_ic = np.log2(num_eic / den_eic)

    # 分散・信頼区間
    v1 = (N - a  + γ - γ11) / ((a  + γ11) * (N + γ))
    v2 = (N - a1 + α - α1)  / ((a1 + α1)  * (N + α))
    v3 = (N - a2 + β - β1)  / ((a2 + β1)  * (N + β))
    v_ic = ln2_sq * (v1 + v2 + v3)

    sd = np.sqrt(v_ic)
    IC.append(round(e_ic, 3))
    IC025.append(round(e_ic - 2 * sd, 3))
    IC975.append(round(e_ic + 2 * sd, 3))

# --- 値をリストに変換 ---
values_n11, values_n12, values_n21, values_n22 = [list(x) for x in [n11, n12, n21, n22]]
values_odds_ratio = list(odds_ratio)
values_CI_min = list(CI_min)
values_CI_max = list(CI_max)
values_PRR = list(PRR)
values_PRR025 = list(PRR025)
values_PRR975 = list(PRR975)
values_kai2 = list(kai2)
formatted_p_values = [f"{p:.4e}" if pd.notna(p) else np.nan for p in p_values]

# --- DataFrameに格納 ---
data_frames = {
    'result_df_n11': {'column_name': 'n11', 'values': values_n11},
    'result_df_n12': {'column_name': 'n12', 'values': values_n12},
    'result_df_n21': {'column_name': 'n21', 'values': values_n21},
    'result_df_n22': {'column_name': 'n22', 'values': values_n22},
    'result_df_odds_ratio': {'column_name': 'ROR', 'values': values_odds_ratio},
    'result_df_CI_min': {'column_name': 'ROR025', 'values': values_CI_min},
    'result_df_CI_max': {'column_name': 'ROR975', 'values': values_CI_max},
    'result_df_p_value': {'column_name': 'p-value', 'values': formatted_p_values},
    'result_df_PRR': {'column_name': 'PRR', 'values': values_PRR},
    'result_df_PRR025': {'column_name': 'PRR025', 'values': values_PRR025},
    'result_df_PRR975': {'column_name': 'PRR975', 'values': values_PRR975},
    'result_df_kai2': {'column_name': 'χ^2', 'values': values_kai2},
    'result_df_IC': {'column_name': 'IC', 'values': IC},
    'result_df_IC025': {'column_name': 'IC025', 'values': IC025},
    'result_df_IC975': {'column_name': 'IC975', 'values': IC975}
}

# --- 各DataFrameを作成 ---
for df_name, info in data_frames.items():
    globals()[df_name] = pd.DataFrame({info['column_name']: info['values']})

# --- 結合 ---
result_df = pd.concat([globals()[df_name] for df_name in data_frames.keys()], axis=1)

# --- 医薬品列と結合 ---
column = table1_pd.iloc[:, 0]
result_concat = pd.concat([column, result_df], axis=1)

# --- MSI DataFrameに変換して出力 ---
result_msi = pandas_to_dataframe(result_concat)
result = result_msi
