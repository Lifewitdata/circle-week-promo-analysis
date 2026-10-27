# Metric definitions and analytical contract

All money is synthetic USD. Revenue is assumed net of discounts for scenario
accounting; the source does not document accounting recognition or discount treatment.

**Grain:** one store × category × Monday week. Stores and products are dimensions;
sales_weekly is a fact table. A store join is many-to-one. Names repeated on the
fact are validated against dimensions before analysis. No order or SKU grain exists.

**Primary effect:** average weekly test-store post revenue minus test-store pre
revenue, less the equivalent control-store change. Units: USD/store/week.
OLS `revenue ~ is_test * is_post` estimates the same effect for this complete,
balanced panel. Standard errors cluster at store level, with t-based intervals.
Do not aggregate multiple categories and call the result an Electronics effect.

**Incremental revenue:** primary effect × number of test stores × post weeks.
Its confidence bounds multiply the same exposure by primary-effect bounds.
This is an estimated counterfactual difference, not booked incremental sales.

**Average store growth gap:** mean of each test store's (post/pre−1)×100 minus
the control equivalent. Units: percentage points (pp), not percent lift.
**Aggregate growth gap:** ratio of group sums, differenced in pp. Different
weighting means it need not match the average-store result.
**Effect as percent of baseline:** primary dollar effect / test pre weekly average
×100. This is a third distinct measure. Never interchange the three.

**Revenue per unit:** sum(revenue)/sum(units_sold). Not average order value,
basket value or conversion rate; order and visitor counts are unavailable.
**Store growth:** (post revenue/pre revenue−1)×100. Store rankings include secular
growth and noise and are not store-specific causal treatment effects.

**Scenario contribution:** estimated incremental revenue × assumed gross margin
minus additional promotion cost rate × total treated revenue, minus fixed
per-store cost × stores. Total treated revenue assumes test pre weekly baseline
plus control weekly change plus treatment effect. Incremental revenue excludes
counterfactual revenue; additional promo costs apply to all treated sales.
Discounts already reflected in revenue must not be counted again as extra cost.
These are conditional assumptions, not measured profit, ROI or forecasts.

**Forecast benchmark:** pre-promo category revenue summed across stores. First
n−4 pre weeks train each baseline; last four pre weeks evaluate it. MAE is mean
absolute dollar error; WAPE is total absolute error / total actual revenue.
No post-promotion rows enter training, model selection or evaluation. Only one
small holdout is available; no annual seasonality or production-demand claim.
