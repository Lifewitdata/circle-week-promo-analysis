-- BigQuery session-local TEMP table (Teradata VOLATILE is a different dialect).
CREATE TEMP TABLE electronics_weekly AS
SELECT store_id,test_group,period,week_start_date,revenue
FROM `{{dataset}}.sales_weekly`
WHERE category_id='CAT04'
 AND week_start_date BETWEEN DATE '2026-01-05' AND DATE '2026-06-29';
SELECT test_group,period,AVG(revenue) AS revenue
FROM electronics_weekly GROUP BY test_group,period;
