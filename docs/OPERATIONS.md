# Running and maintaining the project

Local: `python -m src.pipeline` from the repository root. The compatibility scripts
`python statistical_test.py`, `python sql/validate_queries.py` and
`python dashboard/build_dashboard.py` resolve the root from their own location.
Use `python /absolute/path/statistical_test.py` from another working directory.
Use --input-dir for a compatible alternative fixture; --output-dir keeps its
results separate. Do not run overlapping local refreshes into the same directory.

The pipeline stages calculations and presentation artifacts in a temporary
directory. Publication starts only after checks pass. Files are copied individually,
not transactionally across a whole directory; consumers should check run_status
and avoid reading during refresh. Failed CLI runs mark status failed and preserve
previous artifacts for diagnosis. Input hashes identify the source snapshot.

GitHub Actions runs tests and a full refresh on pushes, pull requests, manual
dispatch and Mondays at 06:00 UTC. It uploads results without writing to main.
Scheduled Actions only runs when the workflow is on the repository default branch.
No claim is made that remote CI has run until a successful run is visible.

Airflow alternative: install orchestration/circle_week_dag.py in an Airflow 2.10
environment and set CIRCLE_WEEK_REPO and CIRCLE_WEEK_PYTHON for the analytics
environment. The DAG runs Mondays 06:00 UTC, disables catchup, limits concurrency
to one run, retries failures and uses subprocess check=True. Parsing is unit-tested
with a lightweight decorator stub; real scheduler/operator integration needs an
Airflow environment. Airflow is intentionally excluded from core dependencies.

Git/agile practice: make scoped branches, run tests, inspect generated metrics,
open a PR with validation evidence and review before merging. A portfolio repo
demonstrates source control, not prior professional agile-team experience.

Not implemented/claimed: Oracle, Hive/HDFS, Teradata, Spark clusters, corporate
data access, actual Target data, production deployment or privacy certification.
These are alternative JD platforms; adding their names would not establish use.
