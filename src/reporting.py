"""Generate all presentation artifacts from the calculated results."""
import base64
import html
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd


def write_reports(out, summary, changes, placebo, regions, trend, unit, scenario, forecast_metrics, quality, config):
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    tables={'store_growth':changes,'category_effects':placebo,'region_effects':regions,
            'weekly_trend':trend,'revenue_per_unit':unit,'scenarios':scenario,'forecast_metrics':forecast_metrics}
    for name,frame in tables.items():
        frame.to_csv(out/f'{name}.csv',index=False)
    (out/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    (out/'data_quality.json').write_text(json.dumps(quality,indent=2)+'\n')
    main=scenario[scenario.scenario=='Point estimate'].iloc[0]
    text=f'''# Electronics promotion: decision brief

Synthetic portfolio case study — not Target company data or an actual business result.

**Decision:** consider a limited follow-up pilot, subject to verified margins, stock
availability and promotion costs. Revenue evidence alone does not justify chain-wide rollout.

- Across {summary['n_test']} test and {summary['n_control']} control stores, the additive
  difference-in-differences estimate is **${summary['effect_usd_per_store_week']:,.2f} additional
  revenue per test store per week** (95% store-clustered CI:
  ${summary['effect_ci_low']:,.2f}–${summary['effect_ci_high']:,.2f}).
- Over {summary['post_weeks']} weeks, that is **${summary['incremental_revenue_usd']:,.2f} estimated
  incremental revenue** in the test stores (CI ${summary['incremental_revenue_ci_low']:,.2f}–
  ${summary['incremental_revenue_ci_high']:,.2f}). This assumes the control group's
  dollar change represents the test group's counterfactual dollar change.
- The average store growth gap is **{summary['store_growth_gap_pp']:.2f} percentage points**.
  This is a separate estimator, not the percentage version of the dollar estimate.
- Under explicitly assumed {config['gross_margin_rate']:.0%} margin, {config['additional_promo_cost_rate']:.0%}
  additional promotion cost on treated sales and ${config['fixed_cost_per_store']:,.0f} fixed cost per store,
  a {config['rollout_stores']}-store / {config['scenario_weeks']}-week sensitivity scenario gives
  **${main.incremental_contribution_usd:,.2f} incremental contribution**. This is not a forecast or observed profit.

**Checks:** complete store/category/week panel, SQL-to-Python reconciliation,
store-clustered regression, whole-store bootstrap, pre-period slope diagnostic,
per-category placebo and regional comparisons with Holm correction.

**Limits:** only 13 weeks before and after; original allocation algorithm unavailable;
synthetic effects can be designed into the data. Nonsignificant placebo/pretrend tests
do not prove no spillovers or parallel counterfactual trends. Category aggregates
cannot identify individual SKU substitution, order conversion or true basket value.
Margins, inventory, redemption costs and sustained demand are not observed.

![Results dashboard](../dashboard/dashboard.png)
'''
    (out/'executive_summary.md').write_text(text)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(2,2,figsize=(14,9),layout='constrained')
    fig.suptitle('Electronics promotion | synthetic retail experiment',fontsize=20,fontweight='bold')
    for name,color in [('Test','#c62828'),('Control','#00796b')]:
        g=trend[trend.test_group==name]
        ax[0,0].plot(pd.to_datetime(g.week_start_date),g.revenue,label=name,color=color,lw=2)
    ax[0,0].axvline(pd.to_datetime(trend[trend.period=='Post'].week_start_date).min(),color='#666',ls=':')
    ax[0,0].set(title='Weekly revenue per store',ylabel='USD / store / week')
    ax[0,0].legend(frameon=False)
    ax[0,0].tick_params(axis='x',rotation=20)
    p=placebo.sort_values('effect_usd_per_store_week')
    ax[0,1].barh(p.category,p.effect_usd_per_store_week,color=['#c62828' if x else '#9eaaa8' for x in p.is_target])
    ax[0,1].errorbar(p.effect_usd_per_store_week,p.category,
                     xerr=[p.effect_usd_per_store_week-p.ci_low,p.ci_high-p.effect_usd_per_store_week],fmt='none',ecolor='#333',capsize=3)
    ax[0,1].axvline(0,color='#666',lw=.8)
    ax[0,1].set(title='Category effects with 95% clustered CIs',xlabel='Incremental USD / store / week')
    ax[1,0].errorbar(regions.region,regions.effect_usd_per_store_week,
                     yerr=[regions.effect_usd_per_store_week-regions.ci_low,regions.ci_high-regions.effect_usd_per_store_week],fmt='o',color='#00796b',capsize=5)
    ax[1,0].set(title='Regional effects (exploratory)',ylabel='Incremental USD / store / week')
    ax[1,1].bar(scenario.scenario,scenario.incremental_contribution_usd/1000,color=['#9eaaa8','#00796b','#9eaaa8'])
    ax[1,1].axhline(0,color='#666',lw=.8)
    ax[1,1].set(title='Rollout sensitivity under assumed costs',ylabel='Illustrative contribution, USD thousands')
    dash=out.parent/'dashboard'
    dash.mkdir(exist_ok=True)
    fig.savefig(dash/'dashboard.png',dpi=140)
    fig.savefig(dash/'dashboard.pdf')
    plt.close(fig)
    clean_scenarios=scenario.astype(object).where(pd.notna(scenario),None)
    payload={'summary':summary,'regions':regions.to_dict('records'),'scenarios':clean_scenarios.to_dict('records'),
             'config':config,'quality':quality,'stores':changes.to_dict('records')}
    (dash/'data.json').write_text(json.dumps(payload,indent=2,allow_nan=False)+'\n')
    image=base64.b64encode((dash/'dashboard.png').read_bytes()).decode()
    page=TEMPLATE.replace('__IMAGE__',image).replace('__DATA__',json.dumps(payload,allow_nan=False).replace('<','\\u003c'))
    (dash/'index.html').write_text(page)


TEMPLATE='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Circle Week | Retail decision brief</title><style>
:root{font-family:Arial,sans-serif;color:#202a29;background:#f4f5f1}*{box-sizing:border-box}body{margin:0}main{max-width:1240px;margin:auto;padding:36px 24px}header{border-top:5px solid #c62828;padding-top:22px}.eyebrow{font-size:12px;letter-spacing:2px;font-weight:bold;color:#a62323}h1{font-size:38px;letter-spacing:-1px;margin:12px 0}p{line-height:1.6;color:#52615e}nav{display:flex;gap:10px;margin:24px 0;flex-wrap:wrap}button{border:1px solid #b8c4bf;background:white;padding:12px 20px;border-radius:6px;cursor:pointer}button[aria-selected=true]{background:#16483d;color:white}section[hidden]{display:none}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.card,.panel{background:white;border:1px solid #dae0da;border-radius:8px;padding:22px}.card span{display:block;font-size:12px;color:#52615e}.value{font-size:31px;font-weight:bold;margin:10px 0}.note{font-size:13px}.panel{margin-top:20px}img{width:100%;height:auto}label{display:block;margin:12px 0;color:#41554d}input,select{padding:9px;border:1px solid #9eaaa8;border-radius:4px;font-size:16px}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:12px;border-bottom:1px solid #e5e9e4}th{font-size:12px;color:#52615e}.assumptions{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}footer{margin-top:28px;font-size:12px;color:#52615e}@media(max-width:700px){.cards,.assumptions{grid-template-columns:1fr}h1{font-size:29px}.panel{overflow:auto}.value{font-size:27px}}
</style><main><header><div class="eyebrow">MERCHANDISING / TEST & MEASURE</div><h1>Did the promotion earn its place?</h1><p>Synthetic Electronics promotion across <span id="sampleSize"></span> stores. Revenue evidence, uncertainty and the cost assumptions behind a rollout decision.</p></header>
<nav role="tablist" aria-label="Analysis views"><button id="tab-overview" role="tab" aria-selected="true" aria-controls="overview" data-view="overview">Results</button><button id="tab-scenarios" role="tab" aria-selected="false" aria-controls="scenarios" data-view="scenarios">What-if costs</button><button id="tab-stores" role="tab" aria-selected="false" aria-controls="stores" data-view="stores">Store growth</button></nav>
<section id="overview" role="tabpanel" aria-labelledby="tab-overview"><div class="cards"><div class="card"><span>ADDITIVE DID / STORE / WEEK</span><div class="value" id="effect"></div><p class="note" id="interval"></p></div><div class="card"><span>TEST-STORE INCREMENTAL REVENUE</span><div class="value" id="incremental"></div><p class="note" id="exposure"></p></div><div class="card"><span>STORE GROWTH GAP</span><div class="value" id="growth"></div><p class="note">Percentage-point difference. Separate from dollar DiD.</p></div></div><div class="panel"><img alt="Revenue trend, category confidence intervals, regional effects and rollout sensitivity" src="data:image/png;base64,__IMAGE__"></div><div class="panel"><h2>Decision</h2><p>Consider a limited follow-up pilot after confirming margins, costs and stock. Synthetic evidence cannot establish an actual promotion's value.</p><p>Confidence intervals describe estimation uncertainty under the model. They are not rollout prediction intervals. A nonsignificant placebo does not prove no spillovers.</p></div></section>
<section id="scenarios" role="tabpanel" aria-labelledby="tab-scenarios" hidden><div class="panel"><h2>Make the assumptions visible</h2><p>Illustrative transfer of the test-store effect. No inventory, margin or redemption-cost data was observed. Revenue is assumed net of discounts; extra promo costs exclude discounts already reflected in sales.</p><div class="assumptions"><label>Rollout stores <input id="count" type="number" min="1" max="10000" step="1" value="100"></label><label>Weeks <input id="weeks" type="number" min="1" max="52" step="1" value="13"></label><label>Gross margin % <input id="margin" type="number" min="0" max="100" step="1" value="30"></label><label>Extra promo cost % of treated sales <input id="rate" type="number" min="0" max="100" step="0.1" value="2"></label><label>Fixed cost per store, USD <input id="fixed" type="number" min="0" max="1000000" value="500"></label><label>Effect assumption <select id="effectChoice"><option value="effect_ci_low">Lower confidence bound</option><option value="effect_usd_per_store_week" selected>Point estimate</option><option value="effect_ci_high">Upper confidence bound</option></select></label></div><p id="scenarioResult" aria-live="polite"></p><p class="note">Extending to more weeks or stores assumes a stable effect and comparable stores. This is sensitivity analysis, not a causal forecast.</p></div></section>
<section id="stores" role="tabpanel" aria-labelledby="tab-stores" hidden><div class="panel"><h2>Store growth</h2><p>Pre/post revenue growth includes background changes. These rankings are not individual treatment-effect estimates.</p><label>Region <select id="region"><option value="all">All regions</option></select></label><table><thead><tr><th>Store</th><th>Region</th><th>Assignment</th><th>Growth %</th></tr></thead><tbody id="storeRows"></tbody></table></div></section><footer>Source: committed synthetic weekly panel. Definitions, limitations and reproducible analysis are in the repository. Dashboard runs offline; all values are generated by the pipeline.</footer></main>
<script>const D=__DATA__;const s=D.summary;const money=x=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(x);document.getElementById('sampleSize').textContent=s.n_test+s.n_control;document.getElementById('exposure').textContent=s.n_test+' stores × '+s.post_weeks+' post weeks; estimated, synthetic.';document.getElementById('effect').textContent=money(s.effect_usd_per_store_week);document.getElementById('interval').textContent='95% CI '+money(s.effect_ci_low)+' to '+money(s.effect_ci_high);document.getElementById('incremental').textContent=money(s.incremental_revenue_usd);document.getElementById('growth').textContent=s.store_growth_gap_pp.toFixed(2)+' pp';
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('section[role=tabpanel]').forEach(p=>p.hidden=p.id!==b.dataset.view);document.querySelectorAll('[data-view]').forEach(t=>t.setAttribute('aria-selected',String(t===b)))}));
for(const [id,key] of [['count','rollout_stores'],['weeks','scenario_weeks'],['margin','gross_margin_rate'],['rate','additional_promo_cost_rate'],['fixed','fixed_cost_per_store']])document.getElementById(id).value=D.config[key]*(['margin','rate'].includes(id)?100:1);
function recalc(){let els=['count','weeks','margin','rate','fixed'].map(x=>document.getElementById(x));let r=document.getElementById('scenarioResult');if(!els.every(x=>x.checkValidity()&&x.value!=='')){r.textContent='Enter valid assumptions within the displayed limits.';return;}let [n,w,m,c,f]=els.map(x=>+x.value);let e=s[document.getElementById('effectChoice').value],base=s.test_pre_weekly_revenue+s.control_weekly_change,inc=e*n*w;let contribution=inc*m/100-(base+e)*n*w*c/100-n*f;r.textContent='Illustrative incremental revenue: '+money(inc)+' · incremental contribution: '+money(contribution);}
document.querySelectorAll('#scenarios input,#scenarios select').forEach(x=>x.addEventListener('input',recalc));recalc();
let region=document.getElementById('region');[...new Set(D.stores.map(x=>x.region))].sort().forEach(r=>{let o=document.createElement('option');o.value=r;o.textContent=r;region.appendChild(o)});function rows(){let body=document.getElementById('storeRows');body.replaceChildren();D.stores.filter(x=>region.value==='all'||x.region===region.value).sort((a,b)=>b.growth_pct-a.growth_pct).forEach(x=>{let tr=document.createElement('tr');[x.store_id,x.region,x.test_group,x.growth_pct.toFixed(2)].forEach(v=>{let td=document.createElement('td');td.textContent=v;tr.appendChild(td)});body.appendChild(tr)})}region.addEventListener('change',rows);rows();</script></html>'''
