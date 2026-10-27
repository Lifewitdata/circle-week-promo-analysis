# Experiment design, diagnostics and limitations

This is a synthetic case study, not an evaluation of Target's real Circle Week.
The original generator and assignment algorithm were not committed. Existing
test/control labels are observed; the project cannot verify original randomization.
`data/generate_data.py` supplies a separate seeded randomized fixture. It does
not reproduce the old generator or preserve the original headline figures.

The committed panel contains 60 stores, 8 categories and 26 weeks: 13 pre and
13 post. Store is the unit of allocation and inference. Repeated weekly rows
are correlated, so treating 1,560 Electronics rows as independent would overstate
precision. We use store-clustered OLS and a 2,000-draw whole-store bootstrap.
Welch's t-test and Cohen's d compare store percentage changes as secondary checks.

Primary dollar DiD assumes the test stores would experience the control stores'
average dollar change without treatment. This is not guaranteed by a chart or
by a nonsignificant test. A pre-period group × time interaction is reported as
a diagnostic. Baseline differences, seasonality, changing store composition,
spillovers and stock availability remain threats to interpretation.

Each non-Electronics category receives a separate DiD regression. Seven placebo
p-values receive Holm family-wise correction. Four regional comparisons receive
their own Holm correction and remain exploratory (small store counts). Individual
95% confidence intervals shown in charts are not simultaneous intervals. A null
result is insufficient evidence to claim "no spillovers" or "effect isolation proven."

Prospective real experiment: specify primary incremental contribution, a minimum
commercially useful effect, a store-level power calculation, stratification by
region/format and a recorded random seed before launch. Monitor stockout rate,
returns, margin and customer complaints as guardrails; these are not present in
the synthetic source. Avoid early repeated significance peeking. Preserve holdout
stores and check execution/compliance. No retrospective p-value proves power.

The new generator's known injected effect is for simulation testing, not evidence
that the analyst discovered a real commercial opportunity. Re-running with a new
seed or effect should change estimates. All estimates require external validity
checks before applying them to new stores or longer durations.

No classification target is available. Adding an arbitrary classifier would not
improve this experiment. DemandPilot is the complementary portfolio forecasting
project; the local revenue baseline benchmark only demonstrates temporal holdout
discipline and must not be sold as a production inventory model.
