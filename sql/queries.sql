-- =====================================================================
-- Circle Week Promotion Effectiveness Analysis
-- BigQuery SQL — Test vs Control, Pre vs Post analysis
-- Dataset: `retail-analytics.promo_analysis`
-- Tables: sales_weekly, stores, products, promotions
-- =====================================================================


-- ---------------------------------------------------------------------
-- Q1. DATA QUALITY CHECK
-- Sanity-check row counts, date range, and nulls before trusting anything.
-- ---------------------------------------------------------------------
SELECT
  COUNT(*)                              AS total_rows,
  COUNT(DISTINCT store_id)              AS distinct_stores,
  COUNT(DISTINCT category_id)           AS distinct_categories,
  MIN(week_start_date)                  AS first_week,
  MAX(week_start_date)                  AS last_week,
  SUM(CASE WHEN revenue IS NULL THEN 1 ELSE 0 END)     AS null_revenue_rows,
  SUM(CASE WHEN revenue < 0 THEN 1 ELSE 0 END)         AS negative_revenue_rows
FROM `target-retail-analytics.promo_analysis.sales_weekly`;


-- ---------------------------------------------------------------------
-- Q2. OVERALL PRE VS POST REVENUE — ELECTRONICS ONLY, BY TEST GROUP
-- The core comparison: did Test stores grow more than Control after the promo?
-- ---------------------------------------------------------------------
SELECT
  s.test_group,
  sw.period,
  ROUND(SUM(sw.revenue), 0)             AS total_revenue,
  ROUND(AVG(sw.revenue), 0)             AS avg_weekly_store_revenue,
  COUNT(DISTINCT sw.store_id)           AS store_count
FROM `target-retail-analytics.promo_analysis.sales_weekly` sw
JOIN `target-retail-analytics.promo_analysis.stores` s
  ON sw.store_id = s.store_id
WHERE sw.category_name = 'Electronics'
GROUP BY 1, 2
ORDER BY 1, 2;


-- ---------------------------------------------------------------------
-- Q3. DIFFERENCE-IN-DIFFERENCES (DiD) LIFT CALCULATION
-- The headline metric: incremental % lift attributable to the promo,
-- after netting out the natural pre/post change seen in Control stores.
-- ---------------------------------------------------------------------
WITH grp AS (
  SELECT
    s.test_group,
    sw.period,
    SUM(sw.revenue) / COUNT(DISTINCT sw.store_id) AS rev_per_store
  FROM `target-retail-analytics.promo_analysis.sales_weekly` sw
  JOIN `target-retail-analytics.promo_analysis.stores` s
    ON sw.store_id = s.store_id
  WHERE sw.category_name = 'Electronics'
  GROUP BY 1, 2
),
pivoted AS (
  SELECT
    test_group,
    MAX(CASE WHEN period = 'Pre'  THEN rev_per_store END)  AS pre_rev,
    MAX(CASE WHEN period = 'Post' THEN rev_per_store END)  AS post_rev
  FROM grp
  GROUP BY test_group
)
SELECT
  test_group,
  ROUND(pre_rev, 0)                                   AS pre_revenue_per_store,
  ROUND(post_rev, 0)                                  AS post_revenue_per_store,
  ROUND(SAFE_DIVIDE(post_rev - pre_rev, pre_rev) * 100, 2) AS pct_change
FROM pivoted;

-- DiD lift = (Test % change) − (Control % change)
-- Run as a follow-up once the above CTE is materialized, or wrap in one query:
WITH grp AS (
  SELECT
    s.test_group, sw.period,
    SUM(sw.revenue) / COUNT(DISTINCT sw.store_id) AS rev_per_store
  FROM `target-retail-analytics.promo_analysis.sales_weekly` sw
  JOIN `target-retail-analytics.promo_analysis.stores` s ON sw.store_id = s.store_id
  WHERE sw.category_name = 'Electronics'
  GROUP BY 1, 2
),
pivoted AS (
  SELECT test_group,
    MAX(CASE WHEN period='Pre' THEN rev_per_store END)  AS pre_rev,
    MAX(CASE WHEN period='Post' THEN rev_per_store END) AS post_rev
  FROM grp GROUP BY test_group
),
pct AS (
  SELECT test_group, SAFE_DIVIDE(post_rev - pre_rev, pre_rev) AS pct_change
  FROM pivoted
)
SELECT
  ROUND((MAX(CASE WHEN test_group='Test' THEN pct_change END)
       - MAX(CASE WHEN test_group='Control' THEN pct_change END)) * 100, 2) AS did_lift_pct
FROM pct;


-- ---------------------------------------------------------------------
-- Q4. WEEKLY REVENUE TREND — ELECTRONICS, TEST VS CONTROL
-- Feeds the trend line chart in the dashboard; shows the two lines
-- tracking together pre-promo and diverging post-promo.
-- ---------------------------------------------------------------------
SELECT
  sw.week_start_date,
  sw.period,
  s.test_group,
  ROUND(SUM(sw.revenue) / COUNT(DISTINCT sw.store_id), 0) AS avg_revenue_per_store
FROM `target-retail-analytics.promo_analysis.sales_weekly` sw
JOIN `target-retail-analytics.promo_analysis.stores` s
  ON sw.store_id = s.store_id
WHERE sw.category_name = 'Electronics'
GROUP BY 1, 2, 3
ORDER BY 1, 3;


-- ---------------------------------------------------------------------
-- Q5. PLACEBO / FALSIFICATION CHECK — ALL OTHER CATEGORIES
-- If the promo only targeted Electronics, Test and Control stores should
-- show NO meaningful lift gap in other categories. Confirms the effect
-- isn't just "Test stores sell more of everything."
-- ---------------------------------------------------------------------
WITH grp AS (
  SELECT
    sw.category_name, s.test_group, sw.period,
    SUM(sw.revenue) / COUNT(DISTINCT sw.store_id) AS rev_per_store
  FROM `target-retail-analytics.promo_analysis.sales_weekly` sw
  JOIN `target-retail-analytics.promo_analysis.stores` s ON sw.store_id = s.store_id
  WHERE sw.category_name != 'Electronics'
  GROUP BY 1, 2, 3
),
pivoted AS (
  SELECT category_name, test_group,
    MAX(CASE WHEN period='Pre' THEN rev_per_store END)  AS pre_rev,
    MAX(CASE WHEN period='Post' THEN rev_per_store END) AS post_rev
  FROM grp GROUP BY 1, 2
)
SELECT
  category_name, test_group,
  ROUND(SAFE_DIVIDE(post_rev - pre_rev, pre_rev) * 100, 2) AS pct_change
FROM pivoted
ORDER BY category_name, test_group;


-- ---------------------------------------------------------------------
-- Q6. LIFT BY REGION
-- Did the promo work everywhere, or is the lift concentrated in a
-- specific region? Useful for a future rollout recommendation.
-- ---------------------------------------------------------------------
WITH grp AS (
  SELECT
    s.region, s.test_group, sw.period,
    SUM(sw.revenue) / COUNT(DISTINCT sw.store_id) AS rev_per_store
  FROM `target-retail-analytics.promo_analysis.sales_weekly` sw
  JOIN `target-retail-analytics.promo_analysis.stores` s ON sw.store_id = s.store_id
  WHERE sw.category_name = 'Electronics'
  GROUP BY 1, 2, 3
),
pivoted AS (
  SELECT region, test_group,
    MAX(CASE WHEN period='Pre' THEN rev_per_store END)  AS pre_rev,
    MAX(CASE WHEN period='Post' THEN rev_per_store END) AS post_rev
  FROM grp GROUP BY 1, 2
)
SELECT
  region, test_group,
  ROUND(pre_rev, 0)  AS pre_revenue,
  ROUND(post_rev, 0) AS post_revenue,
  ROUND(SAFE_DIVIDE(post_rev - pre_rev, pre_rev) * 100, 2) AS pct_change
FROM pivoted
ORDER BY region, test_group;


-- ---------------------------------------------------------------------
-- Q7. LIFT BY STORE FORMAT (Target / SuperTarget / Small Format)
-- Checks whether the promo performs differently by store format —
-- relevant for merchandising/space-planning decisions.
-- ---------------------------------------------------------------------
WITH grp AS (
  SELECT
    s.store_format, s.test_group, sw.period,
    SUM(sw.revenue) / COUNT(DISTINCT sw.store_id) AS rev_per_store
  FROM `target-retail-analytics.promo_analysis.sales_weekly` sw
  JOIN `target-retail-analytics.promo_analysis.stores` s ON sw.store_id = s.store_id
  WHERE sw.category_name = 'Electronics'
  GROUP BY 1, 2, 3
),
pivoted AS (
  SELECT store_format, test_group,
    MAX(CASE WHEN period='Pre' THEN rev_per_store END)  AS pre_rev,
    MAX(CASE WHEN period='Post' THEN rev_per_store END) AS post_rev
  FROM grp GROUP BY 1, 2
)
SELECT
  store_format, test_group,
  ROUND(SAFE_DIVIDE(post_rev - pre_rev, pre_rev) * 100, 2) AS pct_change
FROM pivoted
ORDER BY store_format, test_group;


-- ---------------------------------------------------------------------
-- Q8. AVERAGE ORDER / BASKET VALUE CHANGE (Revenue per Unit)
-- Distinguishes whether the lift came from more units sold (volume)
-- or higher price points per unit (mix/value).
-- ---------------------------------------------------------------------
SELECT
  s.test_group,
  sw.period,
  ROUND(SUM(sw.revenue), 0)                         AS total_revenue,
  SUM(sw.units_sold)                                AS total_units,
  ROUND(SAFE_DIVIDE(SUM(sw.revenue), SUM(sw.units_sold)), 2) AS revenue_per_unit
FROM `target-retail-analytics.promo_analysis.sales_weekly` sw
JOIN `target-retail-analytics.promo_analysis.stores` s
  ON sw.store_id = s.store_id
WHERE sw.category_name = 'Electronics'
GROUP BY 1, 2
ORDER BY 1, 2;


-- ---------------------------------------------------------------------
-- Q9. TOP / BOTTOM 5 STORES BY INDIVIDUAL LIFT
-- Store-level ranking — flags standout performers and laggards worth
-- a follow-up qualitative review (e.g. execution issues, local competition).
-- ---------------------------------------------------------------------
WITH store_pivot AS (
  SELECT
    sw.store_id, s.region, s.test_group,
    SUM(CASE WHEN sw.period = 'Pre'  THEN sw.revenue END)  AS pre_rev,
    SUM(CASE WHEN sw.period = 'Post' THEN sw.revenue END)  AS post_rev
  FROM `target-retail-analytics.promo_analysis.sales_weekly` sw
  JOIN `target-retail-analytics.promo_analysis.stores` s ON sw.store_id = s.store_id
  WHERE sw.category_name = 'Electronics' AND s.test_group = 'Test'
  GROUP BY 1, 2, 3
)
SELECT
  store_id, region,
  ROUND(pre_rev, 0)  AS pre_revenue,
  ROUND(post_rev, 0) AS post_revenue,
  ROUND(SAFE_DIVIDE(post_rev - pre_rev, pre_rev) * 100, 2) AS pct_change
FROM store_pivot
ORDER BY pct_change DESC
LIMIT 5;
-- Flip to `ORDER BY pct_change ASC LIMIT 5` for the bottom 5.


-- ---------------------------------------------------------------------
-- Q10. WEEKLY INDEXED REVENUE (Week 1 = 100)
-- Normalizes Test and Control onto the same starting index so they can
-- be plotted on one chart and visually compared regardless of base size.
-- ---------------------------------------------------------------------
WITH weekly AS (
  SELECT
    sw.week_start_date,
    s.test_group,
    SUM(sw.revenue) / COUNT(DISTINCT sw.store_id) AS avg_rev
  FROM `target-retail-analytics.promo_analysis.sales_weekly` sw
  JOIN `target-retail-analytics.promo_analysis.stores` s ON sw.store_id = s.store_id
  WHERE sw.category_name = 'Electronics'
  GROUP BY 1, 2
),
base AS (
  SELECT test_group, avg_rev AS base_rev
  FROM weekly
  QUALIFY ROW_NUMBER() OVER (PARTITION BY test_group ORDER BY week_start_date) = 1
)
SELECT
  w.week_start_date,
  w.test_group,
  ROUND(SAFE_DIVIDE(w.avg_rev, b.base_rev) * 100, 1) AS revenue_index
FROM weekly w
JOIN base b ON w.test_group = b.test_group
ORDER BY w.test_group, w.week_start_date;
