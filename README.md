<div align="center">

# 🎯 Circle Week — Electronics Promo Effectiveness Analysis
### A Test-vs-Control Data Analytics Case Study, built for Target-style Retail Analytics

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-BigQuery-4285F4?style=for-the-badge&logo=googlebigquery&logoColor=white)
![Status](https://img.shields.io/badge/Status-Complete-4ade80?style=for-the-badge)
![License](https://img.shields.io/badge/Use-Portfolio%20Project-e23744?style=for-the-badge)

![Net Lift](https://img.shields.io/badge/Net%20Incremental%20Lift-%2B14.9%25-e23744?style=flat-square)
![Significance](https://img.shields.io/badge/Significance-p%20%3C%200.001-4ade80?style=flat-square)
![Revenue](https://img.shields.io/badge/Incremental%20Revenue-%24917K-3ec1b3?style=flat-square)
![Stores](https://img.shields.io/badge/Stores%20Tested-60-8b8d95?style=flat-square)

<br>

<img src="docs/trend_animation.gif" width="640" alt="Test vs Control weekly revenue trend, animated">

*Test stores (red) and control stores (teal) track together for 13 weeks — then diverge the moment the promo launches.*

</div>

---

## 📌 The Business Question

> Did the **"Circle Week — Electronics Deal Days"** promotion actually drive incremental
> revenue, or would sales have grown anyway? And if it worked, should it be rolled out
> chain-wide?

This is a full end-to-end analytics case study — from raw data generation through SQL,
statistics, dashboarding, and a stakeholder-ready executive summary — built to mirror
the kind of test-and-measure work a **Data Analytics / Merchandising Insights** team
does day to day (BigQuery, SQL, Python, A/B testing, BI storytelling).

## 🧭 tl;dr — What we found

| Metric | Result |
|---|---|
| **Net incremental lift** | **+14.9%** (Test vs. Control, post-promo) |
| **Incremental revenue** | **~$917K** over the 13-week test window |
| **Statistical significance** | **p < 0.000001** (Welch's t-test + clustered DiD regression) |
| **Effect isolation** | Placebo-tested — ~0% lift in every *other* category |
| **Regional consistency** | Significant lift in all 4 regions (11–21 pts) |
| **Driver** | Volume, not price — revenue-per-unit was flat |
| **Recommendation** | Expand the mechanic to all stores for the next promo cycle |

---

## 🗂️ Project Structure

```
target_promo_project/
├── data/
│   ├── generate_data.py          # Synthetic Target-style dataset generator
│   ├── stores.csv                 # 60 stores — region, format, sq ft, test/control
│   ├── products.csv               # 8 departments (Electronics, Grocery, etc.)
│   ├── promotions.csv             # Promo metadata
│   └── sales_weekly.csv           # 12,480 rows — weekly store × category revenue
│
├── sql/
│   ├── queries.sql                # 10 BigQuery queries (DiD, placebo, region, etc.)
│   └── validate_queries.py        # DuckDB proof-run of the same logic locally
│
├── analysis/
│   └── statistical_test.py        # t-test, Cohen's d, clustered DiD regression,
│                                   #   placebo model, region-level significance
│
├── dashboard/
│   ├── build_dashboard.py         # Python/matplotlib dashboard generator
│   ├── dashboard.png / .pdf       # Rendered static dashboard
│   ├── index.html                 # Chart.js interactive version (needs internet)
│   └── data.json                  # Aggregated data feeding both dashboards
│
└── docs/
    ├── executive_summary.docx     # 1-page stakeholder writeup (BLUF + findings)
    ├── build_exec_summary.js      # Generates the .docx via the `docx` npm package
    ├── build_animation.py         # Generates the animated hero GIF above
    ├── trend_animation.gif
    ├── trend_mini.png
    └── BIGQUERY_IMPLEMENTATION_GUIDE.md   # Step-by-step: run this for real in GCP
```

---

## 🔬 Methodology

**Design:** Randomized test-vs-control at the store level. 60 stores split
~50/50, promo targeted **only** the Electronics category, **only** in Test stores,
**only** in the 13-week post period.

**Why Difference-in-Differences (DiD):** Simple pre/post comparison would confuse
the promo's effect with normal seasonal growth. DiD nets out the Control group's
natural change, isolating the number that's actually attributable to the promo.

```
DiD Lift  =  (% change in Test group)  −  (% change in Control group)
          =  20.2%  −  5.3%
          =  14.9%  incremental lift
```

**Validation checks performed (this is what separates a rigorous analysis from a
surface-level one):**
- ✅ **Placebo test** — ran the identical model on every *non*-Electronics category;
  lift is ~0% and not significant, confirming the effect isn't just "Test stores
  sell more of everything."
- ✅ **Clustered standard errors** — regression clusters by `store_id` so the model
  doesn't overstate confidence from having many correlated weekly observations per store.
- ✅ **Effect size, not just p-value** — Cohen's d reported alongside significance,
  since statistical significance alone doesn't tell you if an effect is *meaningful*.
- ✅ **Volume vs. price decomposition** — checked revenue-per-unit to confirm the lift
  was driven by more units sold, not a pricing/mix artifact.

---

## ▶️ How to Run This Yourself

```bash
# 1. Generate the synthetic dataset
cd data && python3 generate_data.py

# 2. Validate the SQL logic locally (DuckDB — no BigQuery account needed)
cd ../sql && python3 validate_queries.py

# 3. Run the statistical significance tests
cd ../analysis && python3 statistical_test.py

# 4. Build the dashboard
cd ../dashboard && python3 build_dashboard.py

# 5. (Optional) Rebuild the animated GIF
cd ../docs && python3 build_animation.py
```

To run the SQL for real in the cloud instead of DuckDB, see
**[`docs/BIGQUERY_IMPLEMENTATION_GUIDE.md`](docs/BIGQUERY_IMPLEMENTATION_GUIDE.md)**
for a full step-by-step walkthrough (GCP project setup → load CSVs → run
`sql/queries.sql` → optionally connect Looker Studio).

---

## 🛠️ Tech Stack

`Python` · `pandas` · `numpy` · `scipy` · `statsmodels` · `matplotlib` · `DuckDB` ·
`BigQuery SQL` · `Chart.js` · `docx` (Node.js)

---

<div align="center">

*Built as a portfolio project simulating a Data Analytics role spanning*
*Merchandising, Marketing & Digital, and BI/Advanced Analytics.*

</div>
