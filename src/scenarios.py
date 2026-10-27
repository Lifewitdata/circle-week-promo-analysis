"""Illustrative decisions; assumptions are not observed costs or forecasts."""
import pandas as pd


def scenarios(summary, config):
    for key in ['rollout_stores','scenario_weeks']:
        if config[key] <= 0 or int(config[key]) != config[key]:
            raise ValueError(f'{key} must be a positive integer')
    if not 0 <= config['gross_margin_rate'] <= 1 or not 0 <= config['additional_promo_cost_rate'] <= 1 or config['fixed_cost_per_store'] < 0:
        raise ValueError('Invalid cost assumptions')
    baseline = summary['test_pre_weekly_revenue']+summary['control_weekly_change']
    rows=[]
    for label, effect in [('Lower effect',summary['effect_ci_low']),('Point estimate',summary['effect_usd_per_store_week']),('Upper effect',summary['effect_ci_high'])]:
        exposure=config['rollout_stores']*config['scenario_weeks']
        incremental=effect*exposure
        total=(baseline+effect)*exposure
        contribution=incremental*config['gross_margin_rate']-total*config['additional_promo_cost_rate']-config['rollout_stores']*config['fixed_cost_per_store']
        rows.append({'scenario':label,'stores':config['rollout_stores'],'weeks':config['scenario_weeks'],
                     'incremental_revenue_usd':incremental,'assumed_gross_margin_rate':config['gross_margin_rate'],
                     'assumed_additional_promo_cost_rate':config['additional_promo_cost_rate'],
                     'assumed_fixed_cost_per_store':config['fixed_cost_per_store'],
                     'incremental_contribution_usd':contribution,
                     'break_even_margin_rate':(total*config['additional_promo_cost_rate']+config['rollout_stores']*config['fixed_cost_per_store'])/incremental if incremental>0 else None,
                     'interpretation':'Sensitivity scenario, not a rollout prediction'})
    return pd.DataFrame(rows)
