# Circle Week — Retail Promotion Effectiveness

**SQL · Python · BigQuery · Tableau · statistical analysis · Groq AI**

[**View the published Tableau dashboard**](https://public.tableau.com/app/profile/isfaque.ansari5273/viz/Circle_Week_Dashboard/Promotiondecisionbrief)

An independent retail analytics portfolio project asking: **Did an Electronics promotion increase revenue, and does the evidence support a limited follow-up pilot?**

The analysis uses synthetic data. It is not affiliated with Target and contains no actual Target sales or customer information.

## Project status

The portfolio workflow has been completed through local analysis, live BigQuery execution, a user-confirmed live Groq run, and Tableau publication.

The corrected implementation is on [`fix/target-retail-analytics`](https://github.com/Lifewitdata/circle-week-promo-analysis/tree/fix/target-retail-analytics), with [PR #1](https://github.com/Lifewitdata/circle-week-promo-analysis/pull/1) awaiting merge. Use that branch for the commands below.

| Component | Status |
|---|---|
| Python analysis and SQL reconciliation | Completed |
| Live BigQuery | Executed; primary effect reconciled with local analysis |
| Live AI | Groq summary execution confirmed by the project author |
| Tableau | Published; dashboard linked above |
| Airflow | Optional DAG implemented; live scheduler execution not verified |

## Business question and decision

Compare promotion and control stores before and during the promotion, estimate the revenue effect, check category and regional patterns, and examine whether assumed margins and promotion costs support further testing.

**Recommendation:** consider a limited Electronics pilot after checking margins, costs, stock availability and operating capacity. Revenue evidence alone does not establish profitability or justify a chain-wide rollout.

## Results

The panel contains **12,480 rows**, covering **60 stores**, **8 categories** and **26 weeks**: 13 pre-promotion and 13 promotion weeks. There are 28 test stores and 32 control stores.

| Measure | Result |
|---|---:|
| Primary additive difference-in-differences estimate | **$2,585.55 per store per week** |
| Store-clustered 95% confidence interval | **$2,265.95–$2,905.16 per store per week** |
| Estimated test-period revenue effect | **$941,141.76** |
| Average store revenue growth gap | **14.89 percentage points** |

The test-period estimate is the weekly effect multiplied by **28 test stores × 13 weeks**. The growth gap is a separate percentage-point measure, not a percent lift.

These results replace the earlier, unexplained $917K headline. They describe a synthetic case study, not realized business impact.

## Tableau dashboard

[**Open Retail Promotion Effectiveness — Promotion Decision Brief**](https://public.tableau.com/app/profile/isfaque.ansari5273/viz/Circle_Week_Dashboard/Promotiondecisionbrief)

The dashboard includes:

- Weekly Electronics revenue for test and control stores.
- Category effect estimates with uncertainty available in tooltips.
- Regional Electronics effect estimates.
- Three illustrative contribution scenarios.
- KPI cards for weekly effect, test-period revenue effect and the 95% confidence interval.

Four separate sources support the dashboard: `weekly_trend.csv`, `category_effects.csv`, `region_effects.csv` and `scenarios.csv`. They represent different aggregation levels and should not be joined into one table.

**Refresh:** Tableau Public uses extracted CSV snapshots. It is not a live BigQuery connection. Refresh the source files and republish after new analysis.

The published workbook is the presentation deliverable. The pipeline-generated local Tableau package is an intermediate artifact; native compatibility and extract creation may require manual work.

## Methods and controls

- Validate keys, dates, numeric values, dimension references and the complete weekly panel.
- Run ten canonical SQL queries and reconcile the primary estimate against Python.
- Estimate additive difference-in-differences with store-clustered inference and a whole-store bootstrap.
- Use Welch tests, pretrend diagnostics, category placebo checks and Holm-adjusted exploratory comparisons.
- Compare simple revenue forecasting baselines using a pre-promotion holdout.
- Model margin, promotion-cost and fixed-cost sensitivity, with break-even calculations.
- Retrieve approved project evidence for optional Groq summaries; validate selected fact and action identifiers before rendering numerical statements.

Recorded test/control labels are available, but the original randomization algorithm is not. Diagnostic checks do not establish all causal assumptions or prove the absence of spillovers.

## Cost scenarios

For **100 stores over 13 weeks**, assuming **30% gross margin**, **2% additional promotion cost** and **$500 fixed cost per store**:

| Effect assumption | Illustrative incremental contribution |
|---|---:|
| Lower effect | $313,313 |
| Point estimate | $429,650 |
| Upper effect | $545,987 |

Promotion cost applies to all modeled treated revenue. These are alternative sensitivity scenarios, not observed profit or rollout forecasts. Do not add the three scenarios together.

## Run the analysis

Clone the corrected implementation branch:

```bash
git clone --branch fix/target-retail-analytics https://github.com/Lifewitdata/circle-week-promo-analysis.git
cd circle-week-promo-analysis
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux instead: source .venv/bin/activate
pip install -r requirements.txt
python -m src.pipeline
python -m pytest -q
python -m src.ai_summary
```

Python 3.12 is recommended. Core analysis and offline summaries require no cloud credentials.

The pipeline produces reports and offline HTML, PNG/PDF and Tableau source outputs. Open `dashboard/index.html` for the offline interactive report. Dashboard DOM checks are available with `npm ci` followed by `npm run test:dashboard`.

## Live BigQuery

The completed sandbox run used dataset `circle_week_sandbox` with an **unpartitioned, clustered** fact table. Historical date partitions were unsuitable for the sandbox's automatic partition expiry. Live partition pruning is not claimed.

To reproduce in your own dedicated project:

```bash
pip install -r requirements-cloud.txt
gcloud auth application-default login
python -m src.bigquery_runner --project YOUR_PROJECT --dataset circle_week_sandbox --load --unpartitioned
python -m src.bigquery_runner --project YOUR_PROJECT --dataset circle_week_sandbox --execute --benchmark
```

`--load` replaces the four tables in the selected dataset. Execution uses per-query billing caps. The default query mode is dry-run. Local job evidence and results are written under `reports/live_bigquery/` and are gitignored.

The live run returned **$2,585.5542 per store per week** and a **14.8860 percentage-point** store growth gap, consistent with the local analysis.

## Live AI summaries

Set `GROQ_API_KEY` and `GROQ_MODEL` in your shell. The completed setup used `openai/gpt-oss-120b`.

```bash
python -m src.ai_summary --live --question "What revenue evidence supports a limited pilot?"
```

Live Groq execution was confirmed by the project author. Offline mode remains explicitly extractive. Never commit API keys, cloud credentials or credential files.

## Implementation and documentation

The following links point to the corrected implementation branch:

- [Pipeline and source modules](https://github.com/Lifewitdata/circle-week-promo-analysis/tree/fix/target-retail-analytics/src)
- [Canonical SQL](https://github.com/Lifewitdata/circle-week-promo-analysis/blob/fix/target-retail-analytics/sql/queries.sql)
- [Validated results](https://github.com/Lifewitdata/circle-week-promo-analysis/blob/fix/target-retail-analytics/reports/summary.json)
- [Executive summary](https://github.com/Lifewitdata/circle-week-promo-analysis/blob/fix/target-retail-analytics/reports/executive_summary.md)
- [Metric definitions](https://github.com/Lifewitdata/circle-week-promo-analysis/blob/fix/target-retail-analytics/docs/metric_definitions.md)
- [Methodology](https://github.com/Lifewitdata/circle-week-promo-analysis/blob/fix/target-retail-analytics/docs/methodology.md)
- [BigQuery setup and sandbox guidance](https://github.com/Lifewitdata/circle-week-promo-analysis/blob/fix/target-retail-analytics/docs/BIGQUERY_IMPLEMENTATION_GUIDE.md)
- [AI workflow](https://github.com/Lifewitdata/circle-week-promo-analysis/blob/fix/target-retail-analytics/docs/AI_WORKFLOW.md)
- [Data governance](https://github.com/Lifewitdata/circle-week-promo-analysis/blob/fix/target-retail-analytics/docs/governance.md)
- [Operations and Airflow setup](https://github.com/Lifewitdata/circle-week-promo-analysis/blob/fix/target-retail-analytics/docs/OPERATIONS.md)

Some earlier verification documents predate the live walkthrough. The status table above records the later BigQuery, Groq and Tableau milestones. Native Tableau pixel layout and extract contents were not independently verified in the automated review environment.

## Tools

Python, pandas, NumPy, SciPy, statsmodels, DuckDB, SQL, Google BigQuery, Tableau Public, Groq, GitHub Actions and an optional Airflow DAG.

This small synthetic panel is a portfolio demonstration, not a production-scale benchmark.
