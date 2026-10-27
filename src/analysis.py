"""Store-randomized experiment: additive DiD is the primary estimator."""
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests


def clustered_did(frame):
    d = frame.assign(is_test=(frame.test_group == 'Test').astype(int),
                     is_post=(frame.period == 'Post').astype(int))
    return smf.ols('revenue ~ is_test * is_post', data=d).fit(
        cov_type='cluster', cov_kwds={'groups': d.store_id}, use_t=True)


def analyze(sales, target, config):
    e = sales[sales.category_name == target].copy()
    store = e.groupby(['store_id', 'test_group', 'region', 'period']).agg(
        revenue=('revenue', 'sum'), weekly_revenue=('revenue', 'mean')).unstack('period')
    changes = store['revenue'].reset_index()
    changes['growth_pct'] = (changes.Post / changes.Pre - 1) * 100
    t = changes.loc[changes.test_group == 'Test', 'growth_pct'].to_numpy()
    c = changes.loc[changes.test_group == 'Control', 'growth_pct'].to_numpy()
    pooled_sd = np.sqrt(((len(t)-1)*t.var(ddof=1)+(len(c)-1)*c.var(ddof=1))/(len(t)+len(c)-2))
    model = clustered_did(e)
    effect = float(model.params['is_test:is_post'])
    ci = model.conf_int().loc['is_test:is_post'].to_numpy()
    n_test, n_control = len(t), len(c)
    n_weeks = int(e[e.period == 'Post'].week_start_date.nunique())
    baseline = float(e[(e.test_group == 'Test') & (e.period == 'Pre')].revenue.mean())
    # Resample whole stores, never individual weeks (randomization unit).
    wide = e.groupby(['store_id', 'test_group', 'period']).revenue.mean().unstack().reset_index()
    a = (wide[wide.test_group == 'Test'].Post-wide[wide.test_group == 'Test'].Pre).to_numpy()
    b = (wide[wide.test_group == 'Control'].Post-wide[wide.test_group == 'Control'].Pre).to_numpy()
    rng = np.random.default_rng(config['seed'])
    samples = rng.choice(a, (config['bootstrap_draws'], len(a)), replace=True).mean(axis=1)-rng.choice(b, (config['bootstrap_draws'], len(b)), replace=True).mean(axis=1)
    boot_ci = np.quantile(samples, [.025, .975])
    # Pre-period slope is a diagnostic, not proof of parallel counterfactuals.
    pre = e[e.period == 'Pre'].copy()
    pre['week_index'] = (pre.week_start_date-pre.week_start_date.min()).dt.days/7
    pre['is_test'] = (pre.test_group == 'Test').astype(int)
    trend = smf.ols('revenue ~ is_test * week_index', data=pre).fit(cov_type='cluster', cov_kwds={'groups': pre.store_id}, use_t=True)
    groups = e.groupby(['test_group', 'period']).revenue.sum().unstack()
    growth = (groups.Post/groups.Pre-1)*100
    summary = {
        'category': target, 'synthetic': True, 'n_rows': len(sales),
        'n_test': n_test, 'n_control': n_control, 'post_weeks': n_weeks,
        'effect_usd_per_store_week': effect,
        'effect_ci_low': float(ci[0]), 'effect_ci_high': float(ci[1]),
        'effect_p_value': float(model.pvalues['is_test:is_post']),
        'incremental_revenue_usd': effect*n_test*n_weeks,
        'incremental_revenue_ci_low': float(ci[0])*n_test*n_weeks,
        'incremental_revenue_ci_high': float(ci[1])*n_test*n_weeks,
        'effect_pct_of_test_pre_baseline': effect/baseline*100,
        'test_pre_weekly_revenue': baseline,
        'control_pre_weekly_revenue': float(e[(e.test_group == 'Control') & (e.period == 'Pre')].revenue.mean()),
        'control_weekly_change': float(model.params['is_post']),
        'store_growth_gap_pp': float(t.mean()-c.mean()),
        'aggregate_growth_gap_pp': float(growth.Test-growth.Control),
        'welch_p_value': float(stats.ttest_ind(t,c,equal_var=False).pvalue),
        'cohens_d_growth': float((t.mean()-c.mean())/pooled_sd),
        'bootstrap_effect_ci': boot_ci.tolist(),
        'pretrend_slope_gap_usd_per_week': float(trend.params['is_test:week_index']),
        'pretrend_p_value': float(trend.pvalues['is_test:week_index']),
        'assignment_note': 'Simulated test/control allocation; original randomization algorithm unavailable.'
    }
    placebo = []
    for name, frame in sales.groupby('category_name'):
        fit = clustered_did(frame)
        interval = fit.conf_int().loc['is_test:is_post']
        placebo.append({'category': name, 'effect_usd_per_store_week': float(fit.params['is_test:is_post']),
                        'ci_low': float(interval.iloc[0]), 'ci_high': float(interval.iloc[1]),
                        'p_value': float(fit.pvalues['is_test:is_post']), 'is_target': name == target})
    placebo = pd.DataFrame(placebo)
    mask = ~placebo.is_target
    placebo.loc[mask, 'holm_p_value'] = multipletests(placebo.loc[mask, 'p_value'], method='holm')[1]
    region = []
    for name, frame in e.groupby('region'):
        fit = clustered_did(frame)
        interval = fit.conf_int().loc['is_test:is_post']
        region.append({'region':name, 'effect_usd_per_store_week':float(fit.params['is_test:is_post']),
                       'ci_low':float(interval.iloc[0]),'ci_high':float(interval.iloc[1]),
                       'p_value':float(fit.pvalues['is_test:is_post']),
                       'n_stores':frame.store_id.nunique()})
    regions = pd.DataFrame(region)
    regions['holm_p_value'] = multipletests(regions.p_value, method='holm')[1]
    trend_data = e.groupby(['week_start_date','test_group','period'],as_index=False).agg(revenue=('revenue','mean'))
    unit = e.groupby(['test_group','period'],as_index=False).agg(revenue=('revenue','sum'), units_sold=('units_sold','sum'))
    unit['revenue_per_unit'] = unit.revenue/unit.units_sold
    return summary, changes, placebo, regions, trend_data, unit
