-- Canonical queries: {{dataset}} becomes project.dataset in BigQuery.
-- The local runner removes the prefix and supplies SAFE_DIVIDE as a macro.
-- name: quality
SELECT COUNT(*) AS total_rows, COUNT(DISTINCT store_id) AS stores,
 COUNT(DISTINCT category_id) AS categories,
 SUM(CASE WHEN revenue IS NULL OR revenue < 0 THEN 1 ELSE 0 END) AS invalid_revenue
FROM `{{dataset}}.sales_weekly`
WHERE week_start_date BETWEEN DATE '2026-01-05' AND DATE '2026-06-29';

-- name: group_totals
SELECT s.test_group, sw.period, SUM(sw.revenue) AS revenue,
 AVG(sw.revenue) AS weekly_store_revenue, COUNT(DISTINCT sw.store_id) AS stores
FROM `{{dataset}}.sales_weekly` sw
JOIN `{{dataset}}.stores` s ON sw.store_id=s.store_id
WHERE sw.category_name='Electronics'
 AND sw.week_start_date BETWEEN DATE '2026-01-05' AND DATE '2026-06-29'
GROUP BY s.test_group, sw.period;

-- name: primary_effect
WITH per_store AS (
 SELECT store_id, test_group,
 AVG(CASE WHEN period='Pre' THEN revenue END) AS pre_weekly,
 AVG(CASE WHEN period='Post' THEN revenue END) AS post_weekly
 FROM `{{dataset}}.sales_weekly`
 WHERE category_name='Electronics'
 AND week_start_date BETWEEN DATE '2026-01-05' AND DATE '2026-06-29'
 GROUP BY store_id, test_group
), changes AS (
 SELECT *, post_weekly-pre_weekly AS delta,
 SAFE_DIVIDE(post_weekly-pre_weekly,pre_weekly)*100 AS growth_pct FROM per_store
)
SELECT AVG(CASE WHEN test_group='Test' THEN delta END)
 - AVG(CASE WHEN test_group='Control' THEN delta END) AS effect_usd_per_store_week,
 AVG(CASE WHEN test_group='Test' THEN growth_pct END)
 - AVG(CASE WHEN test_group='Control' THEN growth_pct END) AS store_growth_gap_pp
FROM changes;

-- name: weekly_trend
SELECT week_start_date,test_group,period,AVG(revenue) AS revenue
FROM `{{dataset}}.sales_weekly`
WHERE category_name='Electronics'
 AND week_start_date BETWEEN DATE '2026-01-05' AND DATE '2026-06-29'
GROUP BY week_start_date,test_group,period ORDER BY week_start_date,test_group;

-- name: category_changes
SELECT category_name,test_group,period,AVG(revenue) AS weekly_store_revenue
FROM `{{dataset}}.sales_weekly`
WHERE week_start_date BETWEEN DATE '2026-01-05' AND DATE '2026-06-29'
GROUP BY category_name,test_group,period;

-- name: region_changes
SELECT s.region,s.test_group,sw.period,AVG(sw.revenue) AS weekly_store_revenue
FROM `{{dataset}}.sales_weekly` sw JOIN `{{dataset}}.stores` s ON sw.store_id=s.store_id
WHERE sw.category_name='Electronics'
 AND sw.week_start_date BETWEEN DATE '2026-01-05' AND DATE '2026-06-29'
GROUP BY s.region,s.test_group,sw.period;

-- name: format_changes
SELECT s.store_format,s.test_group,sw.period,AVG(sw.revenue) AS weekly_store_revenue
FROM `{{dataset}}.sales_weekly` sw JOIN `{{dataset}}.stores` s ON sw.store_id=s.store_id
WHERE sw.category_name='Electronics'
 AND sw.week_start_date BETWEEN DATE '2026-01-05' AND DATE '2026-06-29'
GROUP BY s.store_format,s.test_group,sw.period;

-- name: revenue_per_unit
SELECT test_group,period,SUM(revenue) AS revenue,SUM(units_sold) AS units_sold,
 SAFE_DIVIDE(SUM(revenue),SUM(units_sold)) AS revenue_per_unit
FROM `{{dataset}}.sales_weekly`
WHERE category_name='Electronics'
 AND week_start_date BETWEEN DATE '2026-01-05' AND DATE '2026-06-29'
GROUP BY test_group,period;

-- name: store_growth
WITH p AS (
 SELECT store_id,region,test_group,
 SUM(CASE WHEN period='Pre' THEN revenue ELSE 0 END) AS pre_revenue,
 SUM(CASE WHEN period='Post' THEN revenue ELSE 0 END) AS post_revenue
 FROM `{{dataset}}.sales_weekly`
 WHERE category_name='Electronics'
 AND week_start_date BETWEEN DATE '2026-01-05' AND DATE '2026-06-29'
 GROUP BY store_id,region,test_group
)
SELECT *,SAFE_DIVIDE(post_revenue-pre_revenue,pre_revenue)*100 AS growth_pct
FROM p ORDER BY growth_pct DESC;

-- name: revenue_index
WITH weekly AS (
 SELECT week_start_date,test_group,AVG(revenue) AS revenue
 FROM `{{dataset}}.sales_weekly`
 WHERE category_name='Electronics'
 AND week_start_date BETWEEN DATE '2026-01-05' AND DATE '2026-06-29'
 GROUP BY week_start_date,test_group
), first_week AS (
 SELECT test_group,revenue AS baseline FROM weekly
 QUALIFY ROW_NUMBER() OVER (PARTITION BY test_group ORDER BY week_start_date)=1
)
SELECT w.week_start_date,w.test_group,SAFE_DIVIDE(w.revenue,b.baseline)*100 AS revenue_index
FROM weekly w JOIN first_week b ON w.test_group=b.test_group
ORDER BY w.week_start_date,w.test_group;
