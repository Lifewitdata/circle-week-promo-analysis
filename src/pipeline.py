"""python -m src.pipeline: validated inputs -> SQL -> statistics -> decisions -> reports."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import shutil
import pandas as pd
import numpy as np
from src.validation import validate
from src.warehouse import build
from src.analysis import analyze
from src.scenarios import scenarios
from src.forecast import benchmark
from src.reporting import write_reports

ROOT=Path(__file__).resolve().parents[1]


def run(input_dir=None, output_dir=None):
    data=Path(input_dir) if input_dir else ROOT/'data'
    dest=Path(output_dir) if output_dir else ROOT
    config=json.loads((ROOT/'config.json').read_text())
    tables=[pd.read_csv(data/f'{name}.csv') for name in ['sales_weekly','stores','products','promotions']]
    sales,quality=validate(*tables)
    # Canonical query window currently describes the committed case study.
    if sales.week_start_date.min()!=pd.Timestamp('2026-01-05') or sales.week_start_date.max()!=pd.Timestamp('2026-06-29') or tables[3].iloc[0].category_targeted!='Electronics':
        raise ValueError('SQL window supports Jan 5–Jun 29 2026 Electronics case study only')
    input_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(data.glob('*.csv'))}
    dest.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='circle-') as tmp:
        stage=Path(tmp)
        reports=stage/'reports'
        sql=build(sales,*tables[1:],ROOT/'sql/queries.sql',reports/'sql')
        summary,changes,placebo,regions,trend,unit=analyze(sales,tables[3].iloc[0].category_targeted,config)
        for key in ['effect_usd_per_store_week','store_growth_gap_pp']:
            if not np.isclose(sql['primary_effect'].iloc[0][key],summary[key],rtol=1e-10):
                raise AssertionError(f'SQL/Python reconciliation failed: {key}')
        quality['sql_python_reconciled']=True
        summary['input_sha256']=input_hashes
        scenario=scenarios(summary,config)
        forecasts,metrics=benchmark(sales,summary['category'])
        forecasts.to_csv(reports/'forecast_predictions.csv',index=False)
        write_reports(reports,summary,changes,placebo,regions,trend,unit,scenario,metrics,quality,config)
        from src.tableau import package
        package(stage/'dashboard',reports)
        # Publish only after every calculation, validation and rendering succeeds.
        for folder in ['reports','dashboard']:
            shutil.copytree(stage/folder,dest/folder,dirs_exist_ok=True)
        (dest/'reports/run_status.json').write_text(json.dumps({'status':'success','input_sha256':input_hashes},indent=2))
    print(f"Validated {len(sales):,} rows; SQL/Python reconciled. Results: {dest/'reports/executive_summary.md'}")
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir',type=Path)
    parser.add_argument('--output-dir',type=Path,help='Root containing generated reports/ and dashboard/')
    args=parser.parse_args()
    try:
        run(args.input_dir,args.output_dir)
    except Exception:
        dest=args.output_dir or ROOT
        (dest/'reports').mkdir(parents=True,exist_ok=True)
        (dest/'reports/run_status.json').write_text(json.dumps({'status':'failed','note':'Previously generated reports may be stale; see command error.'}))
        raise


if __name__=='__main__':
    main()
