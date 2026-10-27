# Circle Week — retail promotion and rollout analysis

**SQL · Python · retail experiment analysis · Tableau package · BigQuery workflow · grounded AI reporting**

Did a synthetic Electronics promotion increase store revenue, and would a rollout
still make sense after costs? This independent portfolio project follows that
question from input validation to an executive decision brief. It is not affiliated
with Target and contains no actual Target sales or customer data.

![Results dashboard](dashboard/dashboard.png)

## What the committed data supports

The complete panel contains **12,480 store/category/week rows**, **60 stores**,
**8 categories**, **13 pre weeks and 13 post weeks** (28 Test, 32 Control stores).

The validated pipeline regenerates all figures in
[the executive brief](reports/executive_summary.md) and
[machine-readable results](reports/summary.json).

| Measure | Estimate | Interpretation |
|---|---:|---|
| Primary additive DiD | $2,585.55/store/week | Synthetic incremental revenue estimate |
| Store-clustered 95% CI | $2,265.95–$2,905.16/store/week | Uncertainty under the model |
| Test-store incremental revenue | $941,141.76 | Primary effect × 28 stores × 13 weeks |
| Average store growth gap | 14.89 percentage points | Secondary comparison; not percent lift |

The old $917K headline was not reproducible from a documented estimator. This
version uses one defined additive DiD throughout and separately labels percentage
growth diagnostics. The original randomization algorithm is unavailable: recorded
test/control labels are observed, not independently verified random assignment.

**Decision:** consider a limited follow-up pilot after verifying margins, costs and
stock availability. Revenue evidence alone does not establish profitability or
justify chain-wide rollout. Synthetic effects may be designed into generated data.

## Run locally

Python 3.12 recommended. No cloud account or model key is needed for core analysis.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m src.pipeline
python -m pytest -q
python -m src.ai_summary
```

Optional reproducible dashboard-control checks (Node 24+): `npm ci` then
`npm run test:dashboard`. These execute the DOM; they do not replace native browser
layout inspection. The PNG is visually inspected; Tableau native rendering is unverified.

Open `dashboard/index.html` directly: it works offline and includes cost what-if
controls and a region-filtered store-growth table. Open
`dashboard/Circle_Week.twbx` in Tableau Desktop/Public for the native workbook.
See [Tableau verification limits and refresh instructions](docs/TABLEAU_GUIDE.md).

Compatibility entry points (`statistical_test.py`, `sql/validate_queries.py`,
`dashboard/build_dashboard.py`) run the same pipeline and use portable paths.

## What is implemented

- **Data contracts:** unique fact/dimension keys, numeric/date validity, assignment
  consistency, referential integrity, complete weekly panel and equal windows.
- **SQL warehouse:** ten canonical BigQuery/DuckDB queries using joins, CTEs,
  conditional aggregation, window functions and safe division. SQL and Python
  primary results must reconcile before reports publish. TEMP-table example included.
- **Statistical analysis:** store-clustered DiD with t-based CIs, whole-store
  bootstrap, Welch test, Cohen's d, pretrend diagnostic, per-category placebo tests
  and regional comparisons with Holm correction. Null checks do not prove no spillovers.
- **Decision scenarios:** configurable margin, additional promo costs, fixed costs,
  rollout stores and duration; effect-bound sensitivity and break-even margin.
  These are assumptions, not observed profit or rollout forecasts.
- **Time-aware benchmark:** last-week, four-week mean and drift revenue baselines;
  last four pre-promotion weeks held out. No post-treatment leakage. This small
  benchmark does not establish annual demand forecasting capability.
- **Reporting:** regenerated offline HTML, PNG/PDF, four-sheet Tableau package,
  CSV outputs, source hashes, executive brief and documented definitions.
- **Cloud workflow:** explicit BigQuery schemas, partitioned/clustered fact load,
  dry-runs, billing caps, optional execution, job evidence and result reconciliation.
- **AI workflow:** local document retrieval, optional Groq selection of approved
  facts/actions, strict output validation and source provenance. Offline mode is
  labelled extractive. No unverified LLM prose or model-generated SQL executes.
- **Operations:** tests, scheduled/manual GitHub Actions refresh and an optional
  Airflow DAG with retries and concurrency control.

## Optional live BigQuery and AI

```bash
pip install -r requirements-cloud.txt
gcloud auth application-default login
python -m src.bigquery_runner --project YOUR_PROJECT --load
python -m src.bigquery_runner --project YOUR_PROJECT --execute --benchmark
# Set GROQ_API_KEY and GROQ_MODEL in your shell, then:
python -m src.ai_summary --live --question "What evidence supports a limited pilot?"
```

`--load` replaces four tables in the selected dedicated portfolio dataset.
Default query mode is dry-run; `--execute` incurs query work under a per-query
cap. [Cloud details and evidence](docs/BIGQUERY_IMPLEMENTATION_GUIDE.md).
Live outputs are gitignored. No GCP or Groq run is claimed without account evidence.

## Reproducibility and evidence

| Claim | Evidence |
|---|---|
| Input accuracy and panel completeness | src/validation.py; reports/data_quality.json |
| SQL / Python parity | sql/queries.sql; reports/sql/primary_effect.csv; tests/test_project.py |
| Effect, uncertainty and diagnostics | src/analysis.py; reports/summary.json; reports/category_effects.csv |
| Commercial decision logic | src/scenarios.py; config.json; reports/scenarios.csv |
| Temporal validation | src/forecast.py; reports/forecast_predictions.csv |
| Tableau artifact | src/tableau.py; dashboard/Circle_Week.twbx; native rendering still requires Tableau |
| Retrieval / AI controls | src/ai_summary.py; reports/ai_offline/; docs/AI_WORKFLOW.md |
| Cloud implementation | src/bigquery_runner.py; live verification requires GCP |
| Scheduled workflow | .github/workflows/validate.yml; orchestration/circle_week_dag.py |

An alternative generator creates a **new fixture**, preserving the committed data:

```bash
python data/generate_data.py --output /tmp/circle-fixture --seed 42
python -m src.pipeline --input-dir /tmp/circle-fixture --output-dir /tmp/circle-results
```

Use a Windows path instead of /tmp when appropriate. Fixtures must use the same
Electronics category and 2026 date window as the canonical SQL. Do not compare
different fixtures without checking input hashes. Scenarios and results change
with the injected effect and seed.

## Documentation

- [Data dictionary and warehouse grain](docs/data_dictionary.md)
- [Metric definitions](docs/metric_definitions.md)
- [Methodology and experiment limitations](docs/methodology.md)
- [Governance and responsible AI](docs/governance.md)
- [Tableau guide](docs/TABLEAU_GUIDE.md)
- [BigQuery guide](docs/BIGQUERY_IMPLEMENTATION_GUIDE.md)
- [AI workflow and evaluation](docs/AI_WORKFLOW.md)
- [Operations and Airflow setup](docs/OPERATIONS.md)
- [Verification record and remaining live checks](docs/VERIFICATION.md)

Oracle, Hive/HDFS, Teradata and Spark are not claimed. Git use does not prove
professional agile-team experience. A small synthetic panel is not a large-scale
production benchmark. Source code availability, XML validation, mocked tests and
live execution are distinct evidence levels; see the guides before making resume claims.
