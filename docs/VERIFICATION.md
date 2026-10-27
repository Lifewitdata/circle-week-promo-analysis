# Verification record — 27 October 2026

Local Python 3.12 execution; primary data files unchanged.

| Check | Result |
|---|---|
| Complete pipeline on committed input | Passed; 12,480 rows, 60 stores, 8 categories, 26 weeks |
| Ten canonical analytical SQL queries | Executed in DuckDB; primary effect reconciled with Python |
| Python suite | 37 tests passed, including malformed data, zero-effect estimator, SQL parity, leakage, scenario accounting, AI validation and mocked cloud configuration |
| Dashboard controls | DOM execution passed for KPI values, tabs, region filtering, cost recalculation, invalid inputs and no external runtime dependencies |
| PNG | Visually inspected: no overlapping labels or clipped panels |
| Tableau package | XML parses; ZIP integrity and column/source references verified; four CSVs embedded |
| CLI from another working directory | Tested using absolute compatibility entry-point path |
| Alternative seeded fixture with zero injected effect | Complete pipeline passed; weekly effect $12.55, 95% CI −$177.68 to $202.78, p=0.8954 |
| Markdown links | All local targets exist |
| Python compilation / git whitespace | Passed |

The zero-effect simulation is a smoke check on a separate generated dataset, not
a repeated-simulation coverage or type-I-error study. It does not replace the
committed synthetic experiment or prove causal validity of its findings.

Not verified here: native Tableau opening/rendering/publication; authenticated
BigQuery load/query/cost benchmark; live Groq model quality; real Airflow scheduler;
Oracle/Hive/HDFS/Spark; real-browser HTML layout. Browser binary downloads were
unavailable, so HTML interactions were checked through DOM execution instead.

Mock SDK/transport tests verify application configuration and failure handling,
not external service behaviour. Generated live evidence is required before those
capabilities can be described as executed. GitHub Actions results are separate
from this local verification record and must be checked on the pull request.
