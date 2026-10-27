# BigQuery: load, query, validate and record evidence

Use a dedicated disposable portfolio dataset. `--load` creates it if needed and
replaces the four same-named tables there. It does not alter unrelated datasets.
Choose your own GCP project, billing configuration and location in config.json.

```bash
pip install -r requirements-cloud.txt
gcloud auth application-default login
python -m src.pipeline
python -m src.bigquery_runner --project YOUR_PROJECT --load
python -m src.bigquery_runner --project YOUR_PROJECT --execute --benchmark
```

First command with --load incurs load/storage operations, then dry-runs all
analytical queries against existing tables. Without --load it only dry-runs.
--execute runs queries with query cache disabled and a configurable per-query
maximum_bytes_billed cap (default 1 GB). The cap is not a project-wide budget.
Credentials and GCP charges remain in the user's environment. The Python client
uses Application Default Credentials; never put credential JSON in the repo.

## Historical data in BigQuery sandbox

Sandbox applies 60-day partition expiry. This dataset's January–June 2026 date
partitions can expire immediately when loaded later in the year: a load can
complete but leave zero queryable rows. Confirm with get_table().time_partitioning
and an unfiltered row count. Do not change the synthetic business dates to hide this.

Use a NEW dedicated dataset with the sandbox load option:

```bash
python -m src.bigquery_runner --project YOUR_PROJECT --dataset circle_week_sandbox --load --unpartitioned
python -m src.bigquery_runner --project YOUR_PROJECT --dataset circle_week_sandbox --execute --benchmark
```

This preserves clustering and original dates while omitting date partitioning.
The table still has sandbox table-expiration limits, counted from table creation.
It is not evidence of partition pruning; benchmark results must be labelled
unpartitioned. Existing partitioned tables cannot be converted by WRITE_TRUNCATE;
the separate dataset avoids deleting or silently reconfiguring existing tables.
The default partitioned option remains available in an appropriately configured
billing-enabled project, after checking/removing any inherited partition expiry.

Official references:
- https://docs.cloud.google.com/bigquery/docs/sandbox
- https://docs.cloud.google.com/bigquery/docs/managing-partitioned-tables

The fact table is date-partitioned on week_start_date and clustered by category_id,
store_id. Core queries project required columns, filter the fixed date window,
join on dimension keys and aggregate at a defined grain. At 12,480 rows, a partition
or clustering benchmark may show little/no savings. Do not promise an improvement.
The benchmark writes dry-run bytes and actual bytes, slot milliseconds and job IDs.
Compare performance only after confirming identical result columns/rows; clustering
dry-run estimates can be upper bounds. Query cache is disabled for the measurement.

Primary-effect execution compares BigQuery output to local reports/summary.json.
Failure raises instead of silently marking the cloud workflow complete. Execution
evidence is written to reports/live_bigquery/execution_evidence.json (gitignored).
Review/redact project IDs before sharing evidence publicly. Run dates, billing and
job IDs are actual evidence only after the cloud command succeeds.

The TEMP table example in sql/temporary_tables.sql demonstrates session-scoped
materialization. BigQuery TEMP and Teradata VOLATILE are related concepts with
different syntax; this project does not establish Teradata experience.

Official references:
- https://docs.cloud.google.com/bigquery/docs/running-queries
- https://cloud.google.com/bigquery/docs/creating-clustered-tables
- https://docs.cloud.google.com/python/docs/reference/bigquery/latest/google.cloud.bigquery.job.QueryJobConfig

**Current verification:** local SQL execution and cloud configuration tests only
unless live evidence has been generated in your account. No authenticated GCP
execution is implied by the presence of this guide or SQL.
