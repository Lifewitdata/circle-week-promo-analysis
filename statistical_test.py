"""
Statistical Analysis: Is the Circle Week Electronics lift real, or noise?
---------------------------------------------------------------------------
Unit of randomization = STORE, so the store (not the week) is the correct
unit of analysis for significance testing. We:

  1. Collapse weekly data to one Pre-revenue and one Post-revenue number
     per store (Electronics only).
  2. Two-sample independent t-test comparing % change in Test vs Control
     stores -> is the average lift significantly different from zero?
  3. Regression-based Difference-in-Differences (DiD) model -> same
     question, but gives a clean coefficient + p-value + 95% CI, and is
     the standard framework analysts / stakeholders expect.
  4. Effect size (Cohen's d) -> is the difference not just significant,
     but *meaningfully large*?
  5. Region-level cuts, flagged with a small-sample-size caveat.
"""
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.formula.api as smf

sales = pd.read_csv("sales_weekly.csv")
stores = pd.read_csv("stores.csv")

elec = sales[sales["category_name"] == "Electronics"].copy()

# ---------------------------------------------------------------------
# 1. Store-level Pre / Post revenue
# ---------------------------------------------------------------------
store_level = (
    elec.groupby(["store_id", "test_group", "region", "period"])["revenue"]
    .sum()
    .unstack("period")
    .reset_index()
)
store_level["pct_change"] = (store_level["Post"] - store_level["Pre"]) / store_level["Pre"] * 100

test_pct = store_level.loc[store_level.test_group == "Test", "pct_change"]
ctrl_pct = store_level.loc[store_level.test_group == "Control", "pct_change"]

print("="*75)
print("1. STORE-LEVEL SUMMARY")
print("="*75)
print(store_level.groupby("test_group")["pct_change"].describe().round(2).to_string())

# ---------------------------------------------------------------------
# 2. Two-sample t-test on % change (store-level)
# ---------------------------------------------------------------------
t_stat, p_value = stats.ttest_ind(test_pct, ctrl_pct, equal_var=False)  # Welch's t-test

print("\n" + "="*75)
print("2. TWO-SAMPLE T-TEST (Welch) — Test vs Control % change")
print("="*75)
print(f"Test group mean % change:    {test_pct.mean():.2f}%  (n={len(test_pct)})")
print(f"Control group mean % change: {ctrl_pct.mean():.2f}%  (n={len(ctrl_pct)})")
print(f"Observed lift (diff):        {test_pct.mean() - ctrl_pct.mean():.2f} pts")
print(f"t-statistic:                 {t_stat:.3f}")
print(f"p-value:                     {p_value:.6f}")
print(f"Statistically significant at 95% confidence: {'YES' if p_value < 0.05 else 'NO'}")

# ---------------------------------------------------------------------
# 3. Effect size — Cohen's d
# ---------------------------------------------------------------------
pooled_std = np.sqrt(((len(test_pct)-1)*test_pct.std()**2 + (len(ctrl_pct)-1)*ctrl_pct.std()**2)
                      / (len(test_pct) + len(ctrl_pct) - 2))
cohens_d = (test_pct.mean() - ctrl_pct.mean()) / pooled_std

def interpret_d(d):
    d = abs(d)
    if d < 0.2: return "negligible"
    if d < 0.5: return "small"
    if d < 0.8: return "medium"
    return "large"

print("\n" + "="*75)
print("3. EFFECT SIZE — Cohen's d")
print("="*75)
print(f"Cohen's d: {cohens_d:.3f}  ({interpret_d(cohens_d)} effect)")

# ---------------------------------------------------------------------
# 4. Regression-based DiD model (the stakeholder-ready version)
# ---------------------------------------------------------------------
did_data = elec.copy()
did_data["is_test"] = (did_data["test_group"] == "Test").astype(int)
did_data["is_post"] = (did_data["period"] == "Post").astype(int)

model = smf.ols("revenue ~ is_test * is_post", data=did_data).fit(
    cov_type="cluster", cov_kwds={"groups": did_data["store_id"]}
)

print("\n" + "="*75)
print("4. DIFFERENCE-IN-DIFFERENCES REGRESSION (store-clustered SE)")
print("="*75)
print(model.summary().tables[1])

did_coef = model.params["is_test:is_post"]
did_pval = model.pvalues["is_test:is_post"]
ci_low, ci_high = model.conf_int().loc["is_test:is_post"]
baseline = model.params["Intercept"]

print(f"\nDiD coefficient (incremental $ revenue/store/week): ${did_coef:,.0f}")
print(f"As % of baseline weekly revenue (${baseline:,.0f}):    {did_coef/baseline*100:.2f}%")
print(f"95% CI: [${ci_low:,.0f}, ${ci_high:,.0f}]")
print(f"p-value: {did_pval:.6f}  -> {'SIGNIFICANT' if did_pval < 0.05 else 'NOT significant'} at 95% confidence")

# ---------------------------------------------------------------------
# 5. Placebo test (formal): run same DiD model on non-Electronics categories
# ---------------------------------------------------------------------
placebo_data = sales[sales["category_name"] != "Electronics"].copy()
placebo_data["is_test"] = (placebo_data["test_group"] == "Test").astype(int)
placebo_data["is_post"] = (placebo_data["period"] == "Post").astype(int)

placebo_model = smf.ols("revenue ~ is_test * is_post", data=placebo_data).fit(
    cov_type="cluster", cov_kwds={"groups": placebo_data["store_id"]}
)
placebo_coef = placebo_model.params["is_test:is_post"]
placebo_pval = placebo_model.pvalues["is_test:is_post"]

print("\n" + "="*75)
print("5. PLACEBO DiD (all other categories combined) — should be ~0 / not significant")
print("="*75)
print(f"Placebo DiD coefficient: ${placebo_coef:,.0f}  |  p-value: {placebo_pval:.4f}  -> "
      f"{'SIGNIFICANT (concerning!)' if placebo_pval < 0.05 else 'not significant (as expected)'}")

# ---------------------------------------------------------------------
# 6. Region-level significance (small-n caveat)
# ---------------------------------------------------------------------
print("\n" + "="*75)
print("6. REGION-LEVEL T-TESTS (caution: small sample per region, ~7-9 stores/group)")
print("="*75)
for region in sorted(store_level["region"].unique()):
    sub = store_level[store_level.region == region]
    t_r = sub.loc[sub.test_group == "Test", "pct_change"]
    c_r = sub.loc[sub.test_group == "Control", "pct_change"]
    if len(t_r) > 1 and len(c_r) > 1:
        t_s, p_r = stats.ttest_ind(t_r, c_r, equal_var=False)
        sig = "significant" if p_r < 0.05 else "not significant"
        print(f"{region:10s}: Test n={len(t_r)}, Control n={len(c_r)} | "
              f"lift={t_r.mean()-c_r.mean():.1f} pts | p={p_r:.4f} ({sig})")

print("\n\nAnalysis complete.")
