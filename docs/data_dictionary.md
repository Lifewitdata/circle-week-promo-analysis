# Data dictionary

| Table | Key / grain | Columns |
|---|---|---|
| sales_weekly | store_id + category_id + week_start_date | region and test_group (validated dimension copies), category_name, period (Pre/Post), revenue (synthetic USD, nonnegative), units_sold (nonnegative integer) |
| stores | store_id | region, store_format, sq_footage, test_group (Test/Control, fixed over time) |
| products | category_id | category_name, base_weekly_revenue (generator reference, not actual revenue) |
| promotions | promo_id | promo_name, category_targeted, promo_start_date, promo_end_date, design, expected_mechanism (scenario text, not verified redemption data) |

Dates: Monday week starts, 2026-01-05 through 2026-06-29. Promotion metadata runs
2026-04-06 through 2026-07-05; last weekly start is June 29. Each source key must
be unique, required fields populated, panel complete, assignment and category
labels consistent. Validation fails rather than silently dropping bad records.
No direct personal data, actual Target store identifiers or real customer records
are intentionally included; store IDs are simulated labels.

Warehouse design: dimensions can evolve in a real implementation using effective
dates/SCD2; this static panel has no dimension history. Do not claim implemented
SCD2. Weekly revenue is additive across stores/weeks/categories; percentages are
non-additive and must be recalculated from the intended denominators. Never
average percentages without deciding whether equal-store weighting is intended.
