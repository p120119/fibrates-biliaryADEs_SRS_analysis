from msi.common.dataframe import pandas_to_dataframe
import numpy as np
import pandas as pd
from scipy.stats import gamma
from scipy.optimize import minimize

# --- Input data ---
df = table.to_pandas()

# --- Split into Overall row(s) and Subgroup rows ---
overall_df = df[df["Subgroup"] == "Overall"].copy()
sub_df = df[df["Subgroup"] != "Overall"].copy()

# --- Compute expected counts E0_s per subgroup ---
sub_df["n1+"] = sub_df["n11"] + sub_df["n12"]
sub_df["n+1"] = sub_df["n11"] + sub_df["n21"]
sub_df["n++"] = sub_df["n11"] + sub_df["n12"] + sub_df["n21"] + sub_df["n22"]
sub_df["E0_s"] = (sub_df["n1+"] * sub_df["n+1"]) / sub_df["n++"]

# --- Aggregate E0 and O per drug_of_interest ---
grouped_sub = sub_df.groupby("drug_of_interest").agg({
    "E0_s": "sum",
    "n11": "sum"
}).reset_index().rename(columns={"E0_s": "E0", "n11": "O"})

# --- Get background totals from Overall ---
overall_df["n1+"] = overall_df["n11"] + overall_df["n12"]
overall_df["n+1"] = overall_df["n11"] + overall_df["n21"]
overall_df["n++"] = overall_df["n11"] + overall_df["n12"] + overall_df["n21"] + overall_df["n22"]
overall_stats = overall_df[["drug_of_interest", "n1+", "n+1", "n++"]]

# --- Merge ---
result_df = pd.merge(grouped_sub, overall_stats, on="drug_of_interest", how="left")

# --- Extract O and E ---
O = result_df["O"].astype(float).values
E = result_df["E0"].astype(float).values

# --- Negative log-likelihood (mixture of Gammas) ---
def neg_log_likelihood_mgps(params, O, E):
    α1, β1, α2, β2, P = params
    if min(α1, β1, α2, β2) <= 0 or not (0 < P < 1):
        return np.inf
    logL = 0
    for o, e in zip(O, E):
        f1 = gamma.pdf(o, a=α1, scale=1 / (β1 * e))
        f2 = gamma.pdf(o, a=α2, scale=1 / (β2 * e))
        logL += np.log(P * f1 + (1 - P) * f2 + 1e-12)
    return -logL

# --- Initial parameter sets (5 variants) ---
init_sets = [
    [0.2, 0.1, 2, 4, 1/3],
    [0.1, 0.1, 10, 10, 0.2],
    [0.3, 0.5, 6, 6, 0.5],
    [0.5, 0.3, 12, 12, 0.8],
    [0.2, 0.2, 5, 5, 0.4]
]

# --- Run optimization and pick the best starting point ---
results = []
for init in init_sets:
    res = minimize(
        neg_log_likelihood_mgps, init, args=(O, E),
        bounds=[(1e-3, None)] * 4 + [(1e-3, 1 - 1e-3)],
        method='L-BFGS-B'
    )
    results.append(res)

best_result = min(results, key=lambda r: r.fun)
α1_hat, β1_hat, α2_hat, β2_hat, P_hat = best_result.x

# ===============================
# Deterministic random seed: 12345
# ===============================
BASE_SEED = 12345
rng = np.random.default_rng(BASE_SEED)

# --- EBGM calculation ---
EBGM, EB05, EB95 = [], [], []
n_samples = 10_000  # increase/decrease as needed

for o, e in zip(O, E):
    n1 = int(n_samples * P_hat)
    n2 = n_samples - n1

    # Use NumPy's deterministic RNG
    samples1 = rng.gamma(shape=o + α1_hat, scale=1 / (β1_hat + e), size=n1)
    samples2 = rng.gamma(shape=o + α2_hat, scale=1 / (β2_hat + e), size=n2)
    all_samples = np.concatenate([samples1, samples2], dtype=float)

    log_samples = np.log(all_samples + 1e-12)  # Add a tiny term for numerical stability before logging
    ebgm = np.exp(log_samples.mean())
    eb05 = np.exp(np.percentile(log_samples, 5))
    eb95 = np.exp(np.percentile(log_samples, 95))

    EBGM.append(round(float(ebgm), 3))
    EB05.append(round(float(eb05), 3))
    EB95.append(round(float(eb95), 3))

# --- Format results ---
result_df["EBGM"] = EBGM
result_df["EBGM05"] = EB05
result_df["EBGM95"] = EB95
result_df["MGPS_Signal"] = ["Yes" if eb >= 2.0 else "No" for eb in EB05]

# --- Return in MSI format ---
result = pandas_to_dataframe(result_df)
