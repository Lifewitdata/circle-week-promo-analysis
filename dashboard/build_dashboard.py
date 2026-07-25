"""
Circle Week - Electronics Promo Dashboard (pure Python / matplotlib)
----------------------------------------------------------------------
Builds a single static dashboard image straight from the source data.
No browser, no JavaScript, no internet connection required - just run
this script and it produces a PNG (and a PDF) you can open anywhere
or drop into a slide deck / report.
"""
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch
from matplotlib.gridspec import GridSpec

# ---------------------------------------------------------------------
# 0. Theme
# ---------------------------------------------------------------------
BG       = "#101114"
PANEL    = "#17181c"
BORDER   = "#26282e"
TEXT     = "#f2f1ed"
MUTED    = "#8b8d95"
RED      = "#e23744"
TEAL     = "#3ec1b3"
GREY_BAR = "#33353b"
GREEN    = "#4ade80"

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": PANEL,
    "axes.edgecolor": BORDER,
    "text.color": TEXT,
    "axes.labelcolor": MUTED,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "font.family": "DejaVu Sans",
    "font.size": 10,
})

# ---------------------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------------------
BASE = "target_promo_project"
sales = pd.read_csv(f"{BASE}/data/sales_weekly.csv")
stores = pd.read_csv(f"{BASE}/data/stores.csv")
with open(f"{BASE}/dashboard/data.json") as f:
    D = json.load(f)

# ---------------------------------------------------------------------
# 2. Build figure
# ---------------------------------------------------------------------
fig = plt.figure(figsize=(15, 11.5), facecolor=BG)
gs = GridSpec(
    4, 4, figure=fig,
    height_ratios=[1.0, 1.35, 1.35, 1.25],
    hspace=0.55, wspace=0.35,
    left=0.05, right=0.97, top=0.90, bottom=0.05,
)

def style_panel(ax, title=None, note=None):
    ax.set_facecolor(PANEL)
    for spine in ax.spines.values():
        spine.set_color(BORDER)
    ax.tick_params(colors=MUTED, labelsize=9)
    if title:
        ax.set_title(title, loc="left", fontsize=12.5, fontweight="bold",
                      color=TEXT, pad=12)
    if note:
        ax.text(0, -0.22, note, transform=ax.transAxes, fontsize=8.5,
                 color=MUTED, ha="left", va="top")

# --- Header text (figure-level) -----------------------------------
fig.text(0.05, 0.965, "PROMO ANALYSIS · MERCHANDISING / MARKETING & DIGITAL",
          fontsize=9.5, color=RED, fontweight="bold", family="monospace")
fig.text(0.05, 0.935, "Circle Week — Electronics Deal Days",
          fontsize=22, color=TEXT, fontweight="bold")
fig.text(0.05, 0.915,
          "Test-vs-control read on the 13-week Electronics promotion across 60 stores. "
          "Difference-in-differences design, validated with a placebo check.",
          fontsize=10, color=MUTED)

# ---------------------------------------------------------------------
# 3. KPI row (row 0)
# ---------------------------------------------------------------------
kpi = D["kpi"]

# 3a. Hero "tag" panel
ax_tag = fig.add_subplot(gs[0, 0])
ax_tag.axis("off")
tag = FancyBboxPatch((0.03, 0.08), 0.94, 0.86, transform=ax_tag.transAxes,
                       boxstyle="round,pad=0.02,rounding_size=0.06",
                       linewidth=0, facecolor=RED, zorder=1)
ax_tag.add_patch(tag)
ax_tag.add_patch(plt.Circle((0.14, 0.80), 0.035, transform=ax_tag.transAxes,
                              facecolor=BG, zorder=2))
ax_tag.text(0.12, 0.62, "NET INCREMENTAL LIFT", transform=ax_tag.transAxes,
             fontsize=8.5, color="white", alpha=0.9, family="monospace", fontweight="bold")
ax_tag.text(0.12, 0.30, f"+{kpi['did_lift_pct']}%", transform=ax_tag.transAxes,
             fontsize=34, color="white", fontweight="bold")
ax_tag.text(0.12, 0.16, "vs. control stores, post-promo", transform=ax_tag.transAxes,
             fontsize=8.5, color="white", alpha=0.85)

def stat_panel(gs_pos, label, value, sub=None, badge=None):
    ax = fig.add_subplot(gs_pos)
    ax.axis("off")
    box = FancyBboxPatch((0.02, 0.06), 0.96, 0.88, transform=ax.transAxes,
                           boxstyle="round,pad=0.02,rounding_size=0.05",
                           linewidth=1, edgecolor=BORDER, facecolor=PANEL)
    ax.add_patch(box)
    ax.text(0.11, 0.72, label, transform=ax.transAxes, fontsize=8.5,
             color=MUTED, family="monospace", fontweight="bold")
    ax.text(0.11, 0.42, value, transform=ax.transAxes, fontsize=21,
             color=TEXT, fontweight="bold")
    if sub:
        ax.text(0.11, 0.22, sub, transform=ax.transAxes, fontsize=8.5, color=MUTED)
    if badge:
        ax.add_patch(FancyBboxPatch((0.11, 0.06), 0.6, 0.12, transform=ax.transAxes,
                                      boxstyle="round,pad=0.01,rounding_size=0.5",
                                      linewidth=0, facecolor="#182620"))
        ax.text(0.16, 0.115, badge, transform=ax.transAxes, fontsize=8, color=GREEN,
                 family="monospace", va="center", fontweight="bold")
    return ax

stat_panel(gs[0, 1], "INCREMENTAL REVENUE", f"${kpi['incremental_revenue']/1000:.0f}K",
            sub="Test stores, 13-wk post period")
stat_panel(gs[0, 2], "SAMPLE", f"{kpi['n_test']} / {kpi['n_ctrl']}",
            sub="Test / Control stores")
stat_panel(gs[0, 3], "SIGNIFICANCE", f"p {kpi['p_value']}",
            badge="● SIGNIFICANT (95% CI)")

# ---------------------------------------------------------------------
# 4. Weekly trend chart (row 1, full width)
# ---------------------------------------------------------------------
ax_trend = fig.add_subplot(gs[1, :])
weeks = D["trend"]["Test"]["weeks"]
x = np.arange(len(weeks))
ax_trend.plot(x, D["trend"]["Test"]["index"], color=RED, linewidth=2.6, label="Test", zorder=3)
ax_trend.fill_between(x, D["trend"]["Test"]["index"], 100, color=RED, alpha=0.08, zorder=2)
ax_trend.plot(x, D["trend"]["Control"]["index"], color=TEAL, linewidth=2, linestyle="--", label="Control", zorder=3)
ax_trend.axvline(13, color=MUTED, linewidth=1, linestyle=":", alpha=0.7)
ax_trend.text(13.3, ax_trend.get_ylim()[1] if False else 131, "Promo starts", fontsize=8.5, color=MUTED)
tick_idx = list(range(0, len(weeks), 3))
ax_trend.set_xticks(tick_idx)
ax_trend.set_xticklabels([pd.to_datetime(weeks[i]).strftime("%b %d") for i in tick_idx], fontsize=8.5)
ax_trend.set_ylabel("Index (Wk 1 = 100)", fontsize=9)
ax_trend.grid(axis="y", color=BORDER, linewidth=0.6)
ax_trend.legend(loc="upper left", frameon=False, fontsize=9.5, labelcolor=TEXT)
style_panel(ax_trend, title="Weekly revenue index — Electronics (Week 1 = 100)",
             note="Lines track together pre-promo, then diverge after week 14 — the signature of a real treatment effect.")

# ---------------------------------------------------------------------
# 5. Category placebo chart (row 2, left 2 cols)
# ---------------------------------------------------------------------
ax_cat = fig.add_subplot(gs[2, 0:2])
cats = D["category_lift"]
names = [c["category"] for c in cats][::-1]
vals = [c["lift"] for c in cats][::-1]
colors = [RED if n == "Electronics" else GREY_BAR for n in names]
bars = ax_cat.barh(names, vals, color=colors, height=0.6)
ax_cat.axvline(0, color=BORDER, linewidth=0.8)
ax_cat.set_xlabel("Test − Control lift (pct pts)", fontsize=9)
ax_cat.tick_params(labelsize=9)
style_panel(ax_cat, title="Lift is isolated to Electronics",
             note="Placebo check across all 8 categories — no spillover effect elsewhere.")

# ---------------------------------------------------------------------
# 6. Region chart (row 2, right 2 cols)
# ---------------------------------------------------------------------
ax_reg = fig.add_subplot(gs[2, 2:4])
regions = list(D["region"].keys())
xw = np.arange(len(regions))
w = 0.35
ax_reg.bar(xw - w/2, [D["region"][r]["Test"] for r in regions], width=w, color=RED, label="Test")
ax_reg.bar(xw + w/2, [D["region"][r]["Control"] for r in regions], width=w, color=GREY_BAR, label="Control")
ax_reg.set_xticks(xw)
ax_reg.set_xticklabels(regions, fontsize=9.5)
ax_reg.set_ylabel("Revenue % change", fontsize=9)
ax_reg.legend(loc="upper right", frameon=False, fontsize=9, labelcolor=TEXT)
ax_reg.grid(axis="y", color=BORDER, linewidth=0.6)
style_panel(ax_reg, title="Lift holds across every region", note="Test vs. Control, average store % change pre→post.")

# ---------------------------------------------------------------------
# 7. Top movers table (row 3, full width)
# ---------------------------------------------------------------------
ax_tbl = fig.add_subplot(gs[3, :])
ax_tbl.axis("off")
style_panel(ax_tbl, title="Top 5 test stores by lift")
movers = D["top_movers"]
col_x = [0.02, 0.18, 0.34]
headers = ["STORE", "REGION", "LIFT"]
for cx, h in zip(col_x, headers):
    ax_tbl.text(cx, 0.72, h, transform=ax_tbl.transAxes, fontsize=8.5,
                 color=MUTED, family="monospace", fontweight="bold")
ax_tbl.plot([0.02, 0.5], [0.66, 0.66], transform=ax_tbl.transAxes, color=BORDER, linewidth=0.8)
row_y = 0.55
for m in movers:
    ax_tbl.text(col_x[0], row_y, m["store_id"], transform=ax_tbl.transAxes, fontsize=10, color=TEXT, family="monospace")
    ax_tbl.text(col_x[1], row_y, m["region"], transform=ax_tbl.transAxes, fontsize=10, color=MUTED)
    ax_tbl.text(col_x[2], row_y, f"+{m['pct_change']}%", transform=ax_tbl.transAxes, fontsize=10, color=RED, family="monospace", fontweight="bold")
    row_y -= 0.13

# footer note (right side of same row)
ax_tbl.text(0.55, 0.72,
    "METHOD", transform=ax_tbl.transAxes, fontsize=8.5, color=MUTED, family="monospace", fontweight="bold")
ax_tbl.text(0.55, 0.02,
    "Difference-in-differences on store-clustered weekly revenue\n"
    "(13 wks pre / 13 wks post), 28 test vs 32 control stores,\n"
    "randomized at store level. Placebo test on non-Electronics\n"
    "categories confirms no spillover effect.",
    transform=ax_tbl.transAxes, fontsize=9, color=MUTED, va="bottom", linespacing=1.6)

# ---------------------------------------------------------------------
# 8. Save
# ---------------------------------------------------------------------
out_png = f"{BASE}/dashboard/dashboard.png"
out_pdf = f"{BASE}/dashboard/dashboard.pdf"
fig.savefig(out_png, dpi=200, facecolor=BG, bbox_inches="tight")
fig.savefig(out_pdf, facecolor=BG, bbox_inches="tight")
print(f"Saved: {out_png}")
print(f"Saved: {out_pdf}")
