"""
Runs the same query logic as queries.sql against the local CSVs using DuckDB,
so we can prove the SQL is correct and see real numbers before this ever
touches BigQuery. DuckDB's SQL dialect is close enough to BigQuery
(swap `` `project.dataset.table` `` for plain table names, SAFE_DIVIDE
implemented as a macro) that the logic transfers directly.
"""
import duckdb

con = duckdb.connect()
con.execute("CREATE MACRO SAFE_DIVIDE(a, b) AS (CASE WHEN b = 0 OR b IS NULL THEN NULL ELSE a * 1.0 / b END)")

con.execute("""
    CREATE TABLE sales_weekly AS SELECT * FROM read_csv_auto('/home/claude/target_promo_project/data/sales_weekly.csv')
""")
con.execute("""
    CREATE TABLE stores AS SELECT * FROM read_csv_auto('/home/claude/target_promo_project/data/stores.csv')
""")

def run(title, sql):
    print(f"\n{'='*75}\n{title}\n{'='*75}")
    print(con.execute(sql).df().to_string(index=False))

# Q1
run("Q1. Data Quality Check", """
SELECT
  COUNT(*) AS total_rows,
  COUNT(DISTINCT store_id) AS distinct_stores,
  COUNT(DISTINCT category_id) AS distinct_categories,
  MIN(week_start_date) AS first_week,
  MAX(week_start_date) AS last_week,
  SUM(CASE WHEN revenue IS NULL THEN 1 ELSE 0 END) AS null_revenue_rows
FROM sales_weekly
""")

# Q2
run("Q2. Pre vs Post Revenue - Electronics, by Test Group", """
SELECT s.test_group, sw.period,
  ROUND(SUM(sw.revenue),0) AS total_revenue,
  ROUND(AVG(sw.revenue),0) AS avg_weekly_store_revenue,
  COUNT(DISTINCT sw.store_id) AS store_count
FROM sales_weekly sw JOIN stores s ON sw.store_id = s.store_id
WHERE sw.category_name = 'Electronics'
GROUP BY 1,2 ORDER BY 1,2
""")

# Q3 - DiD lift
run("Q3. Difference-in-Differences Lift", """
WITH grp AS (
  SELECT s.test_group, sw.period,
    SUM(sw.revenue)/COUNT(DISTINCT sw.store_id) AS rev_per_store
  FROM sales_weekly sw JOIN stores s ON sw.store_id = s.store_id
  WHERE sw.category_name = 'Electronics'
  GROUP BY 1,2
),
pivoted AS (
  SELECT test_group,
    MAX(CASE WHEN period='Pre' THEN rev_per_store END) AS pre_rev,
    MAX(CASE WHEN period='Post' THEN rev_per_store END) AS post_rev
  FROM grp GROUP BY test_group
),
pct AS (
  SELECT test_group, SAFE_DIVIDE(post_rev-pre_rev, pre_rev) AS pct_change
  FROM pivoted
)
SELECT
  ROUND(MAX(CASE WHEN test_group='Test' THEN pct_change END)*100,2) AS test_pct_change,
  ROUND(MAX(CASE WHEN test_group='Control' THEN pct_change END)*100,2) AS control_pct_change,
  ROUND((MAX(CASE WHEN test_group='Test' THEN pct_change END)
       - MAX(CASE WHEN test_group='Control' THEN pct_change END))*100,2) AS did_lift_pct
FROM pct
""")

# Q5 - placebo check
run("Q5. Placebo Check - Non-Electronics Categories", """
WITH grp AS (
  SELECT sw.category_name, s.test_group, sw.period,
    SUM(sw.revenue)/COUNT(DISTINCT sw.store_id) AS rev_per_store
  FROM sales_weekly sw JOIN stores s ON sw.store_id = s.store_id
  WHERE sw.category_name != 'Electronics'
  GROUP BY 1,2,3
),
pivoted AS (
  SELECT category_name, test_group,
    MAX(CASE WHEN period='Pre' THEN rev_per_store END) AS pre_rev,
    MAX(CASE WHEN period='Post' THEN rev_per_store END) AS post_rev
  FROM grp GROUP BY 1,2
)
SELECT category_name, test_group,
  ROUND(SAFE_DIVIDE(post_rev-pre_rev, pre_rev)*100,2) AS pct_change
FROM pivoted ORDER BY category_name, test_group
""")

# Q6 - region
run("Q6. Lift by Region", """
WITH grp AS (
  SELECT s.region, s.test_group, sw.period,
    SUM(sw.revenue)/COUNT(DISTINCT sw.store_id) AS rev_per_store
  FROM sales_weekly sw JOIN stores s ON sw.store_id = s.store_id
  WHERE sw.category_name = 'Electronics'
  GROUP BY 1,2,3
),
pivoted AS (
  SELECT region, test_group,
    MAX(CASE WHEN period='Pre' THEN rev_per_store END) AS pre_rev,
    MAX(CASE WHEN period='Post' THEN rev_per_store END) AS post_rev
  FROM grp GROUP BY 1,2
)
SELECT region, test_group,
  ROUND(SAFE_DIVIDE(post_rev-pre_rev, pre_rev)*100,2) AS pct_change
FROM pivoted ORDER BY region, test_group
""")

# Q8 - revenue per unit
run("Q8. Revenue per Unit (Volume vs Value)", """
SELECT s.test_group, sw.period,
  ROUND(SUM(sw.revenue),0) AS total_revenue,
  SUM(sw.units_sold) AS total_units,
  ROUND(SAFE_DIVIDE(SUM(sw.revenue), SUM(sw.units_sold)),2) AS revenue_per_unit
FROM sales_weekly sw JOIN stores s ON sw.store_id = s.store_id
WHERE sw.category_name = 'Electronics'
GROUP BY 1,2 ORDER BY 1,2
""")

# Q9 - top 5 stores by lift
run("Q9. Top 5 Test Stores by Individual Lift", """
WITH store_pivot AS (
  SELECT sw.store_id, s.region,
    SUM(CASE WHEN sw.period='Pre' THEN sw.revenue END) AS pre_rev,
    SUM(CASE WHEN sw.period='Post' THEN sw.revenue END) AS post_rev
  FROM sales_weekly sw JOIN stores s ON sw.store_id = s.store_id
  WHERE sw.category_name = 'Electronics' AND s.test_group = 'Test'
  GROUP BY 1,2
)
SELECT store_id, region,
  ROUND(pre_rev,0) AS pre_revenue, ROUND(post_rev,0) AS post_revenue,
  ROUND(SAFE_DIVIDE(post_rev-pre_rev, pre_rev)*100,2) AS pct_change
FROM store_pivot ORDER BY pct_change DESC LIMIT 5
""")

print("\n\nAll queries executed successfully against local data (DuckDB engine).")
